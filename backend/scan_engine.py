"""SkullHarbor scan orchestration.

Customer-facing code talks to ScanEngine only. Concrete scanner/tool adapters remain
backend implementation details and can be replaced without changing the API.
"""
from dataclasses import dataclass
import json
from datetime import datetime
import threading
import time
from typing import Callable

from database import SessionLocal
from models import Finding, Scan
from scanner import AdapterTimeoutError, run_nikto_streaming, run_nuclei_streaming, run_surface_discovery_streaming
from scan_profiles import require_self_service_profile


@dataclass(frozen=True)
class EngineContext:
    scan_id: int
    target: str
    profile: str
    expected_hostname: str


class ScanEngine:
    """Small in-process orchestrator for the MVP.

    It owns job state, cancellation, lifecycle transitions and persistence. The
    adapter list is deliberately private so no concrete tool identity crosses
    the customer API boundary.
    """

    def __init__(self, validate_target: Callable):
        self._validate_target = validate_target
        self._jobs: dict[int, dict] = {}
        self._lock = threading.Lock()
        self._adapters = None  # private test override retained for regression harnesses
        self._adapter_slots = {
            "primary": self._run_primary_web_security,
            "secondary": self._run_secondary_web_security,
            "surface": self._run_surface_discovery,
        }
        # Customer-safe coverage names. Concrete tool identities never cross the API.
        self._coverage_names = {
            "primary": "Core web security",
            "secondary": "Vulnerability & exposure checks",
            "surface": "Public service exposure",
        }

    def enqueue(self, scan_id: int, target: str, profile: str, expected_hostname: str, initial_ips: list[str]):
        now = time.time()
        with self._lock:
            self._jobs[scan_id] = {
                "status": "queued",
                "stage": "queued",
                "progress": 5,
                "logs": [
                    self._log_line(f"Verified target: {expected_hostname}"),
                    self._log_line(f"Public DNS resolution: {', '.join(initial_ips)}"),
                    self._log_line("Quick Check queued"),
                ],
                "started_at": now,
                "stop_event": threading.Event(),
                "error": None,
                # Private orchestration telemetry. Never returned by snapshot().
                "adapter_runs": [],
            }
        ctx = EngineContext(scan_id, target, profile, expected_hostname)
        threading.Thread(target=self._execute, args=(ctx,), daemon=True).start()

    def snapshot(self, scan_id: int):
        with self._lock:
            job = self._jobs.get(scan_id)
            if not job:
                return None
            return {
                "scan_id": scan_id,
                "status": job["status"],
                "stage": job["stage"],
                "progress": job["progress"],
                "logs": list(job["logs"][-200:]),
                "elapsed_seconds": int(time.time() - job["started_at"]),
                "error": job.get("error"),
                "coverage": self._public_coverage(job),
            }

    def stop(self, scan_id: int) -> bool:
        with self._lock:
            job = self._jobs.get(scan_id)
            if not job or job["status"] not in {"queued", "running"}:
                return False
            job["stop_event"].set()
            job["stage"] = "stopping"
            self._append_locked(job, "Stop requested")
            return True

    def _set(self, scan_id: int, **values):
        with self._lock:
            if scan_id in self._jobs:
                self._jobs[scan_id].update(values)

    def _append(self, scan_id: int, message: str):
        with self._lock:
            job = self._jobs.get(scan_id)
            if job:
                self._append_locked(job, message)

    @staticmethod
    def _log_line(message: str) -> str:
        return f"[{datetime.now().strftime('%H:%M:%S')}]  {message}"

    def _append_locked(self, job: dict, message: str):
        job["logs"].append(self._log_line(message))

    def _execute(self, ctx: EngineContext):
        stop_event = self._jobs[ctx.scan_id]["stop_event"]
        db = SessionLocal()
        try:
            if stop_event.is_set():
                raise RuntimeError("Scan stopped by user")

            # Security gate is repeated immediately before execution to defend
            # against DNS rebinding / a changed destination after verification.
            _, hostname, ips = self._validate_target(ctx.target)
            if hostname != ctx.expected_hostname:
                raise RuntimeError("Target hostname changed before scan")

            record = db.get(Scan, ctx.scan_id)
            if not record:
                raise RuntimeError("Scan record no longer exists")
            record.status = "running"
            db.commit()

            self._set(ctx.scan_id, status="running", stage="authorizing", progress=15)
            self._append(ctx.scan_id, f"Authorization gate passed for verified target {hostname}")
            self._append(ctx.scan_id, f"Public DNS resolution: {', '.join(ips)}")
            self._append(ctx.scan_id, "Initializing SkullHarbor Quick Check")

            policy = require_self_service_profile(ctx.profile)
            if self._adapters:
                adapter_specs = tuple((f"check-{i}", adapter) for i, adapter in enumerate(self._adapters, start=1))
            else:
                adapter_specs = tuple((name, self._adapter_slots[name]) for name in policy.adapter_slots)
            self._set(ctx.scan_id, coverage_expected=len(adapter_specs))
            all_findings = []
            successful_adapters = 0
            for index, (slot, adapter) in enumerate(adapter_specs, start=1):
                if stop_event.is_set():
                    raise RuntimeError("Scan stopped by user")

                started = time.time()
                try:
                    findings = adapter(ctx, stop_event)
                    # Persist a customer-safe coverage family on every finding so
                    # Advanced results can be reviewed by coverage area instead of
                    # as one undifferentiated list. Concrete adapter identities stay private.
                    coverage_family = self._coverage_names.get(slot, "Security check")
                    for finding in findings:
                        finding.setdefault("coverage_family", coverage_family)
                    successful_adapters += 1
                    all_findings.extend(findings)
                    self._record_adapter_run(ctx.scan_id, index, "completed", started, len(findings), slot=slot)
                except Exception as exc:
                    if stop_event.is_set() or str(exc) == "Scan stopped by user":
                        self._record_adapter_run(ctx.scan_id, index, "stopped", started, 0, slot=slot)
                        raise
                    # One adapter must not discard useful results from another.
                    # Concrete adapter identity/error text remains private.
                    outcome = "timeout" if isinstance(exc, AdapterTimeoutError) else "failed"
                    self._record_adapter_run(ctx.scan_id, index, outcome, started, 0, str(exc), slot=slot)
                    self._append(ctx.scan_id, "One web security check could not complete; continuing with remaining checks")

            if successful_adapters == 0:
                raise RuntimeError("Web security checks could not be completed")
            if policy.require_all_adapters and successful_adapters != len(adapter_specs):
                raise RuntimeError("The promised security coverage could not be completed. No partial Advanced result was published.")

            if stop_event.is_set():
                raise RuntimeError("Scan stopped by user")

            all_findings = self._deduplicate_findings(all_findings)
            self._set(ctx.scan_id, stage="processing", progress=75)
            self._append(ctx.scan_id, "Processing normalized security findings")
            for item in all_findings:
                db.add(Finding(scan_id=ctx.scan_id, **item))

            if stop_event.is_set():
                raise RuntimeError("Scan stopped by user")

            self._set(ctx.scan_id, stage="saving", progress=90)
            self._append(ctx.scan_id, "Saving findings")
            if stop_event.is_set():
                raise RuntimeError("Scan stopped by user")
            record.status = "completed"
            record.error = None
            record.coverage_summary = json.dumps(self._public_coverage(self._jobs.get(ctx.scan_id, {})), separators=(",", ":"))
            db.commit()
            self._set(ctx.scan_id, status="completed", stage="completed", progress=100, error=None)
            self._append(ctx.scan_id, f"Completed with {len(all_findings)} normalized findings")
        except Exception as exc:
            record = db.get(Scan, ctx.scan_id)
            stopped = stop_event.is_set() or str(exc) == "Scan stopped by user"
            if record:
                record.status = "stopped" if stopped else "failed"
                record.error = None if stopped else str(exc)[:4000]
                # Persist vendor-neutral coverage telemetry on failure too. This
                # lets support and the UI identify the failed coverage family
                # without publishing partial security findings as a result.
                record.coverage_summary = json.dumps(
                    self._public_coverage(self._jobs.get(ctx.scan_id, {})),
                    separators=(",", ":"),
                )
                db.commit()
            if stopped:
                self._set(ctx.scan_id, status="stopped", stage="stopped", error=None)
                self._append(ctx.scan_id, "Scan stopped by user")
            else:
                error = str(exc)[:4000]
                self._set(ctx.scan_id, status="failed", stage="failed", error=error)
                self._append(ctx.scan_id, f"ERROR: {error}")
        finally:
            db.close()

    def _record_adapter_run(self, scan_id: int, position: int, status: str, started: float, finding_count: int, error: str | None = None, slot: str | None = None):
        """Store private per-adapter execution telemetry without exposing vendor identity."""
        with self._lock:
            job = self._jobs.get(scan_id)
            if not job:
                return
            job.setdefault("adapter_runs", []).append({
                "position": position,
                "slot": slot,
                "status": status,
                "duration_ms": max(0, int((time.time() - started) * 1000)),
                "finding_count": finding_count,
                "error": (error or "")[:1000] or None,
            })

    def _public_coverage(self, job: dict) -> dict:
        runs = list(job.get("adapter_runs") or [])
        items = []
        for run in runs:
            slot = run.get("slot") or "check"
            items.append({
                "name": self._coverage_names.get(slot, "Security check"),
                "status": run.get("status") or "pending",
                "finding_count": int(run.get("finding_count") or 0),
            })
        expected = int(job.get("coverage_expected") or len(items) or 0)
        completed = sum(1 for item in items if item["status"] == "completed")
        return {"expected": expected, "completed": completed, "complete": bool(expected and completed == expected), "checks": items}

    @staticmethod
    def _deduplicate_findings(findings: list[dict]) -> list[dict]:
        """Collapse overlapping adapter results using stable normalized fields.

        First occurrence wins for customer text. References/evidence from later
        matches are merged so deduplication does not throw away useful context.
        """
        unique: dict[tuple[str, str, str], dict] = {}
        for finding in findings:
            key = (
                str(finding.get("rule_id") or "").strip().lower(),
                str(finding.get("url") or "").rstrip("/").strip().lower(),
                str(finding.get("title") or "").strip().lower(),
            )
            if key not in unique:
                unique[key] = dict(finding)
                continue

            current = unique[key]
            for field in ("reference", "evidence"):
                existing = str(current.get(field) or "").strip()
                incoming = str(finding.get(field) or "").strip()
                if incoming and incoming not in existing:
                    current[field] = f"{existing}\n{incoming}".strip()
        return list(unique.values())

    def _run_primary_web_security(self, ctx: EngineContext, stop_event: threading.Event):
        self._set(ctx.scan_id, stage="web-security", progress=25)

        def on_log(line: str):
            # Adapter is responsible for returning vendor-neutral text.
            self._append(ctx.scan_id, line)
            snap = self.snapshot(ctx.scan_id)
            if snap and snap["progress"] < 68:
                self._set(ctx.scan_id, progress=min(68, snap["progress"] + 2))

        return run_nikto_streaming(ctx.target, on_log, stop_event, profile=ctx.profile)


    def _run_secondary_web_security(self, ctx: EngineContext, stop_event: threading.Event):
        self._set(ctx.scan_id, stage="web-security", progress=55)

        def on_log(line: str):
            self._append(ctx.scan_id, line)
            snap = self.snapshot(ctx.scan_id)
            if snap and snap["progress"] < 72:
                self._set(ctx.scan_id, progress=min(72, snap["progress"] + 2))

        return run_nuclei_streaming(ctx.target, on_log, stop_event, profile=ctx.profile)
    def _run_surface_discovery(self, ctx: EngineContext, stop_event: threading.Event):
        self._set(ctx.scan_id, stage="web-security", progress=62)

        def on_log(line: str):
            self._append(ctx.scan_id, line)
            snap = self.snapshot(ctx.scan_id)
            if snap and snap["progress"] < 73:
                self._set(ctx.scan_id, progress=min(73, snap["progress"] + 2))

        return run_surface_discovery_streaming(ctx.target, on_log, stop_event, profile=ctx.profile)


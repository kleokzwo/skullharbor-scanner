import React from "react";
import {Header, MobileNav, Sidebar, Icon, Empty, PlanCard, DnsValue, ProductReadiness, ProgressCard, DetailRow, Explanation, LEVELS, severityClass, statusClass, customerPlanState, resultHeadline} from "../components/ui.jsx";

export default function DashboardPage(props) {
  const {page, setPage, productStatus, users, userId, setUserId, scans, setScans, targets, setTargets, target, setTarget, newDomain, setNewDomain, targetMessage, error, setup, setSetup, devAuthority, activationBusy, activationProduct, activateDevelopmentAccess, addTarget, verifyTarget, copyText, submitCustomerSetup, selected, setSelected, finding, setFinding, job, setJob, openScan, openFinding, closeFinding, moveFinding, findingIndex, findings, counts, active, run, stop, readiness} = props;
  const coverageOrder = ["Core web security", "Vulnerability & exposure checks", "Public service exposure"];
  const groupedFindings = coverageOrder.map(name => ({name, items: findings.filter(f => (f.coverage_family || "Core web security") === name)})).filter(group => group.items.length > 0);
  const resultNoun = name => name === "Public service exposure" ? "observation" : "finding";
  const coverageHelp = {
    "Core web security": "Website configuration and common web-security checks.",
    "Vulnerability & exposure checks": "Targeted checks for exposed files, interfaces and common web risks.",
    "Public service exposure": "Additional internet-facing services only; normal website ports 80/443 are excluded.",
  };
  return <div className="min-h-screen bg-slate-50">
    <Header productStatus={productStatus}/>
    <MobileNav page={page} setPage={setPage}/>
    <div className="flex min-h-[calc(100vh-70px)]">
      <Sidebar page={page} setPage={setPage}/>
      <main className="workspace min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10">
        <div className="mx-auto max-w-[1180px]">
          <section>
            <p className="eyebrow">SECURITY WORKSPACE</p>
            <div className="hero-row"><div><h1 className="product-title">Quick Check</h1>
            <p className="product-subtitle">Check an authorized website for common security issues.</p></div><div className="local-chip"><span></span>Runs locally</div></div>
  
            <ProductReadiness users={users} userId={userId} setUserId={setUserId} status={readiness || productStatus} goTargets={()=>setPage("targets")} goSetup={()=>setPage("setup")}/>
  
            <form onSubmit={run} className="scan-launcher mt-5 grid gap-3 sm:grid-cols-[1fr_auto]">
              <div className="relative">
                <Icon name="link" className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400"/>
                <input required value={target} onChange={e=>setTarget(e.target.value)} placeholder="https://your-verified-site.com" disabled={active} className="scan-input"/>
                {target&&!active&&<button type="button" onClick={()=>setTarget("")} className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-2 text-slate-400 hover:bg-slate-50">×</button>}
              </div>
              <button disabled={active || !(readiness || productStatus)?.ready_for_quick_check} className="primary-action"><Icon name="play" className="h-5 w-5"/>{active?"Scanning...":"Start Scan"}</button>
            </form>
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-400"><Icon name="shield" className="h-4 w-4"/>SkullHarbor verifies access and authorization again when the check starts.</div>
            {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
          </section>
  
          {job&&<ProgressCard job={job} target={target} active={active} stop={stop}/>} 
  
          {selected&&selected.status!=="completed"&&selected.scan_profile==="monthly"&&selected.coverage&&selected.coverage.checks?.length>0&&<section className="card mt-5 p-5 sm:p-6">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-base font-extrabold text-slate-900">Advanced coverage status</h2><p className="mt-1 text-xs text-slate-500">No partial security result was published. This status only shows which promised coverage families completed.</p></div><span className="pill bg-amber-50 text-amber-700">{selected.coverage.completed}/{selected.coverage.expected} completed</span></div>
            <div className="mt-4 grid gap-2 sm:grid-cols-3">{(selected.coverage.checks||[]).map((check,index)=><div key={`${check.name}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"><div className="flex items-center gap-2"><span className={`grid h-6 w-6 place-items-center rounded-full ${check.status==="completed"?"bg-emerald-50 text-emerald-600":"bg-amber-50 text-amber-600"}`}><Icon name={check.status==="completed"?"check":"shield"} className="h-4 w-4"/></span><b className="text-xs text-slate-800">{check.name}</b></div><div className="mt-2 text-[11px] font-semibold text-slate-500">{check.status==="completed"?"Completed":check.status==="timeout"?"Timed out":"Could not complete"}</div></div>)}</div>
          </section>}

          {selected&&selected.status==="completed"&&<section className="card mt-5 p-5 sm:p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-emerald-600 text-white"><Icon name="check" className="h-6 w-6"/></span>
                <div><h2 className="text-xl font-extrabold">{selected.status==="completed"?resultHeadline(findings):"Check result"}</h2><p className="mt-1 break-all text-sm text-slate-500">{selected.target}</p></div>
              </div>
              <div className="text-left text-xs text-slate-400 sm:text-right"><div>{selected.created_at?new Date(selected.created_at).toLocaleString():""}</div><div className="mt-1">{selected.scan_profile==="monthly"?"Advanced Security Check":"Quick Check"}</div></div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-5">
              {LEVELS.map(level=><div key={level} className={`severity-tile ${severityClass(level)}`}><div className="text-2xl font-black">{counts[level]}</div><div className="mt-1 text-xs font-bold capitalize">{level}</div></div>)}
            </div>
            {selected.scan_profile==="monthly"&&selected.coverage&&<div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><div className="text-sm font-extrabold text-slate-900">Advanced coverage</div><div className="mt-1 text-xs text-slate-500">SkullHarbor completed the paid coverage families promised for this check.</div></div><span className={`pill ${selected.coverage.complete?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}>{selected.coverage.completed}/{selected.coverage.expected} completed</span></div>
              <div className="mt-4 grid gap-2 sm:grid-cols-3">{(selected.coverage.checks||[]).map((check,index)=><div key={`${check.name}-${index}`} className="rounded-xl border border-slate-200 bg-white px-4 py-3"><div className="flex items-center gap-2"><span className={`grid h-6 w-6 place-items-center rounded-full ${check.status==="completed"?"bg-emerald-50 text-emerald-600":"bg-amber-50 text-amber-600"}`}><Icon name={check.status==="completed"?"check":"shield"} className="h-4 w-4"/></span><b className="text-xs text-slate-800">{check.name}</b></div><div className="mt-2 text-[11px] leading-5 text-slate-400"><span className="font-semibold text-slate-500">{check.finding_count} {resultNoun(check.name)}{check.finding_count===1?"":"s"}</span><span className="block">{coverageHelp[check.name] || "Completed security coverage."}</span></div></div>)}</div>
            </div>}
          </section>}
  
          <section className="mt-4 grid gap-4 md:grid-cols-[1.15fr_.85fr]">
            <div className="card overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                <div><h2 className="text-xl font-extrabold">Security results {selected?`(${findings.length})`:""}</h2><p className="mt-0.5 text-xs text-slate-400">Findings and verified external-service observations from this check.</p></div>
              </div>
              {active?<Empty title="Scan in progress" text="Results appear here when the scan is finished."/>:!selected?<Empty title="Select a scan" text="Choose a recent scan to review its findings."/>:selected.status!=="completed"?<Empty title="No result published" text="This check did not complete, so SkullHarbor did not publish a partial security result."/>:findings.length===0?<Empty title="No findings in this check" text="Nothing actionable was detected by this check. This is not a guarantee that the website has no vulnerabilities."/>:<div>{(selected.scan_profile==="monthly"?groupedFindings:[{name:null,items:findings}]).map(group=><div key={group.name||"findings"}>{group.name&&<div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-5 py-3"><b className="text-xs uppercase tracking-wide text-slate-600">{group.name}</b><span className="pill bg-white text-slate-500">{group.items.length} {resultNoun(group.name)}{group.items.length===1?"":"s"}</span></div>}{group.items.map(f=><button key={f.id} onClick={()=>openFinding(f)} className="grid w-full grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-slate-100 px-5 py-4 text-left transition last:border-b-0 hover:bg-slate-50"><span className={`pill ${severityClass(f.severity)}`}>{f.severity}</span><span className="min-w-0"><b className="block truncate text-sm text-slate-900">{f.title}</b><small className="mt-1 block truncate text-xs text-slate-400">{f.description||"General web security information"}</small></span><span className="inline-flex items-center gap-1 rounded-xl border-2 border-emerald-500 px-3 py-2 text-sm font-bold text-blue-600">View <Icon name="chevron" className="h-4 w-4"/></span></button>)}</div>)}</div>}
            </div>
  
            <div className="card overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><h2 className="text-xl font-extrabold">Recent scans</h2><span className="text-sm font-semibold text-blue-600">View all →</span></div>
              {scans.length===0?<Empty title="No scans yet" text="Your completed scans will appear here." small/>:<div>{scans.slice(0,5).map(s=><button key={s.id} onClick={()=>openScan(s.id)} className={`grid w-full grid-cols-[auto_1fr_auto_auto] items-center gap-3 border-b border-slate-100 px-5 py-4 text-left transition last:border-b-0 hover:bg-slate-50 ${selected?.id===s.id?"bg-blue-50/40":""}`}><span className="text-slate-400"><Icon name="clock"/></span><span className="min-w-0"><b className="block truncate text-sm">{s.target}</b><small className="mt-1 block truncate text-xs text-slate-400">{new Date(s.created_at).toLocaleString()} · {s.finding_count} finding{s.finding_count===1?"":"s"}</small></span><span className={`pill ${statusClass(s.status)}`}>{s.status}</span><Icon name="chevron" className="h-4 w-4 text-slate-400"/></button>)}</div>}
            </div>
          </section>
  
          <footer className="py-7 text-[10px] text-slate-400">Use only against systems you own or are explicitly authorized to test.</footer>
        </div>
      </main>
    </div>
  </div>;
}

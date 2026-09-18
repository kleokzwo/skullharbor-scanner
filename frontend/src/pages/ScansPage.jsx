import React from "react";
import {
    Header,
    MobileNav,
    Sidebar,
    Icon,
    Empty,
    statusClass,
} from "../components/ui.jsx";
import {
    CheckCircle2,
    XCircle,
    Clock3,
    ShieldCheck,
    Search,
    ChevronRight,
} from "lucide-react";

function scanStatusMeta(status) {
    const value = String(status || "").toUpperCase();

    if (value === "COMPLETED") {
        return {
            label: "Completed",
            icon: CheckCircle2,
            iconClass: "text-emerald-600",
            iconBg: "bg-emerald-50",
        };
    }

    if (value === "FAILED") {
        return {
            label: "Failed",
            icon: XCircle,
            iconClass: "text-rose-500",
            iconBg: "bg-rose-50",
        };
    }

    return {
        label: value || "Unknown",
        icon: Clock3,
        iconClass: "text-slate-500",
        iconBg: "bg-slate-100",
    };
}

export default function ScansPage(props) {
    const {
        page,
        setPage,
        scans,
        openScan,
    } = props;

    const completedCount = scans.filter(
        (scan) => String(scan.status || "").toUpperCase() === "COMPLETED",
    ).length;
    const failedCount = scans.filter(
        (scan) => String(scan.status || "").toUpperCase() === "FAILED",
    ).length;
    const totalFindings = scans.reduce(
        (total, scan) => total + Number(scan.finding_count || 0),
        0,
    );

    return (
        <div className="min-h-screen bg-slate-50">
            <Header />
            <MobileNav page={page} setPage={setPage} />

            <div className="flex min-h-[calc(100vh-70px)]">
                <Sidebar page={page} setPage={setPage} />

                <main className="min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10">
                    <div className="mx-auto w-full max-w-[1280px]">
                        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                            <div>
                                <p className="eyebrow">SCAN HISTORY</p>
                                <h1 className="product-title mt-2">Security scans</h1>
                                <p className="product-subtitle mt-3 max-w-2xl">
                                    Review completed and unsuccessful checks for your authorized targets.
                                </p>
                            </div>

                            {scans.length > 0 && (
                                <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-500">
                                    <span className="rounded-full border border-slate-200 bg-white px-3 py-2">
                                        {scans.length} scans
                                    </span>
                                    <span className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-2 text-emerald-700">
                                        {completedCount} completed
                                    </span>
                                    {failedCount > 0 && (
                                        <span className="rounded-full border border-rose-100 bg-rose-50 px-3 py-2 text-rose-600">
                                            {failedCount} failed
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>

                        {scans.length === 0 ? (
                            <section className="card mt-7 overflow-hidden">
                                <Empty
                                    title="No scans yet"
                                    text="Completed scans will appear here."
                                />
                            </section>
                        ) : (
                            <section className="card mt-7 overflow-hidden">
                                <div className="border-b border-slate-100 px-5 py-5 sm:px-7">
                                    <div className="flex items-center justify-between gap-4">
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                                                <ShieldCheck className="h-5 w-5" strokeWidth={1.8} />
                                            </div>
                                            <div>
                                                <h2 className="text-base font-semibold text-slate-950">
                                                    Scan history
                                                </h2>
                                                <p className="mt-0.5 text-xs text-slate-500">
                                                    Open a scan to review its security results.
                                                </p>
                                            </div>
                                        </div>

                                        <div className="hidden text-right sm:block">
                                            <div className="text-lg font-semibold tracking-[-.02em] text-slate-950">
                                                {totalFindings}
                                            </div>
                                            <div className="text-[11px] font-medium uppercase tracking-[.08em] text-slate-400">
                                                recorded results
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="divide-y divide-slate-100">
                                    {scans.map((scan) => {
                                        const meta = scanStatusMeta(scan.status);
                                        const StatusIcon = meta.icon;
                                        const findings = Number(scan.finding_count || 0);

                                        return (
                                            <button
                                                key={scan.id}
                                                type="button"
                                                onClick={async () => {
                                                    await openScan(scan.id);
                                                    setPage("dashboard");
                                                }}
                                                className="group grid w-full gap-4 px-5 py-5 text-left transition-colors hover:bg-slate-50/80 sm:px-7 md:grid-cols-[minmax(0,1fr)_150px_150px_40px] md:items-center"
                                            >
                                                <div className="min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <Search
                                                            className="h-4 w-4 shrink-0 text-slate-400"
                                                            strokeWidth={1.8}
                                                        />
                                                        <span className="truncate text-sm font-semibold text-slate-950">
                                                            {scan.target}
                                                        </span>
                                                    </div>
                                                    <div className="mt-1.5 pl-6 text-xs text-slate-400">
                                                        {new Date(scan.created_at).toLocaleString()}
                                                    </div>
                                                </div>

                                                <div className="pl-6 md:pl-0">
                                                    <div className="text-[10px] font-bold uppercase tracking-[.09em] text-slate-400 md:hidden">
                                                        Results
                                                    </div>
                                                    <div className="mt-1 text-sm font-semibold text-slate-800 md:mt-0">
                                                        {findings} {findings === 1 ? "result" : "results"}
                                                    </div>
                                                </div>

                                                <div className="pl-6 md:pl-0">
                                                    <div
                                                        className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-bold ${meta.iconBg} ${meta.iconClass}`}
                                                    >
                                                        <StatusIcon className="h-4 w-4" strokeWidth={2} />
                                                        {meta.label}
                                                    </div>
                                                </div>

                                                <div className="hidden h-9 w-9 items-center justify-center rounded-full text-slate-400 transition-all group-hover:bg-white group-hover:text-slate-950 group-hover:shadow-sm md:flex">
                                                    <ChevronRight className="h-4 w-4" strokeWidth={2} />
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </section>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}

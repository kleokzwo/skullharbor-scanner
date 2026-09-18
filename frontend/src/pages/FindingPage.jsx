import React from "react";
import {Header, MobileNav, Sidebar, Icon, DetailRow, Explanation, severityClass} from "../components/ui.jsx";
import { ArrowLeft, ArrowRight, ShieldCheck, ExternalLink } from "lucide-react";

export default function FindingPage(props) {
  const {page, setPage, productStatus, users, userId, setUserId, scans, setScans, targets, setTargets, target, setTarget, newDomain, setNewDomain, targetMessage, error, setup, setSetup, devAuthority, activationBusy, activationProduct, activateDevelopmentAccess, addTarget, verifyTarget, copyText, submitCustomerSetup, selected, setSelected, finding, setFinding, job, setJob, openScan, openFinding, closeFinding, moveFinding, findingIndex, findings, counts, active, run, stop, readiness} = props;
    const isSurface = finding?.coverage_family === "Public service exposure" || finding?.category === "External Service Exposure";
    const resultLabel = isSurface ? "OBSERVATION" : "FINDING";

    // FindingPage is an overlay/detail state. Merely changing `page` is not
    // enough because AppController keeps rendering this page while `finding`
    // is still selected. Navigation from the app shell must leave detail state
    // first, then switch the workspace page.
    const navigateFromFinding = (nextPage) => {
      setFinding(null);
      setPage(nextPage);
    };
    return <div className="min-h-screen bg-slate-50">
      <Header productStatus={productStatus}/>
      <MobileNav page={page} setPage={navigateFromFinding}/>
      <div className="flex min-h-[calc(100vh-70px)]">
        <Sidebar page={page} setPage={navigateFromFinding}/>
        <main className="min-w-0 flex-1 px-4 py-6 sm:px-7 lg:px-10 lg:py-10">
          <div className="mx-auto w-full max-w-[1180px]">
            <button onClick={closeFinding} className="mb-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition hover:text-slate-950"><ArrowLeft className="h-4 w-4"/>Back to results</button>
  
            <section className="card overflow-hidden shadow-sm">
              <div className="p-6 sm:p-8 lg:p-10">
                <div className="flex items-center justify-between gap-4">
                  <span className={`pill ${severityClass(finding.severity)}`}>{finding.severity}</span>
                  <span className="pill bg-emerald-50 text-emerald-700">{resultLabel}</span>
                </div>
                <h1 className="mt-5 max-w-4xl text-3xl font-semibold tracking-[-.035em] text-slate-950 sm:text-[42px] sm:leading-[1.05]">{finding.title}</h1>
                <p className="mt-3 max-w-3xl text-base leading-7 text-slate-500">{finding.description||"General web security information"}</p>
              </div>
              <div className="grid border-t border-slate-200 bg-slate-50/60 sm:grid-cols-3">
                <div className="p-5 sm:px-7"><div className="text-xs text-slate-400">Target</div><div className="mt-1 break-all text-sm font-semibold">{finding.url||selected?.target}</div></div>
                <div className="border-t border-slate-200 p-5 sm:border-l sm:border-t-0 sm:px-7"><div className="text-xs text-slate-400">Security check</div><div className="mt-1 text-sm font-semibold">SkullHarbor Quick Check</div></div>
                <div className="border-t border-slate-200 p-5 sm:border-l sm:border-t-0 sm:px-7"><div className="text-xs text-slate-400">Scan date</div><div className="mt-1 text-sm font-semibold">{selected?.created_at?new Date(selected.created_at).toLocaleString():"—"}</div></div>
              </div>
            </section>
  
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              <Explanation icon="search" title={isSurface?"What did we observe?":"What did we find?"} text={finding.description||"The web security check returned an informational observation about the target."}/>
              <Explanation icon="shield" title="Why does this matter?" text={finding.impact||"This result may reveal useful technical information about the server, which could help an attacker. Review whether this information needs to be exposed."}/>
              <Explanation icon="wrench" title="What should I do?" text={finding.recommendation||"Review the affected URL and technical evidence. If possible, remove or restrict unnecessary exposure before going into production."}/>
            </div>
  
            <section className="card mt-5 overflow-hidden">
              <DetailRow icon="code" title="Evidence & details"><div className="space-y-4"><div><div className="text-xs font-bold uppercase tracking-wider text-slate-400">Category</div><div className="mt-1 text-sm font-semibold text-slate-700">{finding.category||"General"}</div></div><div><div className="font-semibold text-slate-700">Observed evidence</div><p className="mt-2 whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">{finding.evidence||"No additional evidence was returned."}</p></div></div></DetailRow>
              <DetailRow icon="link" title="References"><p className="break-words text-sm leading-6 text-slate-500">{finding.reference||"No external reference is available for this result."}</p></DetailRow>
            </section>
  
            <div className="mt-6 flex items-center justify-between">
              <span className="hidden text-xs font-medium text-slate-400 sm:block">Navigate through this scan’s results</span><div className="grid grid-cols-2 gap-2 sm:flex">
                <button onClick={()=>moveFinding(-1)} disabled={findingIndex<=0} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-500 disabled:opacity-40"><ArrowLeft className="h-4 w-4"/>Previous result</button>
                <button onClick={()=>moveFinding(1)} disabled={findingIndex<0||findingIndex>=findings.length-1} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-500 disabled:opacity-40">Next result<ArrowRight className="h-4 w-4"/></button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>;
}

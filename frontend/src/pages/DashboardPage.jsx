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
  const isAdvanced = selected?.scan_profile === "monthly";
  const coverageCount = name => findings.filter(f => (f.coverage_family || "Core web security") === name).length;
  const highCritical = (counts.high || 0) + (counts.critical || 0);
  const servicePort = finding => {
    const text = `${finding.title || ""} ${finding.description || ""}`;
    const match = text.match(/(?:TCP\s*\/?\s*|port\s*)(\d{1,5})/i);
    return match ? `TCP / ${match[1]}` : "—";
  };
  const serviceName = finding => (finding.title || "Service").replace(/\s+publicly reachable.*$/i, "").trim();
  return <div className="min-h-screen bg-slate-50">
    <Header productStatus={productStatus}/>
    <MobileNav page={page} setPage={setPage}/>
    <div className="flex min-h-[calc(100vh-70px)]">
      <Sidebar page={page} setPage={setPage}/>
      <main className="workspace min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10">
        <div className="mx-auto max-w-[1280px]">
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

          {selected&&selected.status==="completed"&&<section className="results-report mt-6">
            <div className="report-title-row">
              <div className="flex min-w-0 items-start gap-4">
                <span className="report-complete-icon"><Icon name={isAdvanced?"shield":"check"} className="h-8 w-8"/></span>
                <div className="min-w-0"><h2 className="text-3xl tracking-[-.035em] text-slate-950">{isAdvanced?"Advanced Security Check Complete":"Scan complete"}</h2><b className="mt-1 block break-all text-sm text-slate-800">{selected.target}</b><p className="mt-1 text-xs text-slate-500">{selected.created_at?`Completed on ${new Date(selected.created_at).toLocaleString()}`:"Completed"}{isAdvanced?" · All 3 scan categories completed successfully.":""}</p></div>
              </div>
              {isAdvanced&&<div className="report-title-metrics">
                <div><b>{findings.filter(f=>(f.coverage_family||"Core web security")!=="Public service exposure").length}</b><span>Findings</span></div>
                <div><b className={highCritical?"text-red-600":""}>{highCritical}</b><span>High / Critical</span></div>
                <div><b>{coverageCount("Public service exposure")}</b><span>Observations</span></div>
              </div>}
            </div>

            {isAdvanced ? <div className="result-timeline">
              {coverageOrder.map((name,index)=>{
                const items=findings.filter(f=>(f.coverage_family||"Core web security")===name);
                const surface=name==="Public service exposure";
                const vuln=name==="Vulnerability & exposure checks";
                const icon=surface?"network":vuln?"shield":"globe";
                return <section key={name} className={`result-section result-section-${index+1}`}>
                  <span className="timeline-number">{String(index+1).padStart(2,"0")}</span>
                  <div className="result-section-head"><span className="section-icon"><Icon name={icon} className="h-6 w-6"/></span><div className="min-w-0 flex-1"><h3>{name}</h3><p>{coverageHelp[name]}</p></div><b className="section-count">{items.length} {surface?"Observation":"Finding"}{items.length===1?"":"s"}</b></div>
                  {items.length===0 ? <div className="no-exposures"><span><Icon name="check" className="h-7 w-7"/></span><b>No exposures detected</b><p>Targeted security checks completed. No vulnerabilities or exposures were found.</p></div> : surface ? <div className="result-table"><div className="result-table-head surface-grid"><span>#</span><span>Severity</span><span>Service</span><span>Port / Protocol</span><span>Description</span><span>Action</span></div>{items.map((f,i)=><div key={f.id} className="result-table-row surface-grid"><span>{String(i+1).padStart(2,"0")}</span><span><i className={`pill not-italic ${severityClass(f.severity)}`}>{f.severity}</i></span><b>{serviceName(f)}</b><b>{servicePort(f)}</b><span className="truncate text-slate-500">{f.description||"Public service is reachable from the internet."}</span><button onClick={()=>openFinding(f)} className="view-action">View <Icon name="arrow-right" className="h-4 w-4"/></button></div>)}</div> : <div className="result-table"><div className="result-table-head finding-grid"><span>#</span><span>Severity</span><span>Finding</span><span>Description</span><span>Action</span></div>{items.map((f,i)=><div key={f.id} className="result-table-row finding-grid"><span>{String(i+1).padStart(2,"0")}</span><span><i className={`pill not-italic ${severityClass(f.severity)}`}>{f.severity}</i></span><b>{f.title}</b><span className="truncate text-slate-500">{f.description||"General web security information"}</span><button onClick={()=>openFinding(f)} className="view-action">View <Icon name="arrow-right" className="h-4 w-4"/></button></div>)}</div>}
                  {surface&&<div className="good-to-know"><Icon name="lightbulb" className="h-6 w-6"/><div><b>Good to know</b><p>Public services may be intentionally exposed. Review each service and ensure it is required and properly secured.</p></div></div>}
                </section>;
              })}
            </div> : <div className="card mt-4 overflow-hidden">{findings.length===0?<Empty title="No findings in this check" text="Nothing actionable was detected by this check. This is not a guarantee that the website has no vulnerabilities."/>:<div>{findings.map(f=><button key={f.id} onClick={()=>openFinding(f)} className="grid w-full grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-slate-100 px-5 py-4 text-left last:border-b-0 hover:bg-slate-50"><span className={`pill ${severityClass(f.severity)}`}>{f.severity}</span><span><b className="block text-sm">{f.title}</b><small className="text-xs text-slate-400">{f.description}</small></span><span className="view-action">View <Icon name="arrow-right" className="h-4 w-4"/></span></button>)}</div>}</div>}
          </section>}

          {selected&&selected.status!=="completed"&&<section className="card mt-4 overflow-hidden"><Empty title="No result published" text="This check did not complete, so SkullHarbor did not publish a partial security result."/></section>}
  
          <footer className="py-7 text-[10px] text-slate-400">Use only against systems you own or are explicitly authorized to test.</footer>
        </div>
      </main>
    </div>
  </div>;
}

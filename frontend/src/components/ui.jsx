import React from "react";

// Security contract: Your access and scope are checked again by SkullHarbor when the scan starts.
export const LEVELS = ["critical", "high", "medium", "low", "info"];

export function Icon({name, className="h-5 w-5"}) {
  const common={className,fill:"none",stroke:"currentColor",strokeWidth:"1.8",viewBox:"0 0 24 24","aria-hidden":"true"};
  if(name==="home") return <svg {...common}><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V20h13v-9.5M9.5 20v-6h5v6"/></svg>;
  if(name==="doc") return <svg {...common}><path d="M6 3.5h8l4 4V20H6z"/><path d="M14 3.5V8h4M9 12h6M9 15.5h6"/></svg>;
  if(name==="shield") return <svg {...common}><path d="M12 3 4.5 6v5.5c0 4.8 3 7.8 7.5 9.5 4.5-1.7 7.5-4.7 7.5-9.5V6z"/></svg>;
  if(name==="gear") return <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19 13.5v-3l-2-.6a7 7 0 0 0-.8-1.9l1-1.8-2.1-2.1-1.8 1a7 7 0 0 0-1.9-.8L10.8 2h-3l-.6 2.1a7 7 0 0 0-1.9.8l-1.8-1-2.1 2.1 1 1.8a7 7 0 0 0-.8 1.9L0 10.5v3l2 .6c.2.7.5 1.3.8 1.9l-1 1.8 2.1 2.1 1.8-1c.6.4 1.2.6 1.9.8l.6 2.1h3l.6-2.1c.7-.2 1.3-.5 1.9-.8l1.8 1 2.1-2.1-1-1.8c.4-.6.6-1.2.8-1.9z" transform="translate(2 -0.1) scale(.83)"/></svg>;
  if(name==="info") return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M12 10.5v6M12 7.5h.01"/></svg>;
  if(name==="link") return <svg {...common}><path d="M9.5 14.5 14.5 9"/><path d="M7.2 16.8 5.8 18.2a3.5 3.5 0 0 1-5-5L5 9a3.5 3.5 0 0 1 5 0" transform="translate(2)"/><path d="m16.8 7.2 1.4-1.4a3.5 3.5 0 0 1 5 5L19 15a3.5 3.5 0 0 1-5 0" transform="translate(-2)"/></svg>;
  if(name==="play") return <svg {...common} fill="currentColor" stroke="none"><path d="m8 5 11 7-11 7z"/></svg>;
  if(name==="check") return <svg {...common}><path d="m5 12.5 4.2 4L19 7"/></svg>;
  if(name==="copy") return <svg {...common}><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>;
  if(name==="globe") return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.5 3.8 5.5 3.8 9S14.5 18.5 12 21c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3z"/></svg>;
  if(name==="clock") return <svg {...common}><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>;
  if(name==="search") return <svg {...common}><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg>;
  if(name==="wrench") return <svg {...common}><path d="M14.5 6.5a4.5 4.5 0 0 0-6 5.8L3.5 17.3l3.2 3.2 5-5a4.5 4.5 0 0 0 5.8-6l-3 3-3-3z"/></svg>;
  if(name==="code") return <svg {...common}><path d="m9 6-6 6 6 6M15 6l6 6-6 6M13 4l-2 16"/></svg>;
  if(name==="trash") return <svg {...common}><path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13M10 10v7M14 10v7"/></svg>;
  if(name==="chevron") return <svg {...common}><path d="m9 6 6 6-6 6"/></svg>;
  if(name==="arrow-left") return <svg {...common}><path d="M19 12H5m6-6-6 6 6 6"/></svg>;
  if(name==="arrow-right") return <svg {...common}><path d="M5 12h14m-6-6 6 6-6 6"/></svg>;
  return null;
}

function fmtTime(total=0){
  const h=String(Math.floor(total/3600)).padStart(2,"0");
  const m=String(Math.floor((total%3600)/60)).padStart(2,"0");
  const s=String(total%60).padStart(2,"0");
  return `${h}:${m}:${s}`;
}

export function severityClass(level){ return `severity-${level || "info"}`; }
export function statusClass(status){ return `status-${status || "completed"}`; }
function daysRemaining(validUntil){
  if(!validUntil) return null;
  const end=new Date(validUntil);
  if(Number.isNaN(end.getTime())) return null;
  return Math.max(0,Math.ceil((end.getTime()-Date.now())/86400000));
}
export function customerPlanState(status){
  const access=(status?.access||"").toUpperCase();
  const key=(status?.product_key||status?.scan_profile||"").toLowerCase();
  const remaining=daysRemaining(status?.valid_until);
  if(access==="TRIAL" && key==="free") return {title:"SkullHarbor Free Trial",badge:remaining===null?"Trial":remaining===1?"1 day left":`${remaining} days left`,tone:"trial",detail:remaining===0?"Trial ends today":`Free Trial · ${remaining ?? "—"} days left`};
  if(access==="ACTIVE" && key==="monthly") return {title:"SkullHarbor Advanced",badge:"Active",tone:"active",detail:"Advanced · Active"};
  if(access==="EXPIRED") return {title:key==="monthly"?"SkullHarbor Advanced":"SkullHarbor Free Trial",badge:"Expired",tone:"inactive",detail:"Plan expired"};
  if(access==="NO_SEAT") return {title:key==="monthly"?"SkullHarbor Advanced":"SkullHarbor",badge:"Seat required",tone:"inactive",detail:"Plan needs attention"};
  return {title:key==="monthly"?"SkullHarbor Advanced":key==="free"?"SkullHarbor Free Trial":"No active plan",badge:"Inactive",tone:"inactive",detail:"Activation required"};
}
function customerStage(stage){
  const labels={queued:"Preparing check",authorizing:"Confirming authorization","web-security":"Checking website",processing:"Reviewing results",saving:"Saving results",completed:"Check complete",stopping:"Stopping check",stopped:"Check stopped",failed:"Check could not complete"};
  return labels[stage] || "Running security checks";
}
export function resultHeadline(findings=[]){
  if(findings.some(f=>f.severity==="critical"||f.severity==="high")) return "Important issues need attention";
  if(findings.length) return "Review your security findings";
  return "No findings in this Quick Check";
}

function Brand(){
  return <div className="flex items-center gap-2.5 whitespace-nowrap font-extrabold tracking-tight text-slate-950">
    <span className="brand-mark">☠</span><span>SKULLHARBOR</span>
  </div>;
}

export function Header({productStatus}){
  return <header className="app-header">
    <div className="flex h-full items-center justify-between px-5 sm:px-7 lg:px-8">
      <Brand/>
      <div className="flex items-center gap-4 sm:gap-6">
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-extrabold text-emerald-700">{productStatus?.product || "SKULLHARBOR"}</span>
        <button className="hidden items-center gap-1 text-sm font-bold text-slate-900 sm:flex">kzwo <span className="text-slate-400">⌄</span></button>
      </div>
    </div>
  </header>;
}

export function Sidebar({page,setPage}){
  const item=(id,label,icon)=><button onClick={()=>setPage(id)} className={`nav-item ${page===id?"nav-item-active":""}`}><Icon name={icon}/>{label}</button>;
  return <aside className="app-sidebar hidden lg:block">
    <nav className="space-y-1 px-2 py-6">
      {item("dashboard","Dashboard","home")}
      {item("scans","Scans","doc")}
      {item("targets","Targets","shield")}
      {item("settings","Settings","gear")}
      <button className="nav-item"><Icon name="info"/>About</button>
    </nav>
    <div className="sidebar-foot">LOCAL SECURITY<br/>WORKSPACE</div>
  </aside>;
}

export function MobileNav({page,setPage}){
  const item=(id,label,icon)=><button onClick={()=>setPage(id)} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${page===id?"bg-blue-50 font-semibold text-blue-600":"text-slate-500"}`}><Icon name={icon} className="h-4 w-4"/>{label}</button>;
  return <div className="border-b border-slate-200 bg-white px-3 py-2 lg:hidden"><div className="flex gap-1 overflow-x-auto">{item("dashboard","Dashboard","home")}{item("scans","Scans","doc")}{item("targets","Targets","shield")}{item("settings","Settings","gear")}</div></div>;
}

export function PlanCard({title,subtitle,features,current=false,emphasized=false}){
  return <article className={`relative rounded-[20px] border bg-white p-5 ${emphasized?"border-emerald-300 shadow-[0_12px_30px_rgba(15,23,42,.06)]":"border-slate-200"}`}>
    {current&&<span className="absolute right-4 top-4 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wide text-emerald-700">Current</span>}
    <h4 className="pr-16 text-base font-extrabold text-slate-950">{title}</h4><p className="mt-1 min-h-[40px] text-xs leading-5 text-slate-500">{subtitle}</p>
    <div className="my-4 border-t border-slate-100"/>
    <ul className="space-y-3">{features.map(([included,label])=><li key={label} className={`flex items-start gap-2 text-xs leading-5 ${included?"text-slate-700":"text-slate-400"}`}><span className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full text-[10px] font-black ${included?"bg-emerald-50 text-emerald-700":"bg-slate-100 text-slate-400"}`}>{included?"✓":"—"}</span><span>{label}</span></li>)}</ul>
  </article>;
}

export function DnsValue({label,value,copy}){
  return <div><div className="mb-1.5 text-[11px] font-extrabold uppercase tracking-[.12em] text-slate-400">{label}</div><div className="flex min-h-[50px] items-center gap-2 rounded-xl border border-slate-200 bg-white p-2 pl-3"><code className="min-w-0 flex-1 break-all text-xs font-semibold text-slate-600">{value}</code><button type="button" onClick={copy} aria-label={`Copy ${label}`} className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"><Icon name="copy" className="h-4 w-4"/></button></div></div>;
}

export function ProductReadiness({users,userId,setUserId,status,goTargets,goSetup}){
  const verificationOk=status?.verification==="approved";
  const accessOk=["ACTIVE","TRIAL"].includes(status?.access);
  const scopeOk=!!status && (status.ownership_verified || status.authorized_targets+status.active_engagements>0);
  const allReady=verificationOk&&accessOk&&scopeOk;
  const planState=customerPlanState(status);
  const item=(label,ok,waiting,readyText="Ready")=><div className={`readiness-item ${ok?"is-ready":""}`}><span className="readiness-icon"><Icon name={ok?"check":"clock"} className="h-4 w-4"/></span><span><b>{label}</b><small>{ok?readyText:waiting}</small></span></div>;
  return <section className={`readiness-panel mt-7 ${allReady?"is-complete":""}`}>
    <div className="readiness-head">
      <div><p className="eyebrow">QUICK CHECK STATUS</p><h2>{allReady?"Ready to scan":scopeOk?"Website verified":"Setup required"}</h2><p>{status?.next_action || (users.length?"Choose your customer profile.":"Set up your SkullHarbor customer profile to continue.")}</p></div>
      {users.length>0&&<div className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-right"><div className="text-[10px] font-extrabold uppercase tracking-[.12em] text-slate-400">Organization</div><div className="mt-0.5 text-sm font-bold text-slate-800">{users.find(u=>String(u.id)===String(userId))?.company_name||users.find(u=>String(u.id)===String(userId))?.name||"SkullHarbor customer"}</div></div>}
    </div>
    <div className="readiness-flow" aria-label="Quick Check readiness">
      {item("Identity",verificationOk,"Verification required")}
      <span className="readiness-connector" aria-hidden="true"/>
      {item("Product access",accessOk,"Activation required",planState.detail)}
      <span className="readiness-connector" aria-hidden="true"/>
      {item("Authorized website",scopeOk,"Verify ownership")}
    </div>
    {!verificationOk&&<button onClick={goSetup} className="secondary-action mt-5">{users.length?"View verification status":"Set up customer profile"} <Icon name="arrow-right" className="h-4 w-4"/></button>}
    {verificationOk&&!accessOk&&<div className="mt-5 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600"><b>Product activation is required.</b> Access is issued only after trusted SkullHarbor verification; this app cannot self-approve or create a license.</div>}
    {!scopeOk&&verificationOk&&accessOk&&<button onClick={goTargets} className="secondary-action mt-5">Verify a website <Icon name="arrow-right" className="h-4 w-4"/></button>}
  </section>;
}
export function Explanation({icon,title,text}){
  return <article className="card flex gap-4 p-5 sm:p-6"><div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600"><Icon name={icon}/></div><div><h2 className="text-base font-extrabold sm:text-lg">{title}</h2><p className="mt-1 text-sm leading-6 text-slate-500 sm:text-[15px]">{text}</p></div></article>;
}

export function DetailRow({icon,title,children}){
  return <details className="group border-b border-slate-200 last:border-b-0"><summary className="flex list-none items-center gap-3 px-5 py-4 font-bold text-slate-800 hover:bg-slate-50 sm:px-6"><Icon name={icon} className="h-5 w-5 text-slate-500"/><span>{title}</span><span className="ml-auto text-slate-400 transition group-open:rotate-180">⌄</span></summary><div className="border-t border-slate-100 px-5 py-4 sm:px-14 sm:py-5">{children}</div></details>;
}

export function Empty({title,text,small=false}){
  return <div className={`${small?"min-h-[150px]":"min-h-[210px]"} flex flex-col items-center justify-center px-6 text-center`}><b className="text-sm text-slate-700">{title}</b><span className="mt-1 text-xs text-slate-400">{text}</span></div>;
}

export function ProgressCard({job,target,active,stop}){
  const running=["queued","running"].includes(job.status);
  const title=running?customerStage(job.stage):job.status==="completed"?"Check complete":job.status==="stopped"?"Check stopped":"Check could not complete";
  return <section className="scan-progress mt-6">
    <div className="flex items-start justify-between gap-4"><div className="flex min-w-0 gap-3"><span className={`scan-state-dot ${running?"is-running":job.status==="completed"?"is-done":"is-error"}`}><Icon name={job.status==="completed"?"check":"shield"} className="h-5 w-5"/></span><div className="min-w-0"><div className="text-base font-extrabold text-slate-950">{title}</div><div className="mt-1 truncate text-xs text-slate-400">{target}</div></div></div><div className="shrink-0 text-xs font-semibold text-slate-400">{fmtTime(job.elapsed_seconds)}</div></div>
    <div className="mt-6 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-950 transition-all duration-500" style={{width:`${job.progress||0}%`}}></div></div>
    <div className="mt-3 flex items-center justify-between gap-4 text-xs"><span className="text-slate-500">{running?"SkullHarbor is running the permitted checks locally on this device.":job.status==="completed"?"Results are ready to review.":job.status==="stopped"?"The check was stopped before completion.":"The check ended before results could be completed."}</span><b className="text-slate-700">{job.progress||0}%</b></div>
    {active&&<div className="mt-5 flex justify-end"><button type="button" onClick={stop} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50">Stop check</button></div>}
  </section>;
}

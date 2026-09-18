import React from "react";
import {
  Home, FileText, Shield, Settings, Info, Link2, Play, Check, Copy, Globe2, Clock3,
  Search, Wrench, Code2, Trash2, ChevronRight, ChevronLeft, ArrowRight, ArrowLeft,
  CircleCheck, Network, Lightbulb, Plus, FileCheck2
} from "lucide-react";

// Security contract: Your access and scope are checked again by SkullHarbor when the scan starts.
export const LEVELS = ["critical", "high", "medium", "low", "info"];

export function Icon({name, className="h-5 w-5"}) {
  const icons = {
    home: Home, doc: FileText, shield: Shield, gear: Settings, info: Info, link: Link2,
    play: Play, check: Check, copy: Copy, globe: Globe2, clock: Clock3, search: Search,
    wrench: Wrench, code: Code2, trash: Trash2, chevron: ChevronRight,
    "arrow-left": ArrowLeft, "arrow-right": ArrowRight, "circle-check": CircleCheck,
    network: Network, lightbulb: Lightbulb, plus: Plus, report: FileCheck2
  };
  const Component = icons[name];
  return Component ? <Component className={className} aria-hidden="true" strokeWidth={1.9}/> : null;
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
  const title=running?customerStage(job.stage):job.status==="completed"?"Scan complete":job.status==="stopped"?"Check stopped":"Check could not complete";
  return <section className="scan-progress mt-6">
    <div className="flex items-start justify-between gap-4"><div className="flex min-w-0 gap-3"><span className={`scan-state-dot ${running?"is-running":job.status==="completed"?"is-done":"is-error"}`}><Icon name={job.status==="completed"?"check":"shield"} className="h-5 w-5"/></span><div className="min-w-0"><div className="text-base font-extrabold text-slate-950">{title}</div><div className="mt-1 truncate text-xs text-slate-400">{target}</div></div></div><div className="shrink-0 text-xs font-semibold text-slate-400">{fmtTime(job.elapsed_seconds)}</div></div>
    <div className="mt-6 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-950 transition-all duration-500" style={{width:`${job.progress||0}%`}}></div></div>
    <div className="mt-3 flex items-center justify-between gap-4 text-xs"><span className="text-slate-500">{running?"SkullHarbor is running the permitted checks locally on this device.":job.status==="completed"?"Results are ready to review.":job.status==="stopped"?"The check was stopped before completion.":"The check ended before results could be completed."}</span><b className="text-slate-700">{job.progress||0}%</b></div>
    {active&&<div className="mt-5 flex justify-end"><button type="button" onClick={stop} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50">Stop check</button></div>}
  </section>;
}

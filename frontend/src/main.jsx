import React, {useEffect, useMemo, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
// Security contract: Your access and scope are checked again by SkullHarbor when the scan starts.
const LEVELS = ["critical", "high", "medium", "low", "info"];

function Icon({name, className="h-5 w-5"}) {
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

function severityClass(level){ return `severity-${level || "info"}`; }
function statusClass(status){ return `status-${status || "completed"}`; }
function daysRemaining(validUntil){
  if(!validUntil) return null;
  const end=new Date(validUntil);
  if(Number.isNaN(end.getTime())) return null;
  return Math.max(0,Math.ceil((end.getTime()-Date.now())/86400000));
}
function customerPlanState(status){
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
function resultHeadline(findings=[]){
  if(findings.some(f=>f.severity==="critical"||f.severity==="high")) return "Important issues need attention";
  if(findings.length) return "Review your security findings";
  return "No findings in this Quick Check";
}

function Brand(){
  return <div className="flex items-center gap-2.5 whitespace-nowrap font-extrabold tracking-tight text-slate-950">
    <span className="brand-mark">☠</span><span>SKULLHARBOR</span>
  </div>;
}

function Header({productStatus}){
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

function Sidebar({page,setPage}){
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

function MobileNav({page,setPage}){
  const item=(id,label,icon)=><button onClick={()=>setPage(id)} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${page===id?"bg-blue-50 font-semibold text-blue-600":"text-slate-500"}`}><Icon name={icon} className="h-4 w-4"/>{label}</button>;
  return <div className="border-b border-slate-200 bg-white px-3 py-2 lg:hidden"><div className="flex gap-1 overflow-x-auto">{item("dashboard","Dashboard","home")}{item("scans","Scans","doc")}{item("targets","Targets","shield")}{item("settings","Settings","gear")}</div></div>;
}

function PlanCard({title,subtitle,features,current=false,emphasized=false}){
  return <article className={`relative rounded-[20px] border bg-white p-5 ${emphasized?"border-emerald-300 shadow-[0_12px_30px_rgba(15,23,42,.06)]":"border-slate-200"}`}>
    {current&&<span className="absolute right-4 top-4 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wide text-emerald-700">Current</span>}
    <h4 className="pr-16 text-base font-extrabold text-slate-950">{title}</h4><p className="mt-1 min-h-[40px] text-xs leading-5 text-slate-500">{subtitle}</p>
    <div className="my-4 border-t border-slate-100"/>
    <ul className="space-y-3">{features.map(([included,label])=><li key={label} className={`flex items-start gap-2 text-xs leading-5 ${included?"text-slate-700":"text-slate-400"}`}><span className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full text-[10px] font-black ${included?"bg-emerald-50 text-emerald-700":"bg-slate-100 text-slate-400"}`}>{included?"✓":"—"}</span><span>{label}</span></li>)}</ul>
  </article>;
}

function App(){
  const [page,setPage]=useState("dashboard");
  const [target,setTarget]=useState("");
  const [targets,setTargets]=useState([]);
  const [newDomain,setNewDomain]=useState("");
  const [targetMessage,setTargetMessage]=useState("");
  const [users,setUsers]=useState([]);
  const [userId,setUserId]=useState("");
  const [scans,setScans]=useState([]);
  const [selected,setSelected]=useState(null);
  const [finding,setFinding]=useState(null);
  const [job,setJob]=useState(null);
  const [error,setError]=useState("");
  const [productStatus,setProductStatus]=useState(null);
  const [readiness,setReadiness]=useState(null);
  const [setup,setSetup]=useState({name:"",email:"",company_name:"",company_domain:"",intended_use:"Authorized security testing of systems owned or explicitly authorized by my organization."});
  const [devAuthority,setDevAuthority]=useState(false);
  const [devChecked,setDevChecked]=useState(false);
  const [workspaceLoaded,setWorkspaceLoaded]=useState(false);
  const [activationBusy,setActivationBusy]=useState(false);
  const [activationProduct,setActivationProduct]=useState("");
  const [activationCode,setActivationCode]=useState("");
  const pollRef=useRef(null);
  const active=["queued","running"].includes(job?.status);

  const refresh=async()=>{
    const u=await fetch(`${API}/api/users`);
    const userRows=await u.json();
    setUsers(userRows);
    setWorkspaceLoaded(true);
    // Production has one customer. Development may contain historical rows;
    // never infer/switch identity from another customer's targets or scans.
    let effectiveId=userId;
    if(!effectiveId && userRows.length){
      const approved=userRows.find(row=>row.verification_status==="approved");
      const chosen=approved || userRows[0];
      effectiveId=chosen?.id?String(chosen.id):"";
      if(effectiveId) setUserId(effectiveId);
    }
    if(!effectiveId){setScans([]);setTargets([]);return;}
    const [s,t]=await Promise.all([
      fetch(`${API}/api/scans?user_id=${encodeURIComponent(effectiveId)}`),
      fetch(`${API}/api/targets?user_id=${encodeURIComponent(effectiveId)}`)
    ]);
    if(!s.ok||!t.ok) throw new Error("Could not load customer workspace");
    setScans(await s.json()); setTargets(await t.json());
  };
  useEffect(()=>{refresh().catch(e=>setError(e.message));fetch(`${API}/internal/development-authority/status`).then(r=>{if(r.ok)setDevAuthority(true)}).catch(()=>{}).finally(()=>setDevChecked(true));return()=>clearInterval(pollRef.current)},[]);
  useEffect(()=>{
    if(!userId){setProductStatus(null);setScans([]);setTargets([]);return;}
    Promise.all([
      fetch(`${API}/api/scans?user_id=${encodeURIComponent(userId)}`).then(r=>r.ok?r.json():Promise.reject(new Error("Could not load scans"))),
      fetch(`${API}/api/targets?user_id=${encodeURIComponent(userId)}`).then(r=>r.ok?r.json():Promise.reject(new Error("Could not load targets")))
    ]).then(([scanRows,targetRows])=>{setScans(scanRows);setTargets(targetRows)}).catch(e=>setError(e.message));
    fetch(`${API}/api/users/${userId}/product-status`).then(async r=>{const data=await r.json();if(!r.ok)throw new Error(data.detail||"Could not load product status");setProductStatus(data)}).catch(e=>setError(e.message));
  },[userId,targets.length,scans.length]);
  useEffect(()=>{
    const q=new URLSearchParams();
    if(target)q.set("target",target);
    if(userId)q.set("user_id",userId);
    fetch(`${API}/api/product-readiness?${q.toString()}`).then(async r=>{const data=await r.json();if(!r.ok)throw new Error(data.detail||"Could not load readiness");setReadiness(data)}).catch(e=>setError(e.message));
  },[target,userId,targets.length,scans.length]);
  // Page-scoped feedback must never leak into another workspace/menu.
  // Authorization/verification errors belong only to the action/page that produced them.
  useEffect(()=>{
    setError("");
    setTargetMessage("");
  },[page]);

  useEffect(()=>{
    const onPopState=()=>setFinding(null);
    window.addEventListener("popstate",onPopState);
    return()=>window.removeEventListener("popstate",onPopState);
  },[]);

  const loadDetail=async(id)=>{
    const r=await fetch(`${API}/api/scans/${id}?user_id=${encodeURIComponent(userId)}`); const data=await r.json();
    if(!r.ok) throw new Error(data.detail||"Could not load scan");
    setSelected(data); setFinding(null);
  };
  const pollJob=(id)=>{
    clearInterval(pollRef.current);
    const tick=async()=>{try{
      const r=await fetch(`${API}/api/scans/${id}/status?user_id=${encodeURIComponent(userId)}`); const data=await r.json(); setJob(data);
      if(["completed","failed","stopped"].includes(data.status)){
        clearInterval(pollRef.current); await refresh(); await loadDetail(id);
      }
    }catch(e){setError(e.message);clearInterval(pollRef.current)}};
    tick(); pollRef.current=setInterval(tick,900);
  };
  const run=async(e)=>{e.preventDefault();setError("");setSelected(null);setFinding(null);
    try{
      const r=await fetch(`${API}/api/scan`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target,user_id:userId?Number(userId):null})});
      const data=await r.json(); if(!r.ok) throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail));
      setJob({scan_id:data.scan_id,status:data.status||"queued",stage:"queued",progress:5,logs:[],elapsed_seconds:0,scan_profile:data.scan_profile}); pollJob(data.scan_id);
    }catch(e){setError(e.message)}
  };
  const stop=async()=>{if(job?.scan_id) await fetch(`${API}/api/scans/${job.scan_id}/stop?user_id=${encodeURIComponent(userId)}`,{method:"POST"})};
  const openScan=async(id)=>{setJob(null);clearInterval(pollRef.current);await loadDetail(id)};

  const addTarget=async(e)=>{e.preventDefault();setError("");setTargetMessage("");
    try{const r=await fetch(`${API}/api/targets`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({domain:newDomain,user_id:userId?Number(userId):null})});const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail));setNewDomain("");setTargetMessage("Target added. Add the DNS TXT record shown below, then click Verify.");await refresh();}catch(e){setError(e.message)}};
  const verifyTarget=async(id)=>{setError("");setTargetMessage("");try{const r=await fetch(`${API}/api/targets/${id}/verify?user_id=${encodeURIComponent(userId)}`,{method:"POST"});const data=await r.json();if(!r.ok){const d=data.detail;throw new Error(typeof d==="string"?d:(d?.message||"Verification failed"));}setTargetMessage(`${data.domain} is verified and can now be scanned.`);await refresh();}catch(e){setError(e.message)}};
  const copyText=async(text)=>{try{await navigator.clipboard.writeText(text);setTargetMessage("Copied to clipboard.")}catch{setTargetMessage("Copy failed. Select the value manually.")}};

  const submitCustomerSetup=async(e)=>{e.preventDefault();setError("");
    try{
      let id=userId;
      if(!id){
        const r=await fetch(`${API}/api/users`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:setup.name,email:setup.email})});
        const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail));id=String(data.id);setUserId(id);
      }
      const r=await fetch(`${API}/api/users/${id}/company-profile`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({company_name:setup.company_name,company_domain:setup.company_domain,intended_use:setup.intended_use})});
      const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail));
      await refresh();setPage("dashboard");
    }catch(e){setError(e.message)}
  };

  const activateProduction=async()=>{setError("");setActivationBusy(true);
    try{
      const r=await fetch(`${API}/api/activation`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({activation_code:activationCode})});
      const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:"Activation failed");
      setActivationCode("");await refresh();
    }catch(e){setError(e.message)}finally{setActivationBusy(false)}
  };

  const activateDevelopmentAccess=async(product="free")=>{setError("");setActivationBusy(true);setActivationProduct(product);
    try{
      if(!userId) throw new Error("Choose a customer profile first");
      const r=await fetch(`${API}/internal/development-authority/users/${userId}/access/${product}`,{method:"POST"});
      const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail));
      setProductStatus(data);await refresh();
      const q=new URLSearchParams();if(target)q.set("target",target);q.set("user_id",userId);
      const rr=await fetch(`${API}/api/product-readiness?${q.toString()}`);setReadiness(await rr.json());setPage("dashboard");
    }catch(e){setError(e.message)}finally{setActivationBusy(false);setActivationProduct("")}
  };

  const findings=selected?.findings||[];
  const counts=useMemo(()=>Object.fromEntries(LEVELS.map(x=>[x,findings.filter(f=>f.severity===x).length])),[findings]);
  const findingIndex=finding?findings.findIndex(f=>f.id===finding.id):-1;

  const openFinding=(f)=>{setFinding(f);window.history.pushState({findingId:f.id},"",`#finding-${f.id}`);window.scrollTo({top:0,behavior:"smooth"})};
  const closeFinding=()=>{setFinding(null);if(window.location.hash.startsWith("#finding-")) window.history.back();else window.scrollTo({top:0,behavior:"smooth"})};
  const moveFinding=(delta)=>{const next=findings[findingIndex+delta];if(!next)return;setFinding(next);window.history.replaceState({findingId:next.id},"",`#finding-${next.id}`);window.scrollTo({top:0,behavior:"smooth"})};

  if(workspaceLoaded && devChecked && users.length===0 && !devAuthority){
    return <div className="min-h-screen bg-slate-50"><Header productStatus={null}/><main className="px-4 py-12 sm:px-7 lg:py-20"><div className="mx-auto max-w-[880px]">
      <p className="eyebrow">FIRST RUN</p><h1 className="mt-2 text-[40px] font-black leading-none tracking-[-.045em] text-slate-950 sm:text-[54px]">Welcome to SkullHarbor.</h1>
      <p className="mt-4 max-w-2xl text-base leading-7 text-slate-500">This installation is not activated yet. SkullHarbor requires an approved organization before security checks can be used.</p>
      <section className="mt-8 overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-soft"><div className="grid lg:grid-cols-[.9fr_1.1fr]">
        <div className="bg-slate-950 p-7 text-white sm:p-9"><div className="grid h-12 w-12 place-items-center rounded-2xl bg-white/10"><Icon name="shield"/></div><h2 className="mt-6 text-2xl font-extrabold">Get ready in three steps</h2><div className="mt-7 space-y-5 text-sm"><div className="flex gap-3"><span className="step-dot">1</span><span><b className="block">Register your organization</b><small className="text-slate-400">Company registration happens before the approved download.</small></span></div><div className="flex gap-3"><span className="step-dot">2</span><span><b className="block">Wait for approval</b><small className="text-slate-400">SkullHarbor verifies customer access before activation.</small></span></div><div className="flex gap-3"><span className="step-dot">3</span><span><b className="block">Activate this installation</b><small className="text-slate-400">Activation binds approved product access to this installation.</small></span></div></div></div>
        <div className="p-7 sm:p-9"><div className="rounded-2xl border border-amber-200 bg-amber-50 p-5"><div className="text-sm font-extrabold text-amber-900">Activation required</div><p className="mt-2 text-sm leading-6 text-amber-800">No approved SkullHarbor customer is bound to this installation. Security checks remain locked.</p></div><h3 className="mt-7 text-lg font-extrabold text-slate-950">Already approved?</h3><p className="mt-2 text-sm leading-6 text-slate-500">Enter the one-time activation code issued for your approved organization. SkullHarbor sends only the code and this installation identifier to the trusted Authority — never targets, scans or findings.</p><label className="mt-5 block text-xs font-bold uppercase tracking-wider text-slate-500">Activation code</label><input value={activationCode} onChange={e=>setActivationCode(e.target.value)} autoComplete="off" spellCheck="false" placeholder="Enter activation code" className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400"/><button onClick={activateProduction} disabled={activationBusy||activationCode.trim().length<8} className="primary-action mt-4 disabled:cursor-not-allowed disabled:opacity-50">{activationBusy?"Activating…":"Activate SkullHarbor"}</button>{error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}<p className="mt-3 text-xs leading-5 text-slate-400">Activation fails closed if the Authority is unavailable, the code is invalid, or the signed entitlement does not match this installation.</p></div>
      </div></section><p className="mt-6 text-xs text-slate-400">Targets, scans and findings stay on this device.</p>
    </div></main></div>;
  }

  if(finding){
    return <div className="min-h-screen bg-slate-50">
      <Header productStatus={productStatus}/>
      <main className="px-4 py-5 sm:px-7 sm:py-7 lg:px-8 lg:py-7">
          <div className="max-w-[760px]">
            <button onClick={closeFinding} className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700"><Icon name="arrow-left" className="h-4 w-4"/>Back to results</button>

            <section className="card overflow-hidden">
              <div className="p-5 sm:p-7">
                <div className="flex items-center justify-between gap-4">
                  <span className={`pill ${severityClass(finding.severity)}`}>{finding.severity}</span>
                  <span className="pill bg-emerald-50 text-emerald-700">OPEN</span>
                </div>
                <h1 className="mt-4 text-3xl font-black tracking-[-.035em] text-slate-950 sm:text-4xl">{finding.title}</h1>
                <p className="mt-2 text-base text-slate-500">{finding.description||"General web security information"}</p>
              </div>
              <div className="grid border-t border-slate-200 sm:grid-cols-3">
                <div className="p-5 sm:px-7"><div className="text-xs text-slate-400">Target</div><div className="mt-1 break-all text-sm font-semibold">{finding.url||selected?.target}</div></div>
                <div className="border-t border-slate-200 p-5 sm:border-l sm:border-t-0 sm:px-7"><div className="text-xs text-slate-400">Security check</div><div className="mt-1 text-sm font-semibold">SkullHarbor Quick Check</div></div>
                <div className="border-t border-slate-200 p-5 sm:border-l sm:border-t-0 sm:px-7"><div className="text-xs text-slate-400">Scan date</div><div className="mt-1 text-sm font-semibold">{selected?.created_at?new Date(selected.created_at).toLocaleString():"—"}</div></div>
              </div>
            </section>

            <div className="mt-4 space-y-4">
              <Explanation icon="search" title="What did we find?" text={finding.description||"The web security check returned an informational observation about the target."}/>
              <Explanation icon="shield" title="Why does this matter?" text={finding.impact||"This result may reveal useful technical information about the server, which could help an attacker. Review whether this information needs to be exposed."}/>
              <Explanation icon="wrench" title="What should I do?" text={finding.recommendation||"Review the affected URL and technical evidence. If possible, remove or restrict unnecessary exposure before going into production."}/>
            </div>

            <section className="card mt-4 overflow-hidden">
              <DetailRow icon="code" title="Evidence & details"><div className="space-y-4"><div><div className="text-xs font-bold uppercase tracking-wider text-slate-400">Category</div><div className="mt-1 text-sm font-semibold text-slate-700">{finding.category||"General"}</div></div><div><div className="font-semibold text-slate-700">Observed evidence</div><p className="mt-2 whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">{finding.evidence||"No additional evidence was returned."}</p></div></div></DetailRow>
              <DetailRow icon="link" title="References"><p className="break-words text-sm leading-6 text-slate-500">{finding.reference||"No external reference is available for this finding."}</p></DetailRow>
            </section>

            <div className="mt-6 flex justify-end">
              <div className="grid grid-cols-2 gap-2 sm:flex">
                <button onClick={()=>moveFinding(-1)} disabled={findingIndex<=0} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-500 disabled:opacity-40"><Icon name="arrow-left" className="h-4 w-4"/>Previous finding</button>
                <button onClick={()=>moveFinding(1)} disabled={findingIndex<0||findingIndex>=findings.length-1} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-500 disabled:opacity-40">Next finding<Icon name="arrow-right" className="h-4 w-4"/></button>
              </div>
            </div>
          </div>
      </main>
    </div>;
  }

  if(page==="targets"){
    const customerTargets=targets.filter(t=>!userId || String(t.user_id)===String(userId));
    const pendingTargets=customerTargets.filter(t=>t.status!=="verified");
    const verifiedTargets=customerTargets.filter(t=>t.status==="verified");
    return <div className="min-h-screen bg-slate-50"><Header productStatus={productStatus}/><MobileNav page={page} setPage={setPage}/><div className="flex min-h-[calc(100vh-70px)]"><Sidebar page={page} setPage={setPage}/><main className="min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10"><div className="mx-auto max-w-[1080px]">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between"><div><p className="eyebrow">TARGET AUTHORIZATION</p><h1 className="mt-2 text-[36px] font-black leading-none tracking-[-.045em] text-slate-950 sm:text-[46px]">Verify ownership.</h1><p className="mt-3 max-w-2xl text-[15px] leading-6 text-slate-500 sm:text-base">Before SkullHarbor scans a website, we verify that you control it. This protects your organization and helps prevent unauthorized use.</p></div><div className="flex shrink-0 gap-2"><span className="target-stat"><b>{verifiedTargets.length}</b><small>Ready</small></span><span className="target-stat"><b>{pendingTargets.length}</b><small>Waiting</small></span></div></div>

      <section className="mt-8 overflow-hidden rounded-[22px] border border-slate-200 bg-white shadow-soft">
        <div className="grid lg:grid-cols-[.82fr_1.18fr]">
          <div className="border-b border-slate-200 bg-slate-950 p-6 text-white sm:p-8 lg:border-b-0 lg:border-r">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-white/10"><Icon name="shield"/></div>
            <h2 className="mt-5 text-2xl font-extrabold tracking-tight">Add a website you control</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">You only do this once per domain. SkullHarbor checks a unique DNS record and never treats the UI itself as authorization.</p>
            <div className="mt-6 space-y-4 text-sm"><div className="flex gap-3"><span className="step-dot">1</span><span><b className="block text-white">Enter your domain</b><small className="text-slate-400">Use the root domain, for example company.com.</small></span></div><div className="flex gap-3"><span className="step-dot">2</span><span><b className="block text-white">Add one DNS record</b><small className="text-slate-400">Copy the values SkullHarbor gives you.</small></span></div><div className="flex gap-3"><span className="step-dot">3</span><span><b className="block text-white">Verify and scan</b><small className="text-slate-400">Once verified, the website becomes available for Quick Check.</small></span></div></div>
          </div>
          <div className="p-6 sm:p-8"><div className="text-sm font-extrabold text-slate-950">Website domain</div><p className="mt-1 text-sm text-slate-500">No protocol or path is needed.</p><form onSubmit={addTarget} className="mt-5"><div className="relative"><Icon name="globe" className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400"/><input required value={newDomain} onChange={e=>setNewDomain(e.target.value)} placeholder="company.com" className="h-[58px] w-full rounded-2xl border border-slate-300 bg-white pl-12 pr-4 text-[15px] font-medium outline-none transition focus:border-slate-500 focus:ring-4 focus:ring-slate-100"/></div><button className="mt-3 inline-flex h-[52px] w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-6 font-bold text-white shadow-sm transition hover:bg-emerald-700 sm:w-auto">Continue to verification <Icon name="arrow-right" className="h-4 w-4"/></button></form><div className="mt-5 flex gap-2 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-500"><Icon name="info" className="mt-0.5 h-4 w-4 shrink-0"/><span>Only verify systems you own. Customer systems can instead be authorized through a trusted SkullHarbor engagement.</span></div></div>
        </div>
      </section>

      {error&&<div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}{targetMessage&&<div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{targetMessage}</div>}

      <section className="mt-8"><div className="flex items-center justify-between"><div><h2 className="text-xl font-extrabold tracking-tight text-slate-950">Your websites</h2><p className="mt-1 text-sm text-slate-500">Verified websites are ready for Quick Check.</p></div></div>
      {customerTargets.length===0?<div className="mt-4 rounded-[22px] border border-dashed border-slate-300 bg-white/60"><Empty title="No websites yet" text="Add your first authorized website above."/></div>:<div className="mt-4 space-y-3">{customerTargets.map(t=><article key={t.id} className="overflow-hidden rounded-[20px] border border-slate-200 bg-white shadow-sm"><div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6"><div className="flex min-w-0 items-center gap-4"><span className={`grid h-11 w-11 shrink-0 place-items-center rounded-2xl ${t.status==="verified"?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}><Icon name={t.status==="verified"?"check":"globe"}/></span><div className="min-w-0"><div className="truncate font-extrabold text-slate-950">{t.domain}</div><div className="mt-1 text-xs text-slate-400">{t.status==="verified"?"Ownership verified · Ready for Quick Check":"Verification required"}</div></div></div><span className={`pill ${t.status==="verified"?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}>{t.status==="verified"?"Verified":"Waiting for DNS"}</span></div>
        {t.status!=="verified"&&<div className="border-t border-slate-100 bg-slate-50/70 p-5 sm:p-6"><div className="mb-4"><div className="text-sm font-extrabold text-slate-900">Add this TXT record to your DNS</div><p className="mt-1 text-xs leading-5 text-slate-500">DNS updates can take a little while. Keep this page open or come back later and verify again.</p></div><div className="grid gap-3 lg:grid-cols-2"><DnsValue label="Host / Name" value={t.verification_name} copy={()=>copyText(t.verification_name)}/><DnsValue label="TXT value" value={t.verification_value} copy={()=>copyText(t.verification_value)}/></div><div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><span className="text-xs text-slate-400">Already added the record?</span><button type="button" onClick={()=>verifyTarget(t.id)} className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 text-sm font-bold text-white hover:bg-slate-800"><Icon name="check" className="h-4 w-4"/>Verify ownership</button></div></div>}
        {t.status==="verified"&&<div className="flex items-center justify-between gap-3 border-t border-slate-100 px-5 py-4 sm:px-6"><span className="text-xs text-slate-400">Ownership is verified. Product access is checked before scanning.</span><button type="button" onClick={()=>{setTarget(`https://${t.domain}`);setPage("dashboard")}} className="inline-flex items-center gap-2 text-sm font-bold text-blue-600">Continue <Icon name="arrow-right" className="h-4 w-4"/></button></div>}
      </article>)}</div>}</section>
    </div></main></div></div>;
  }

  if(page==="setup"){
    const current=users.find(u=>String(u.id)===String(userId));
    return <div className="min-h-screen bg-slate-50"><Header productStatus={productStatus}/><MobileNav page={page} setPage={setPage}/><div className="flex min-h-[calc(100vh-70px)]"><Sidebar page={page} setPage={setPage}/><main className="workspace min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10"><div className="mx-auto max-w-[820px]"><p className="eyebrow">CUSTOMER VERIFICATION</p><h1 className="product-title">Verify your organization</h1><p className="product-subtitle">SkullHarbor protects powerful security checks with verified customer access.</p>
      <section className="card mt-7 p-6 sm:p-8">
        {current?<><div className="flex items-center justify-between gap-4"><div><h2 className="text-xl font-extrabold">{current.company_name||current.name}</h2><p className="mt-1 text-sm text-slate-500">{current.email}</p></div><span className={`pill ${current.verification_status==="approved"?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}>{current.verification_status}</span></div><div className="mt-6 rounded-2xl bg-slate-50 p-5"><b className="text-sm">{current.verification_status==="approved"?"Identity verified":"Verification pending"}</b><p className="mt-1 text-sm leading-6 text-slate-500">{current.verification_status==="approved"?"Your organization has been approved by SkullHarbor.":"Your profile is saved. Approval is performed by a trusted SkullHarbor reviewer; the desktop app cannot approve itself."}</p></div>{devAuthority&&<div className="mt-5 rounded-2xl border border-violet-200 bg-violet-50 p-5"><div className="text-[11px] font-extrabold uppercase tracking-[.12em] text-violet-600">Development build</div><h3 className="mt-1 text-base font-extrabold text-slate-950">Trusted test authority</h3><p className="mt-1 text-sm leading-6 text-slate-600">For local product development only. Choose the product policy you want to validate. This control is excluded from production packaging.</p><div className="mt-4 flex flex-wrap gap-3"><button type="button" disabled={activationBusy} onClick={()=>activateDevelopmentAccess("free")} className="secondary-action">{activationBusy&&activationProduct==="free"?"Activating…":"Use FREE test access"}</button><button type="button" disabled={activationBusy} onClick={()=>activateDevelopmentAccess("monthly")} className="primary-action">{activationBusy&&activationProduct==="monthly"?"Activating…":"Use MONTHLY test access"} <Icon name="arrow-right" className="h-4 w-4"/></button></div></div>}</>:<form onSubmit={submitCustomerSetup} className="space-y-4"><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-bold">Your name<input required value={setup.name} onChange={e=>setSetup({...setup,name:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label><label className="text-sm font-bold">Work email<input required type="email" value={setup.email} onChange={e=>setSetup({...setup,email:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label></div><label className="block text-sm font-bold">Organization<input required value={setup.company_name} onChange={e=>setSetup({...setup,company_name:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label><label className="block text-sm font-bold">Organization domain<input required placeholder="company.com" value={setup.company_domain} onChange={e=>setSetup({...setup,company_domain:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label><label className="block text-sm font-bold">Authorized use<textarea required minLength="10" value={setup.intended_use} onChange={e=>setSetup({...setup,intended_use:e.target.value})} className="mt-2 min-h-[110px] w-full rounded-xl border border-slate-300 p-4 font-medium"/></label><button className="primary-action w-full sm:w-auto">Submit for verification <Icon name="arrow-right" className="h-4 w-4"/></button></form>}
      </section>{error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}<button onClick={()=>setPage("dashboard")} className="mt-5 text-sm font-bold text-blue-600">← Back to Quick Check</button></div></main></div></div>;
  }

  if(page==="settings"){
    const current=users.find(u=>String(u.id)===String(userId));
    const currentKey=(productStatus?.product_key||productStatus?.scan_profile||readiness?.product_key||readiness?.scan_profile||"").toLowerCase();
    const isAdvanced=currentKey==="monthly";
    const accessState=(productStatus?.access||readiness?.access||"BLOCKED").toUpperCase();
    const organizationApproved=current?.verification_status==="approved";
    const advancedActive=isAdvanced && accessState==="ACTIVE";
    const validUntil=productStatus?.valid_until||readiness?.valid_until;
    const planState=customerPlanState({...readiness,...productStatus,valid_until:validUntil});
    const planTitle=planState.title;
    const planDescription=isAdvanced?"Advanced Security Check with deeper controlled web-security coverage.":currentKey==="free"?"Quick Check access for the 7-day evaluation period.":"Product access is not currently active for this organization.";
    return <div className="min-h-screen bg-slate-50"><Header productStatus={productStatus}/><MobileNav page={page} setPage={setPage}/><div className="flex min-h-[calc(100vh-70px)]"><Sidebar page={page} setPage={setPage}/><main className="workspace min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10"><div className="mx-auto max-w-[900px]">
      <p className="eyebrow">SETTINGS</p><h1 className="product-title">Account & plan</h1><p className="product-subtitle">Your organization is verified once. Changing plan never creates another profile.</p>
      <section className="card mt-7 p-6 sm:p-8"><div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">Organization</div><div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-xl font-extrabold text-slate-950">{current?.company_name||current?.name||"No organization selected"}</h2><p className="mt-1 text-sm text-slate-500">{current?.email||"No work email available"}</p>{current?.company_domain&&<p className="mt-1 text-xs text-slate-400">{current.company_domain}</p>}</div><span className={`pill ${organizationApproved?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}>{organizationApproved?"Verified organization":current?"Verification pending":"Organization not configured"}</span></div><div className="mt-5 rounded-xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">Your company identity, verified websites and authorization records stay with this account when you upgrade. You do not register again.</div></section>
      <section className="card mt-5 p-6 sm:p-8"><div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"><div><div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">PLAN & BILLING</div><h2 className="mt-1 text-xl font-extrabold text-slate-950">{planTitle}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{planDescription}</p>{validUntil&&<p className="mt-2 text-xs font-semibold text-slate-400">{accessState==="TRIAL"?"Trial ends":"Current access through"} {new Date(validUntil).toLocaleDateString()}</p>}</div><div className="flex flex-col items-start gap-2 sm:items-end"><span className={`pill ${planState.tone==="active"?"bg-emerald-50 text-emerald-700":planState.tone==="trial"?"bg-blue-50 text-blue-700":"bg-slate-100 text-slate-600"}`}>{planState.badge}</span>{advancedActive&&<button type="button" disabled className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-400">Manage subscription · coming later</button>}</div></div>
      {!isAdvanced&&<div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><b className="text-base text-slate-950">Upgrade to Advanced</b><p className="mt-1 max-w-xl text-sm leading-6 text-slate-500">Keep the same organization and authorized websites. Only your SkullHarbor product access changes.</p></div>{devAuthority?<button type="button" disabled={activationBusy||!userId} onClick={()=>activateDevelopmentAccess("monthly")} className="primary-action shrink-0">{activationBusy&&activationProduct==="monthly"?"Activating…":"Test Advanced upgrade"} <Icon name="arrow-right" className="h-4 w-4"/></button>:<button type="button" disabled className="primary-action shrink-0 opacity-60">Upgrade to Advanced</button>}</div></div>}
      {advancedActive&&<div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm leading-6 text-emerald-800"><b>Advanced is active.</b> Your existing organization verification and authorized websites were kept unchanged.</div>}
      {isAdvanced&&!advancedActive&&<div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm leading-6 text-slate-700"><b>Advanced is not active.</b> Existing organization and authorization data remain stored locally; inactive access cannot start new scans.</div>}
      <div className="mt-7 border-t border-slate-200 pt-7"><div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"><div><div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">COMPARE ACCESS</div><h3 className="mt-1 text-lg font-extrabold text-slate-950">Choose the coverage you need</h3></div><p className="max-w-md text-xs leading-5 text-slate-500">Your organization and authorized websites stay the same. Only security-check coverage changes.</p></div>
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <PlanCard title="Free Trial" subtitle="Try the core Quick Check for 7 days." current={currentKey==="free"} features={[
          [true,"Common file and configuration checks"],[true,"Authorized website checks"],[true,"Local scan execution"],[false,"Deeper web-security coverage"],[false,"SQL injection checks"],[false,"Public-service exposure checks"]
        ]}/>
        <PlanCard title="Advanced" subtitle="Broader controlled coverage for ongoing use." current={isAdvanced} emphasized features={[
          [true,"Everything in Free"],[true,"Information disclosure checks"],[true,"Injection and XSS checks"],[true,"SQL injection checks"],[true,"Software identification"],[true,"Public-service exposure checks"]
        ]}/>
        <PlanCard title="Custom / Yearly" subtitle="Managed pentest engagement with an agreed scope." features={[
          [true,"Agreed customer-specific scope"],[true,"Manual security testing"],[true,"Engagement authorization"],[true,"Contract-based delivery"],[false,"Self-service automated tier"],[false,"Unrestricted disruptive testing"]
        ]}/>
      </div></div>
      </section>
      <section className="card mt-5 p-6 sm:p-8"><div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">CUSTOM / YEARLY</div><h2 className="mt-1 text-lg font-extrabold text-slate-950">Managed pentest engagement</h2><p className="mt-2 text-sm leading-6 text-slate-500">Custom yearly work is handled separately with an agreed scope and contract. It is not an unrestricted automated scanner tier.</p></section>
      {devAuthority&&<details className="mt-5 rounded-[22px] border border-violet-200 bg-violet-50 p-6 sm:p-8"><summary className="cursor-pointer text-sm font-extrabold text-violet-700">Development testing controls</summary><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Internal only. Simulate entitlement changes for this same customer. Production packaging excludes this control.</p>{users.length>1&&<label className="mt-4 block max-w-md text-xs font-bold text-violet-800">Development customer workspace<select value={userId} onChange={e=>{setUserId(e.target.value);setTarget("");setSelected(null);setFinding(null);setJob(null);setScans([]);setTargets([]);}} className="mt-2 h-11 w-full rounded-xl border border-violet-200 bg-white px-3 text-sm font-semibold text-slate-800">{users.map(u=><option key={u.id} value={u.id}>{u.company_name||u.name} · {u.email}</option>)}</select></label>}<div className="mt-4 flex flex-wrap gap-3"><button type="button" disabled={activationBusy||!userId} onClick={()=>activateDevelopmentAccess("free")} className="secondary-action">Use FREE test access</button><button type="button" disabled={activationBusy||!userId} onClick={()=>activateDevelopmentAccess("monthly")} className="secondary-action">Use MONTHLY test access</button></div></details>}
      {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    </div></main></div></div>;
  }

  if(page==="scans"){
    return <div className="min-h-screen bg-slate-50"><Header/><MobileNav page={page} setPage={setPage}/><div className="flex min-h-[calc(100vh-70px)]"><Sidebar page={page} setPage={setPage}/><main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-7 lg:py-8"><div className="max-w-[930px]"><p className="eyebrow">SCAN HISTORY</p><h1 className="mt-2 text-[34px] font-black tracking-[-.04em]">Scans.</h1><section className="card mt-6 overflow-hidden">{scans.length===0?<Empty title="No scans yet" text="Completed scans will appear here."/>:<div>{scans.map(s=><button key={s.id} onClick={async()=>{await openScan(s.id);setPage("dashboard")}} className="grid w-full grid-cols-[1fr_auto_auto] items-center gap-3 border-b border-slate-100 px-5 py-4 text-left last:border-0 hover:bg-slate-50"><span><b className="block text-sm">{s.target}</b><small className="text-xs text-slate-400">{new Date(s.created_at).toLocaleString()} · {s.finding_count} findings</small></span><span className={`pill ${statusClass(s.status)}`}>{s.status}</span><Icon name="chevron" className="h-4 w-4 text-slate-400"/></button>)}</div>}</section></div></main></div></div>;
  }

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

          {selected&&<section className="card mt-5 p-5 sm:p-6">
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
          </section>}

          <section className="mt-4 grid gap-4 md:grid-cols-[1.15fr_.85fr]">
            <div className="card overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                <h2 className="text-xl font-extrabold">Findings {selected?`(${findings.length})`:""}</h2>
              </div>
              {active?<Empty title="Scan in progress" text="Results appear here when the scan is finished."/>:!selected?<Empty title="Select a scan" text="Choose a recent scan to review its findings."/>:findings.length===0?<Empty title="No findings in this check" text="Nothing actionable was detected by this check. This is not a guarantee that the website has no vulnerabilities."/>:<div>{findings.map(f=><button key={f.id} onClick={()=>openFinding(f)} className="grid w-full grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-slate-100 px-5 py-4 text-left transition last:border-b-0 hover:bg-slate-50"><span className={`pill ${severityClass(f.severity)}`}>{f.severity}</span><span className="min-w-0"><b className="block truncate text-sm text-slate-900">{f.title}</b><small className="mt-1 block truncate text-xs text-slate-400">{f.description||"General web security information"}</small></span><span className="inline-flex items-center gap-1 rounded-xl border-2 border-emerald-500 px-3 py-2 text-sm font-bold text-blue-600">View <Icon name="chevron" className="h-4 w-4"/></span></button>)}</div>}
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

function DnsValue({label,value,copy}){
  return <div><div className="mb-1.5 text-[11px] font-extrabold uppercase tracking-[.12em] text-slate-400">{label}</div><div className="flex min-h-[50px] items-center gap-2 rounded-xl border border-slate-200 bg-white p-2 pl-3"><code className="min-w-0 flex-1 break-all text-xs font-semibold text-slate-600">{value}</code><button type="button" onClick={copy} aria-label={`Copy ${label}`} className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"><Icon name="copy" className="h-4 w-4"/></button></div></div>;
}

function ProductReadiness({users,userId,setUserId,status,goTargets,goSetup}){
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
    <div className="readiness-grid">
      {item("Identity",verificationOk,"Verification required")}
      {item("Product access",accessOk,"Activation required",planState.detail)}
      {item("Authorized website",scopeOk,"Verify ownership")}
    </div>
    {!verificationOk&&<button onClick={goSetup} className="secondary-action mt-5">{users.length?"View verification status":"Set up customer profile"} <Icon name="arrow-right" className="h-4 w-4"/></button>}
    {verificationOk&&!accessOk&&<div className="mt-5 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600"><b>Product activation is required.</b> Access is issued only after trusted SkullHarbor verification; this app cannot self-approve or create a license.</div>}
    {!scopeOk&&verificationOk&&accessOk&&<button onClick={goTargets} className="secondary-action mt-5">Verify a website <Icon name="arrow-right" className="h-4 w-4"/></button>}
  </section>;
}
function Explanation({icon,title,text}){
  return <article className="card flex gap-4 p-5 sm:p-6"><div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600"><Icon name={icon}/></div><div><h2 className="text-base font-extrabold sm:text-lg">{title}</h2><p className="mt-1 text-sm leading-6 text-slate-500 sm:text-[15px]">{text}</p></div></article>;
}

function DetailRow({icon,title,children}){
  return <details className="group border-b border-slate-200 last:border-b-0"><summary className="flex list-none items-center gap-3 px-5 py-4 font-bold text-slate-800 hover:bg-slate-50 sm:px-6"><Icon name={icon} className="h-5 w-5 text-slate-500"/><span>{title}</span><span className="ml-auto text-slate-400 transition group-open:rotate-180">⌄</span></summary><div className="border-t border-slate-100 px-5 py-4 sm:px-14 sm:py-5">{children}</div></details>;
}

function Empty({title,text,small=false}){
  return <div className={`${small?"min-h-[150px]":"min-h-[210px]"} flex flex-col items-center justify-center px-6 text-center`}><b className="text-sm text-slate-700">{title}</b><span className="mt-1 text-xs text-slate-400">{text}</span></div>;
}

function ProgressCard({job,target,active,stop}){
  const running=["queued","running"].includes(job.status);
  const title=running?customerStage(job.stage):job.status==="completed"?"Check complete":job.status==="stopped"?"Check stopped":"Check could not complete";
  return <section className="scan-progress mt-6">
    <div className="flex items-start justify-between gap-4"><div className="flex min-w-0 gap-3"><span className={`scan-state-dot ${running?"is-running":job.status==="completed"?"is-done":"is-error"}`}><Icon name={job.status==="completed"?"check":"shield"} className="h-5 w-5"/></span><div className="min-w-0"><div className="text-base font-extrabold text-slate-950">{title}</div><div className="mt-1 truncate text-xs text-slate-400">{target}</div></div></div><div className="shrink-0 text-xs font-semibold text-slate-400">{fmtTime(job.elapsed_seconds)}</div></div>
    <div className="mt-6 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-950 transition-all duration-500" style={{width:`${job.progress||0}%`}}></div></div>
    <div className="mt-3 flex items-center justify-between gap-4 text-xs"><span className="text-slate-500">{running?"SkullHarbor is running the permitted checks locally on this device.":job.status==="completed"?"Results are ready to review.":job.status==="stopped"?"The check was stopped before completion.":"The check ended before results could be completed."}</span><b className="text-slate-700">{job.progress||0}%</b></div>
    {active&&<div className="mt-5 flex justify-end"><button type="button" onClick={stop} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50">Stop check</button></div>}
  </section>;
}

createRoot(document.getElementById("root")).render(<App/>);

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
      <button className="nav-item"><Icon name="gear"/>Settings</button>
      <button className="nav-item"><Icon name="info"/>About</button>
    </nav>
    <div className="sidebar-foot">LOCAL SECURITY<br/>WORKSPACE</div>
  </aside>;
}

function MobileNav({page,setPage}){
  const item=(id,label,icon)=><button onClick={()=>setPage(id)} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${page===id?"bg-blue-50 font-semibold text-blue-600":"text-slate-500"}`}><Icon name={icon} className="h-4 w-4"/>{label}</button>;
  return <div className="border-b border-slate-200 bg-white px-3 py-2 lg:hidden"><div className="flex gap-1 overflow-x-auto">{item("dashboard","Dashboard","home")}{item("scans","Scans","doc")}{item("targets","Targets","shield")}</div></div>;
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
  const [activationBusy,setActivationBusy]=useState(false);
  const pollRef=useRef(null);
  const active=["queued","running"].includes(job?.status);

  const refresh=async()=>{
    const [u,s,t]=await Promise.all([fetch(`${API}/api/users`),fetch(`${API}/api/scans`),fetch(`${API}/api/targets`)]);
    const userRows=await u.json();
    setUsers(userRows); setScans(await s.json()); setTargets(await t.json());
    if(!userId && userRows.length===1) setUserId(String(userRows[0].id));
  };
  useEffect(()=>{refresh().catch(e=>setError(e.message));fetch(`${API}/internal/development-authority/status`).then(r=>{if(r.ok)setDevAuthority(true)}).catch(()=>{});return()=>clearInterval(pollRef.current)},[]);
  useEffect(()=>{
    if(!userId){setProductStatus(null);return;}
    fetch(`${API}/api/users/${userId}/product-status`).then(async r=>{const data=await r.json();if(!r.ok)throw new Error(data.detail||"Could not load product status");setProductStatus(data)}).catch(e=>setError(e.message));
  },[userId,targets.length,scans.length]);
  useEffect(()=>{
    const q=new URLSearchParams();
    if(target)q.set("target",target);
    if(userId)q.set("user_id",userId);
    fetch(`${API}/api/product-readiness?${q.toString()}`).then(async r=>{const data=await r.json();if(!r.ok)throw new Error(data.detail||"Could not load readiness");setReadiness(data)}).catch(e=>setError(e.message));
  },[target,userId,targets.length,scans.length]);
  // A verified target already belongs to one local customer profile. Reuse that
  // association instead of asking the user to select/re-verify it again.
  useEffect(()=>{
    if(!target || active)return;
    try{
      const host=new URL(target.includes("://")?target:`https://${target}`).hostname.toLowerCase().replace(/\.$/,"");
      const owned=targets.find(t=>t.status==="verified" && t.domain.toLowerCase().replace(/\.$/,"")===host);
      if(owned?.user_id && String(owned.user_id)!==String(userId)) setUserId(String(owned.user_id));
    }catch{}
  },[target,targets,userId,active]);
  useEffect(()=>{
    const onPopState=()=>setFinding(null);
    window.addEventListener("popstate",onPopState);
    return()=>window.removeEventListener("popstate",onPopState);
  },[]);

  const loadDetail=async(id)=>{
    const r=await fetch(`${API}/api/scans/${id}`); const data=await r.json();
    if(!r.ok) throw new Error(data.detail||"Could not load scan");
    setSelected(data); setFinding(null);
  };
  const pollJob=(id)=>{
    clearInterval(pollRef.current);
    const tick=async()=>{try{
      const r=await fetch(`${API}/api/scans/${id}/status`); const data=await r.json(); setJob(data);
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
  const stop=async()=>{if(job?.scan_id) await fetch(`${API}/api/scans/${job.scan_id}/stop`,{method:"POST"})};
  const openScan=async(id)=>{setJob(null);clearInterval(pollRef.current);await loadDetail(id)};

  const addTarget=async(e)=>{e.preventDefault();setError("");setTargetMessage("");
    try{const r=await fetch(`${API}/api/targets`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({domain:newDomain,user_id:userId?Number(userId):null})});const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail));setNewDomain("");setTargetMessage("Target added. Add the DNS TXT record shown below, then click Verify.");await refresh();}catch(e){setError(e.message)}};
  const verifyTarget=async(id)=>{setError("");setTargetMessage("");try{const r=await fetch(`${API}/api/targets/${id}/verify`,{method:"POST"});const data=await r.json();if(!r.ok){const d=data.detail;throw new Error(typeof d==="string"?d:(d?.message||"Verification failed"));}setTargetMessage(`${data.domain} is verified and can now be scanned.`);await refresh();}catch(e){setError(e.message)}};
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

  const activateDevelopmentAccess=async()=>{setError("");setActivationBusy(true);
    try{
      if(!userId) throw new Error("Choose a customer profile first");
      const r=await fetch(`${API}/internal/development-authority/users/${userId}/approve-trial`,{method:"POST"});
      const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail));
      setProductStatus(data);await refresh();
      const q=new URLSearchParams();if(target)q.set("target",target);q.set("user_id",userId);
      const rr=await fetch(`${API}/api/product-readiness?${q.toString()}`);setReadiness(await rr.json());setPage("dashboard");
    }catch(e){setError(e.message)}finally{setActivationBusy(false)}
  };

  const findings=selected?.findings||[];
  const counts=useMemo(()=>Object.fromEntries(LEVELS.map(x=>[x,findings.filter(f=>f.severity===x).length])),[findings]);
  const findingIndex=finding?findings.findIndex(f=>f.id===finding.id):-1;

  const openFinding=(f)=>{setFinding(f);window.history.pushState({findingId:f.id},"",`#finding-${f.id}`);window.scrollTo({top:0,behavior:"smooth"})};
  const closeFinding=()=>{setFinding(null);if(window.location.hash.startsWith("#finding-")) window.history.back();else window.scrollTo({top:0,behavior:"smooth"})};
  const moveFinding=(delta)=>{const next=findings[findingIndex+delta];if(!next)return;setFinding(next);window.history.replaceState({findingId:next.id},"",`#finding-${next.id}`);window.scrollTo({top:0,behavior:"smooth"})};

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
                <div className="border-t border-slate-200 p-5 sm:border-l sm:border-t-0 sm:px-7"><div className="text-xs text-slate-400">Detected by</div><div className="mt-1 text-sm font-semibold">SkullHarbor Web Check</div></div>
                <div className="border-t border-slate-200 p-5 sm:border-l sm:border-t-0 sm:px-7"><div className="text-xs text-slate-400">Scan date</div><div className="mt-1 text-sm font-semibold">{selected?.created_at?new Date(selected.created_at).toLocaleString():"—"}</div></div>
              </div>
            </section>

            <div className="mt-4 space-y-4">
              <Explanation icon="search" title="What did we find?" text={finding.description||"The web security check returned an informational observation about the target."}/>
              <Explanation icon="shield" title="Why does this matter?" text={finding.impact||"This result may reveal useful technical information about the server, which could help an attacker. Review whether this information needs to be exposed."}/>
              <Explanation icon="wrench" title="What should I do?" text={finding.recommendation||"Review the affected URL and technical evidence. If possible, remove or restrict unnecessary exposure before going into production."}/>
            </div>

            <section className="card mt-4 overflow-hidden">
              <DetailRow icon="code" title="Technical details"><div className="space-y-4"><div className="grid gap-3 sm:grid-cols-2"><div><div className="text-xs font-bold uppercase tracking-wider text-slate-400">Category</div><div className="mt-1 text-sm font-semibold text-slate-700">{finding.category||"General"}</div></div><div><div className="text-xs font-bold uppercase tracking-wider text-slate-400">Rule</div><div className="mt-1 break-all font-mono text-xs text-slate-500">{finding.rule_id||"web.unclassified"}</div></div></div><div><div className="font-semibold text-slate-700">Evidence</div><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-slate-500">{finding.evidence||"No additional evidence was returned."}</p></div></div></DetailRow>
              <DetailRow icon="doc" title="Raw technical evidence"><pre className="whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 text-xs leading-6 text-slate-600">{finding.raw_output||finding.evidence||"No raw output stored for this finding."}</pre></DetailRow>
              <DetailRow icon="link" title="References"><p className="break-words text-sm leading-6 text-slate-500">{finding.reference||"No external reference is available for this finding."}</p></DetailRow>
            </section>

            <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <button type="button" onClick={()=>alert("False-positive reporting will be connected in a later sprint.")} className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-300 bg-white px-4 py-3 text-sm font-semibold text-red-600 hover:bg-red-50"><Icon name="trash" className="h-4 w-4"/>Report as false positive</button>
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
        {t.status==="verified"&&<div className="flex items-center justify-between gap-3 border-t border-slate-100 px-5 py-4 sm:px-6"><span className="text-xs text-slate-400">Ownership is verified. Product access is checked before scanning.</span><button type="button" onClick={()=>{if(t.user_id)setUserId(String(t.user_id));setTarget(`https://${t.domain}`);setPage("dashboard")}} className="inline-flex items-center gap-2 text-sm font-bold text-blue-600">Continue <Icon name="arrow-right" className="h-4 w-4"/></button></div>}
      </article>)}</div>}</section>
    </div></main></div></div>;
  }

  if(page==="setup"){
    const current=users.find(u=>String(u.id)===String(userId));
    return <div className="min-h-screen bg-slate-50"><Header productStatus={productStatus}/><MobileNav page={page} setPage={setPage}/><div className="flex min-h-[calc(100vh-70px)]"><Sidebar page={page} setPage={setPage}/><main className="workspace min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10"><div className="mx-auto max-w-[820px]"><p className="eyebrow">CUSTOMER VERIFICATION</p><h1 className="product-title">Verify your organization</h1><p className="product-subtitle">SkullHarbor protects powerful security checks with verified customer access.</p>
      <section className="card mt-7 p-6 sm:p-8">
        {current?<><div className="flex items-center justify-between gap-4"><div><h2 className="text-xl font-extrabold">{current.company_name||current.name}</h2><p className="mt-1 text-sm text-slate-500">{current.email}</p></div><span className={`pill ${current.verification_status==="approved"?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}>{current.verification_status}</span></div><div className="mt-6 rounded-2xl bg-slate-50 p-5"><b className="text-sm">{current.verification_status==="approved"?"Identity verified":"Verification pending"}</b><p className="mt-1 text-sm leading-6 text-slate-500">{current.verification_status==="approved"?"Your organization has been approved by SkullHarbor.":"Your profile is saved. Approval is performed by a trusted SkullHarbor reviewer; the desktop app cannot approve itself."}</p></div>{devAuthority&&<div className="mt-5 rounded-2xl border border-violet-200 bg-violet-50 p-5"><div className="text-[11px] font-extrabold uppercase tracking-[.12em] text-violet-600">Development build</div><h3 className="mt-1 text-base font-extrabold text-slate-950">Trusted test authority</h3><p className="mt-1 text-sm leading-6 text-slate-600">For local product development only. This performs the same trusted review and issues a bounded 7-day FREE trial. It is excluded from production packaging.</p><button type="button" disabled={activationBusy} onClick={activateDevelopmentAccess} className="secondary-action mt-4">{activationBusy?"Activating…":"Approve & activate test access"} <Icon name="arrow-right" className="h-4 w-4"/></button></div>}</>:<form onSubmit={submitCustomerSetup} className="space-y-4"><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-bold">Your name<input required value={setup.name} onChange={e=>setSetup({...setup,name:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label><label className="text-sm font-bold">Work email<input required type="email" value={setup.email} onChange={e=>setSetup({...setup,email:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label></div><label className="block text-sm font-bold">Organization<input required value={setup.company_name} onChange={e=>setSetup({...setup,company_name:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label><label className="block text-sm font-bold">Organization domain<input required placeholder="company.com" value={setup.company_domain} onChange={e=>setSetup({...setup,company_domain:e.target.value})} className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 font-medium"/></label><label className="block text-sm font-bold">Authorized use<textarea required minLength="10" value={setup.intended_use} onChange={e=>setSetup({...setup,intended_use:e.target.value})} className="mt-2 min-h-[110px] w-full rounded-xl border border-slate-300 p-4 font-medium"/></label><button className="primary-action w-full sm:w-auto">Submit for verification <Icon name="arrow-right" className="h-4 w-4"/></button></form>}
      </section>{error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}<button onClick={()=>setPage("dashboard")} className="mt-5 text-sm font-bold text-blue-600">← Back to Quick Check</button></div></main></div></div>;
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
                <div><h2 className="text-xl font-extrabold">{selected.status==="completed"?"Scan completed":"Scan result"}</h2><p className="mt-1 break-all text-sm text-slate-500">{selected.target}</p></div>
              </div>
              <div className="text-left text-xs text-slate-400 sm:text-right"><div>{selected.created_at?new Date(selected.created_at).toLocaleString():""}</div><div className="mt-1">Profile: {selected.scan_profile||"Free"} · Engine: SkullHarbor Web Check</div></div>
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
              {active?<Empty title="Scan in progress" text="Results appear here when the scan is finished."/>:!selected?<Empty title="Select a scan" text="Choose a recent scan to review its findings."/>:findings.length===0?<Empty title="No findings" text="No security findings were returned."/>:<div>{findings.map(f=><button key={f.id} onClick={()=>openFinding(f)} className="grid w-full grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-slate-100 px-5 py-4 text-left transition last:border-b-0 hover:bg-slate-50"><span className={`pill ${severityClass(f.severity)}`}>{f.severity}</span><span className="min-w-0"><b className="block truncate text-sm text-slate-900">{f.title}</b><small className="mt-1 block truncate text-xs text-slate-400">{f.description||"General web security information"}</small></span><span className="inline-flex items-center gap-1 rounded-xl border-2 border-emerald-500 px-3 py-2 text-sm font-bold text-blue-600">View <Icon name="chevron" className="h-4 w-4"/></span></button>)}</div>}
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
  const item=(label,ok,waiting)=><div className={`readiness-item ${ok?"is-ready":""}`}><span className="readiness-icon"><Icon name={ok?"check":"clock"} className="h-4 w-4"/></span><span><b>{label}</b><small>{ok?"Ready":waiting}</small></span></div>;
  return <section className={`readiness-panel mt-7 ${allReady?"is-complete":""}`}>
    <div className="readiness-head">
      <div><p className="eyebrow">QUICK CHECK STATUS</p><h2>{allReady?"Ready to scan":scopeOk?"Website verified":"Setup required"}</h2><p>{status?.next_action || (users.length?"Choose your customer profile.":"Set up your SkullHarbor customer profile to continue.")}</p></div>
      {users.length>0&&<select aria-label="Customer profile" value={userId} onChange={e=>setUserId(e.target.value)} className="profile-select"><option value="">Choose profile</option>{users.map(u=><option key={u.id} value={u.id}>{u.name}</option>)}</select>}
    </div>
    <div className="readiness-grid">
      {item("Identity",verificationOk,"Verification required")}
      {item("Product access",accessOk,"Activation required")}
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
  return <section className="card mt-6 p-5 sm:p-6">
    <div className="flex items-start justify-between gap-4"><div><div className="flex items-center gap-2 text-sm font-extrabold text-emerald-700"><span className="h-2 w-2 rounded-full bg-emerald-500"></span>{["queued","running"].includes(job.status)?(job.status==="queued"?"Scan queued":"Scan in progress"):job.status==="completed"?"Scan completed":job.status==="stopped"?"Scan stopped":"Scan failed"}</div><div className="mt-1 break-all text-xs text-slate-400">{target}</div></div><div className="text-xs text-slate-400">Elapsed {fmtTime(job.elapsed_seconds)}</div></div>
    <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-600 transition-all" style={{width:`${job.progress||0}%`}}></div></div>
    <div className="mt-2 flex items-center justify-between text-xs"><span className="text-slate-400">{job.stage||"initializing"}</span><b>{job.progress||0}%</b></div>
    <div className="mt-4 flex items-center justify-between gap-3"><details className="min-w-0 flex-1"><summary className="text-xs font-semibold text-slate-500">Technical scan log</summary><div className="mt-3 max-h-48 overflow-auto rounded-xl bg-slate-900 p-4 font-mono text-xs leading-5 text-slate-200">{(job.logs||[]).length===0?<div>Preparing scanner...</div>:job.logs.map((line,i)=><div key={i}>{line}</div>)}</div></details>{active&&<button type="button" onClick={stop} className="rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-600">Stop</button>}</div>
  </section>;
}

createRoot(document.getElementById("root")).render(<App/>);

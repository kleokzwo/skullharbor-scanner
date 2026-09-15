import React, {useEffect, useMemo, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
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
    <span className="text-xl leading-none">☠</span><span>SKULLHARBOR <span className="text-slate-400">/ UI-SCANNER</span></span>
  </div>;
}

function Header(){
  return <header className="h-[70px] border-b border-slate-200 bg-white">
    <div className="flex h-full items-center justify-between px-5 sm:px-7 lg:px-8">
      <Brand/>
      <div className="flex items-center gap-4 sm:gap-6">
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-extrabold text-emerald-700">FREE PLAN</span>
        <button className="hidden items-center gap-1 text-sm font-bold text-slate-900 sm:flex">kzwo <span className="text-slate-400">⌄</span></button>
      </div>
    </div>
  </header>;
}

function Sidebar({page,setPage}){
  const item=(id,label,icon)=><button onClick={()=>setPage(id)} className={`nav-item ${page===id?"nav-item-active":""}`}><Icon name={icon}/>{label}</button>;
  return <aside className="hidden min-h-[calc(100vh-70px)] w-[160px] shrink-0 border-r border-slate-200 bg-white lg:block">
    <nav className="space-y-1 px-2 py-6">
      {item("dashboard","Dashboard","home")}
      {item("scans","Scans","doc")}
      {item("targets","Targets","shield")}
      <button className="nav-item"><Icon name="gear"/>Settings</button>
      <button className="nav-item"><Icon name="info"/>About</button>
    </nav>
    <div className="fixed bottom-8 ml-7 text-[11px] font-medium uppercase tracking-[.08em] text-slate-300">PENTEST<br/>QUICK CHECK<br/><span className="normal-case">v0.2.1</span></div>
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
  const pollRef=useRef(null);

  const refresh=async()=>{
    const [u,s,t]=await Promise.all([fetch(`${API}/api/users`),fetch(`${API}/api/scans`),fetch(`${API}/api/targets`)]);
    setUsers(await u.json()); setScans(await s.json()); setTargets(await t.json());
  };
  useEffect(()=>{refresh().catch(e=>setError(e.message));return()=>clearInterval(pollRef.current)},[]);
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

  const findings=selected?.findings||[];
  const counts=useMemo(()=>Object.fromEntries(LEVELS.map(x=>[x,findings.filter(f=>f.severity===x).length])),[findings]);
  const active=["queued","running"].includes(job?.status);
  const findingIndex=finding?findings.findIndex(f=>f.id===finding.id):-1;

  const openFinding=(f)=>{setFinding(f);window.history.pushState({findingId:f.id},"",`#finding-${f.id}`);window.scrollTo({top:0,behavior:"smooth"})};
  const closeFinding=()=>{setFinding(null);if(window.location.hash.startsWith("#finding-")) window.history.back();else window.scrollTo({top:0,behavior:"smooth"})};
  const moveFinding=(delta)=>{const next=findings[findingIndex+delta];if(!next)return;setFinding(next);window.history.replaceState({findingId:next.id},"",`#finding-${next.id}`);window.scrollTo({top:0,behavior:"smooth"})};

  if(finding){
    return <div className="min-h-screen bg-slate-50">
      <Header/>
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
    return <div className="min-h-screen bg-slate-50"><Header/><MobileNav page={page} setPage={setPage}/><div className="flex min-h-[calc(100vh-70px)]"><Sidebar page={page} setPage={setPage}/><main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-7 lg:py-8"><div className="max-w-[930px]">
      <p className="eyebrow">AUTHORIZED TARGETS</p><h1 className="mt-2 text-[34px] font-black tracking-[-.04em] text-slate-950">Verify a website.</h1><p className="mt-2 max-w-2xl text-slate-500">Before a scan can start, prove that you control the domain. Add one DNS TXT record once; after verification the target is ready for Quick Check.</p>
      <form onSubmit={addTarget} className="mt-6 grid gap-3 sm:grid-cols-[1fr_auto]"><input required value={newDomain} onChange={e=>setNewDomain(e.target.value)} placeholder="example.com" className="h-[54px] rounded-xl border border-slate-300 bg-white px-4 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50"/><button className="h-[54px] rounded-xl bg-emerald-600 px-7 font-bold text-white hover:bg-emerald-700">Add target</button></form>
      {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}{targetMessage&&<div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{targetMessage}</div>}
      <section className="card mt-6 overflow-hidden"><div className="border-b border-slate-200 px-5 py-4"><h2 className="text-xl font-extrabold">Your targets</h2></div>{targets.length===0?<Empty title="No targets yet" text="Add the first domain you are authorized to scan."/>:<div>{targets.map(t=><div key={t.id} className="border-b border-slate-100 p-5 last:border-b-0"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><div className="font-extrabold text-slate-900">{t.domain}</div><div className="mt-1 text-xs text-slate-400">{t.status==="verified"?"Ready to scan":"Waiting for DNS verification"}</div></div><span className={`pill ${t.status==="verified"?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}>{t.status}</span></div>{t.status!=="verified"&&<div className="mt-4 rounded-xl bg-slate-50 p-4"><div className="text-xs font-bold uppercase tracking-wider text-slate-400">1. Add this DNS TXT record</div><div className="mt-3 grid gap-3"><div><div className="text-xs text-slate-400">Host / Name</div><div className="mt-1 flex items-center gap-2"><code className="min-w-0 flex-1 break-all rounded-lg border border-slate-200 bg-white p-3 text-xs">{t.verification_name}</code><button onClick={()=>copyText(t.verification_name)} className="rounded-lg border border-slate-200 bg-white px-3 py-3 text-xs font-bold">Copy</button></div></div><div><div className="text-xs text-slate-400">Value</div><div className="mt-1 flex items-center gap-2"><code className="min-w-0 flex-1 break-all rounded-lg border border-slate-200 bg-white p-3 text-xs">{t.verification_value}</code><button onClick={()=>copyText(t.verification_value)} className="rounded-lg border border-slate-200 bg-white px-3 py-3 text-xs font-bold">Copy</button></div></div></div><div className="mt-4 flex items-center justify-between gap-3"><span className="text-xs text-slate-400">2. Wait for DNS propagation, then verify.</span><button onClick={()=>verifyTarget(t.id)} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white">Verify</button></div></div>}{t.status==="verified"&&<button onClick={()=>{setTarget(`https://${t.domain}`);setPage("dashboard")}} className="mt-4 text-sm font-bold text-blue-600">Use in Quick Check →</button>}</div>)}</div>}</section>
    </div></main></div></div>;
  }

  if(page==="scans"){
    return <div className="min-h-screen bg-slate-50"><Header/><MobileNav page={page} setPage={setPage}/><div className="flex min-h-[calc(100vh-70px)]"><Sidebar page={page} setPage={setPage}/><main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-7 lg:py-8"><div className="max-w-[930px]"><p className="eyebrow">SCAN HISTORY</p><h1 className="mt-2 text-[34px] font-black tracking-[-.04em]">Scans.</h1><section className="card mt-6 overflow-hidden">{scans.length===0?<Empty title="No scans yet" text="Completed scans will appear here."/>:<div>{scans.map(s=><button key={s.id} onClick={async()=>{await openScan(s.id);setPage("dashboard")}} className="grid w-full grid-cols-[1fr_auto_auto] items-center gap-3 border-b border-slate-100 px-5 py-4 text-left last:border-0 hover:bg-slate-50"><span><b className="block text-sm">{s.target}</b><small className="text-xs text-slate-400">{new Date(s.created_at).toLocaleString()} · {s.finding_count} findings</small></span><span className={`pill ${statusClass(s.status)}`}>{s.status}</span><Icon name="chevron" className="h-4 w-4 text-slate-400"/></button>)}</div>}</section></div></main></div></div>;
  }

  return <div className="min-h-screen bg-slate-50">
    <Header/>
    <MobileNav page={page} setPage={setPage}/>
    <div className="flex min-h-[calc(100vh-70px)]">
      <Sidebar page={page} setPage={setPage}/>
      <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-7 lg:py-8">
        <div className="max-w-[930px]">
          <section>
            <p className="eyebrow">AUTHORIZED TARGET SCANNING</p>
            <h1 className="mt-2 text-[34px] font-black leading-[1.04] tracking-[-.045em] text-slate-950 sm:text-[42px]">Quick security check.</h1>
            <p className="mt-2 text-[15px] text-slate-500 sm:text-[17px]">Find common security issues before the deep dive.</p>

            <form onSubmit={run} className="mt-5 grid gap-3 sm:grid-cols-[1fr_auto]">
              <div className="relative">
                <Icon name="link" className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400"/>
                <input required value={target} onChange={e=>setTarget(e.target.value)} placeholder="https://authorized-target.example" disabled={active} className="h-[54px] w-full rounded-xl border border-slate-300 bg-white pl-12 pr-11 text-[15px] text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-4 focus:ring-blue-50 disabled:bg-slate-100"/>
                {target&&!active&&<button type="button" onClick={()=>setTarget("")} className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-2 text-slate-400 hover:bg-slate-50">×</button>}
              </div>
              <button disabled={active} className="inline-flex h-[54px] items-center justify-center gap-2 rounded-xl bg-emerald-600 px-7 text-[15px] font-bold text-white shadow-sm transition hover:bg-emerald-700 disabled:opacity-60"><Icon name="play" className="h-5 w-5"/>{active?"Scanning...":"Start Scan"}</button>
            </form>
            <div className="mt-2 text-xs text-slate-400">Free plan: Basic web security checks</div>
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

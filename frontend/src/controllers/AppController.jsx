import React, {useEffect, useMemo, useRef, useState} from "react";
import {LEVELS, Icon, Header, MobileNav, Sidebar, Empty, PlanCard, DnsValue, ProductReadiness, ProgressCard, DetailRow, Explanation, severityClass, statusClass, customerPlanState, resultHeadline} from "../components/ui.jsx";
import DashboardPage from "../pages/DashboardPage.jsx";
import ScansPage from "../pages/ScansPage.jsx";
import TargetsPage from "../pages/TargetsPage.jsx";
import SettingsPage from "../pages/SettingsPage.jsx";
import FindingPage from "../pages/FindingPage.jsx";
import SetupPage from "../pages/SetupPage.jsx";

import {API} from "../services/apiClient.js";
// Security contract: Your access and scope are checked again by SkullHarbor when the scan starts.

export default function App(){
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
    // Debounce target-aware readiness. Do not hammer the backend for every
    // intermediate value while the user is typing "https://...". Invalid or
    // incomplete input is simply non-ready; authoritative validation remains
    // at scan start.
    const timer=setTimeout(()=>{
      const q=new URLSearchParams();
      const candidate=(target||"").trim();
      const hostCandidate=candidate.replace(/^https?:\/\//i,"").split(/[\/?#]/,1)[0];
      const looksComplete=!candidate || (hostCandidate.includes(".") && !hostCandidate.endsWith("."));
      if(candidate && looksComplete)q.set("target",candidate);
      if(userId)q.set("user_id",userId);
      fetch(`${API}/api/product-readiness?${q.toString()}`).then(async r=>{
        const data=await r.json();
        if(!r.ok)throw new Error(data.detail||"Could not load readiness");
        setReadiness(data);
      }).catch(e=>setError(e.message));
    },250);
    return()=>clearTimeout(timer);
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

  const pageProps={page,setPage,productStatus,users,userId,setUserId,scans,setScans,targets,setTargets,target,setTarget,newDomain,setNewDomain,targetMessage,error,setup,setSetup,devAuthority,activationBusy,activationProduct,activateDevelopmentAccess,addTarget,verifyTarget,copyText,submitCustomerSetup,selected,setSelected,finding,setFinding,job,setJob,openScan,openFinding,closeFinding,moveFinding,findingIndex,findings,counts,active,run,stop,readiness};
  if(finding) return <FindingPage {...pageProps}/>;
  if(page==="targets") return <TargetsPage {...pageProps}/>;
  if(page==="setup") return <SetupPage {...pageProps}/>;
  if(page==="settings") return <SettingsPage {...pageProps}/>;
  if(page==="scans") return <ScansPage {...pageProps}/>;
  return <DashboardPage {...pageProps}/>;
}


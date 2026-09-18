import React from "react";
import { Check, Minus, ShieldCheck, Sparkles, Building2 } from "lucide-react";
import {
    Header,
    MobileNav,
    Sidebar,
    Icon,
    Empty,
    DnsValue,
    ProductReadiness,
    ProgressCard,
    DetailRow,
    Explanation,
    LEVELS,
    severityClass,
    statusClass,
    customerPlanState,
    resultHeadline,
} from "../components/ui.jsx";

function MarketingPlanCard({
    icon: PlanIcon,
    title,
    eyebrow,
    price,
    priceNote,
    subtitle,
    features,
    current = false,
    emphasized = false,
}) {
    return (
        <article
            className={`relative flex h-full flex-col overflow-hidden rounded-[26px] border p-6 transition-all duration-300 sm:p-7 ${
                emphasized
                    ? "border-emerald-300 bg-[radial-gradient(circle_at_88%_0%,rgba(59,130,246,.10),transparent_34%),linear-gradient(145deg,rgba(236,253,245,.96),#fff_48%,rgba(239,246,255,.88))] shadow-[0_24px_60px_-32px_rgba(15,23,42,.38)] lg:-translate-y-2"
                    : "border-slate-200 bg-white shadow-[0_14px_36px_-30px_rgba(15,23,42,.32)]"
            }`}
        >
            {emphasized && (
                <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-400 via-teal-400 to-blue-400" />
            )}

            <div className="flex items-start justify-between gap-4">
                <div
                    className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${
                        emphasized ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" : "bg-slate-100 text-slate-700"
                    }`}
                >
                    <PlanIcon className="h-5 w-5" strokeWidth={2} />
                </div>
                <div className="flex flex-wrap justify-end gap-2">
                    {eyebrow && (
                        <span
                            className={`rounded-full px-3 py-1 text-[10px] font-extrabold tracking-[.08em] ${
                                emphasized ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
                            }`}
                        >
                            {eyebrow}
                        </span>
                    )}
                    {current && (
                        <span className="rounded-full bg-slate-950 px-3 py-1 text-[10px] font-extrabold tracking-[.08em] text-white">
                            CURRENT
                        </span>
                    )}
                </div>
            </div>

            <div className="mt-5">
                <h4 className="text-[20px] font-bold tracking-[-.025em] text-slate-950">{title}</h4>
                <p className="mt-2 min-h-[48px] text-sm leading-6 text-slate-500">{subtitle}</p>
            </div>

            <div className="mt-5 border-y border-slate-200/80 py-5">
                <div className="flex items-end gap-2">
                    <span className="text-[38px] font-semibold leading-none tracking-[-.05em] text-slate-950">{price}</span>
                    {price !== "Custom" && <span className="pb-1 text-xs font-semibold text-slate-400">{priceNote}</span>}
                </div>
                {price === "Custom" && <p className="mt-2 text-xs font-semibold text-slate-400">{priceNote}</p>}
            </div>

            <ul className="mt-6 flex flex-1 flex-col gap-3.5">
                {features.map(([included, label]) => (
                    <li key={label} className={`flex items-start gap-3 text-sm leading-5 ${included ? "text-slate-700" : "text-slate-400"}`}>
                        <span
                            className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                                included ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-400"
                            }`}
                        >
                            {included ? <Check className="h-3.5 w-3.5" strokeWidth={2.5} /> : <Minus className="h-3.5 w-3.5" strokeWidth={2.5} />}
                        </span>
                        <span>{label}</span>
                    </li>
                ))}
            </ul>
        </article>
    );
}

export default function SettingsPage(props) {
    const {
        page,
        setPage,
        productStatus,
        users,
        userId,
        setUserId,
        scans,
        setScans,
        targets,
        setTargets,
        target,
        setTarget,
        newDomain,
        setNewDomain,
        targetMessage,
        error,
        setup,
        setSetup,
        devAuthority,
        activationBusy,
        activationProduct,
        activateDevelopmentAccess,
        addTarget,
        verifyTarget,
        copyText,
        submitCustomerSetup,
        selected,
        setSelected,
        finding,
        setFinding,
        job,
        setJob,
        openScan,
        openFinding,
        closeFinding,
        moveFinding,
        findingIndex,
        findings,
        counts,
        active,
        run,
        stop,
        readiness,
    } = props;
    const current = users.find((u) => String(u.id) === String(userId));
    const currentKey = (
        productStatus?.product_key ||
        productStatus?.scan_profile ||
        readiness?.product_key ||
        readiness?.scan_profile ||
        ""
    ).toLowerCase();
    const isAdvanced = currentKey === "monthly";
    const accessState = (productStatus?.access || readiness?.access || "BLOCKED").toUpperCase();
    const organizationApproved = current?.verification_status === "approved";
    const advancedActive = isAdvanced && accessState === "ACTIVE";
    const validUntil = productStatus?.valid_until || readiness?.valid_until;
    const planState = customerPlanState({ ...readiness, ...productStatus, valid_until: validUntil });
    const planTitle = planState.title;
    const planDescription = isAdvanced
        ? "Advanced Security Check with deeper controlled web-security coverage."
        : currentKey === "free"
          ? "Quick Check access for the 7-day evaluation period."
          : "Product access is not currently active for this organization.";
    return (
        <div className="min-h-screen bg-slate-50">
            <Header productStatus={productStatus} />
            <MobileNav page={page} setPage={setPage} />
            <div className="flex min-h-[calc(100vh-70px)]">
                <Sidebar page={page} setPage={setPage} />
                <main className="workspace min-w-0 flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10">
                    <div className="mx-auto max-w-[1280px]">
                        <p className="eyebrow">SETTINGS</p>
                        <h1 className="product-title">Account & plan</h1>
                        <p className="product-subtitle">
                            Your organization is verified once. Changing plan never creates another profile.
                        </p>
                        <section className="card mt-7 p-6 sm:p-8">
                            <div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">
                                Organization
                            </div>
                            <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <h2 className="text-xl font-extrabold text-slate-950">
                                        {current?.company_name || current?.name || "No organization selected"}
                                    </h2>
                                    <p className="mt-1 text-sm text-slate-500">
                                        {current?.email || "No work email available"}
                                    </p>
                                    {current?.company_domain && (
                                        <p className="mt-1 text-xs text-slate-400">{current.company_domain}</p>
                                    )}
                                </div>
                                <span
                                    className={`pill ${organizationApproved ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}
                                >
                                    {organizationApproved
                                        ? "Verified organization"
                                        : current
                                          ? "Verification pending"
                                          : "Organization not configured"}
                                </span>
                            </div>
                            <div className="mt-5 rounded-xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
                                Your company identity, verified websites and authorization records stay with this
                                account when you upgrade. You do not register again.
                            </div>
                        </section>
                        <section className="card mt-5 p-6 sm:p-8">
                            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                                <div>
                                    <div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">
                                        PLAN & BILLING
                                    </div>
                                    <h2 className="mt-1 text-xl font-extrabold text-slate-950">{planTitle}</h2>
                                    <p className="mt-2 text-sm leading-6 text-slate-500">{planDescription}</p>
                                    {validUntil && (
                                        <p className="mt-2 text-xs font-semibold text-slate-400">
                                            {accessState === "TRIAL" ? "Trial ends" : "Current access through"}{" "}
                                            {new Date(validUntil).toLocaleDateString()}
                                        </p>
                                    )}
                                </div>
                                <div className="flex flex-col items-start gap-2 sm:items-end">
                                    <span
                                        className={`pill ${planState.tone === "active" ? "bg-emerald-50 text-emerald-700" : planState.tone === "trial" ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-600"}`}
                                    >
                                        {planState.badge}
                                    </span>
                                    {advancedActive && (
                                        <button
                                            type="button"
                                            disabled
                                            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-400"
                                        >
                                            Manage subscription · coming later
                                        </button>
                                    )}
                                </div>
                            </div>
                            {!isAdvanced && (
                                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5">
                                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                                        <div>
                                            <b className="text-base text-slate-950">Upgrade to Advanced</b>
                                            <p className="mt-1 max-w-xl text-sm leading-6 text-slate-500">
                                                Keep the same organization and authorized websites. Only your
                                                SkullHarbor product access changes.
                                            </p>
                                        </div>
                                        {devAuthority ? (
                                            <button
                                                type="button"
                                                disabled={activationBusy || !userId}
                                                onClick={() => activateDevelopmentAccess("monthly")}
                                                className="primary-action shrink-0"
                                            >
                                                {activationBusy && activationProduct === "monthly"
                                                    ? "Activating…"
                                                    : "Test Advanced upgrade"}{" "}
                                                <Icon name="arrow-right" className="h-4 w-4" />
                                            </button>
                                        ) : (
                                            <button
                                                type="button"
                                                disabled
                                                className="primary-action shrink-0 opacity-60"
                                            >
                                                Upgrade to Advanced
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                            {advancedActive && (
                                <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm leading-6 text-emerald-800">
                                    <b>Advanced is active.</b> Your existing organization verification and authorized
                                    websites were kept unchanged.
                                </div>
                            )}
                            {isAdvanced && !advancedActive && (
                                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm leading-6 text-slate-700">
                                    <b>Advanced is not active.</b> Existing organization and authorization data remain
                                    stored locally; inactive access cannot start new scans.
                                </div>
                            )}
                            <div className="mt-7 border-t border-slate-200 pt-7">
                                <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                                    <div>
                                        <div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">
                                            COMPARE ACCESS
                                        </div>
                                        <h3 className="mt-1 text-lg font-extrabold text-slate-950">
                                            Choose the coverage you need
                                        </h3>
                                    </div>
                                    <p className="max-w-md text-xs leading-5 text-slate-500">
                                        Your organization and authorized websites stay the same. Only security-check
                                        coverage changes.
                                    </p>
                                </div>
                                <div className="mt-7 grid items-stretch gap-5 lg:grid-cols-3">
                                    <MarketingPlanCard
                                        icon={ShieldCheck}
                                        title="Free Trial"
                                        eyebrow="START HERE"
                                        price="€0"
                                        priceNote="for 7 days"
                                        subtitle="Try the core Quick Check before choosing ongoing coverage."
                                        current={currentKey === "free"}
                                        features={[
                                            [true, "Common file and configuration checks"],
                                            [true, "Authorized website checks"],
                                            [true, "Local scan execution"],
                                            [false, "Deeper web-security coverage"],
                                            [false, "SQL injection checks"],
                                            [false, "Public-service exposure checks"],
                                        ]}
                                    />
                                    <MarketingPlanCard
                                        icon={Sparkles}
                                        title="Advanced"
                                        eyebrow="RECOMMENDED"
                                        price="€XX"
                                        priceNote="per month"
                                        subtitle="Broader controlled coverage for ongoing security checks."
                                        current={isAdvanced}
                                        emphasized
                                        features={[
                                            [true, "Everything in Free"],
                                            [true, "Core web security checks"],
                                            [true, "Vulnerability & exposure checks"],
                                            [true, "Public service exposure checks"],
                                            [true, "Security header & configuration checks"],
                                            [true, "Exposed file & information checks"],
                                            [true, "Injection & XSS checks"],
                                            [true, "SQL injection checks"],
                                            [true, "External services such as SSH, FTP, mail & databases"],
                                        ]}
                                    />
                                    <MarketingPlanCard
                                        icon={Building2}
                                        title="Custom / Yearly"
                                        eyebrow="MANAGED"
                                        price="Custom"
                                        priceNote="agreed scope & contract"
                                        subtitle="Managed pentest engagement tailored to your organization."
                                        features={[
                                            [true, "Agreed customer-specific scope"],
                                            [true, "Manual security testing"],
                                            [true, "Engagement authorization"],
                                            [true, "Contract-based delivery"],
                                            [false, "Self-service automated tier"],
                                            [false, "Unrestricted disruptive testing"],
                                        ]}
                                    />
                                </div>
                            </div>
                        </section>
                        <section className="card mt-5 p-6 sm:p-8">
                            <div className="text-xs font-extrabold uppercase tracking-[.12em] text-slate-400">
                                CUSTOM / YEARLY
                            </div>
                            <h2 className="mt-1 text-lg font-extrabold text-slate-950">Managed pentest engagement</h2>
                            <p className="mt-2 text-sm leading-6 text-slate-500">
                                Custom yearly work is handled separately with an agreed scope and contract. It is not an
                                unrestricted automated scanner tier.
                            </p>
                        </section>
                        {devAuthority && (
                            <details className="mt-5 rounded-[22px] border border-violet-200 bg-violet-50 p-6 sm:p-8">
                                <summary className="cursor-pointer text-sm font-extrabold text-violet-700">
                                    Development testing controls
                                </summary>
                                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
                                    Internal only. Simulate entitlement changes for this same customer. Production
                                    packaging excludes this control.
                                </p>
                                {users.length > 1 && (
                                    <label className="mt-4 block max-w-md text-xs font-bold text-violet-800">
                                        Development customer workspace
                                        <select
                                            value={userId}
                                            onChange={(e) => {
                                                setUserId(e.target.value);
                                                setTarget("");
                                                setSelected(null);
                                                setFinding(null);
                                                setJob(null);
                                                setScans([]);
                                                setTargets([]);
                                            }}
                                            className="mt-2 h-11 w-full rounded-xl border border-violet-200 bg-white px-3 text-sm font-semibold text-slate-800"
                                        >
                                            {users.map((u) => (
                                                <option key={u.id} value={u.id}>
                                                    {u.company_name || u.name} · {u.email}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                )}
                                <div className="mt-4 flex flex-wrap gap-3">
                                    <button
                                        type="button"
                                        disabled={activationBusy || !userId}
                                        onClick={() => activateDevelopmentAccess("free")}
                                        className="secondary-action"
                                    >
                                        Use FREE test access
                                    </button>
                                    <button
                                        type="button"
                                        disabled={activationBusy || !userId}
                                        onClick={() => activateDevelopmentAccess("monthly")}
                                        className="secondary-action"
                                    >
                                        Use MONTHLY test access
                                    </button>
                                </div>
                            </details>
                        )}
                        {error && (
                            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                                {error}
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}

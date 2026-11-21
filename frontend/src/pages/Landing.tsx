// Product page: what Shifttrace is, why it is different, and a one-click live demo.
import { lazy, Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, AudioLines, ChevronRight, BookOpen, Boxes, CalendarClock, Camera, CheckCircle2, ClipboardCheck, Database, Eye, Factory, FileCheck2, Gauge,
  FlaskConical, GraduationCap, History, Lightbulb, Mic, Play, Plug, ScanBarcode, ScanEye, ShieldAlert, ShieldCheck, ShoppingCart, Wallet, Workflow, Wrench,
} from "lucide-react";
import type { Asset, Handoff, SessionRow, ToolAction } from "../api";
import { useFetch, useLiveTick } from "../live";
import { useOnShift } from "../shift";
import { useStartSession } from "../start";
import { btnClass, cx } from "../ui";

/* ---------- hero: an animated product preview built from real C-204 data ---------- */
// A live-feed window of fixed height: beats arrive at the bottom, older ones scroll up and fade out at the top.
// The script loops forever (the next shift's question starts the next round), so the window is never half empty
// and the hero text beside it never moves.

type Beat = { kind: "you" | "agent" | "lookup" | "camera" | "hypo" | "approve" | "verified" | "handoff"; text: string; tag?: string };
const SCRIPT: Beat[] = [
  { kind: "you", text: "What happened to this compressor on the previous shift?" },
  { kind: "lookup", text: "Read the previous handoff H-0042", tag: "Lookup" },
  { kind: "agent", text: "Sensor TS-2 was replaced, but A-17 came back. Drive-end vibration 7.4 mm/s. Bearing suspected, not confirmed." },
  { kind: "camera", text: "Panel reads A-17 DISCH TEMP HIGH, 108 °C", tag: "Camera, unverified" },
  { kind: "hypo", text: "Drive-end bearing wear is driving the heat", tag: "AI hypothesis" },
  { kind: "you", text: "Do we have that bearing? Raise a request." },
  { kind: "approve", text: "1 × Bearing 6316-C3 for WO-1187" },
  { kind: "you", text: "Yes, submit it." },
  { kind: "verified", text: "PR-2001 submitted, re-read from the database", tag: "Verified" },
  { kind: "handoff", text: "Handoff H-0043 filed for B shift", tag: "From records" },
];
const at = (kind: Beat["kind"]) => SCRIPT.findIndex((b) => b.kind === kind);
const TONE: Record<Beat["kind"], { c: string; icon: ReactNode }> = {
  you: { c: "var(--blue)", icon: <Mic size={13} /> }, agent: { c: "var(--ink-2)", icon: <AudioLines size={13} /> },
  lookup: { c: "var(--pencil)", icon: <Database size={13} /> }, camera: { c: "var(--violet)", icon: <ScanEye size={13} /> },
  hypo: { c: "var(--ochre)", icon: <Lightbulb size={13} /> }, approve: { c: "var(--ochre)", icon: <ShoppingCart size={13} /> },
  verified: { c: "var(--green)", icon: <CheckCircle2 size={13} /> }, handoff: { c: "var(--teal)", icon: <FileCheck2 size={13} /> },
};
const T0 = 14 * 3600 + 32 * 60 + 8;
const clock = (i: number) => {
  const s = T0 + i * 6;
  return [Math.floor(s / 3600) % 24, Math.floor(s / 60) % 60, s % 60].map((x) => String(x).padStart(2, "0")).join(":");
};
const WINDOW = 7; // beats kept in the DOM; the fixed-height frame shows the newest ~5

function HeroPreview() {
  const reduce = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // k = beats played so far. It only grows, so React keys stay unique and only the newest beat animates in.
  const [k, setK] = useState(reduce ? at("verified") + 1 : 5);
  useEffect(() => {
    if (reduce) return;
    const last = SCRIPT[(k - 1) % SCRIPT.length].kind;
    const t = window.setTimeout(() => setK((x) => x + 1), last === "handoff" ? 3400 : last === "approve" ? 2200 : 1600);
    return () => window.clearTimeout(t);
  }, [k, reduce]);
  const shown = Math.min(k, WINDOW);
  const items = Array.from({ length: shown }, (_, j) => k - shown + j);
  const pos = (k - 1) % SCRIPT.length; // where the current round is
  const next = SCRIPT[k % SCRIPT.length].kind;
  const waiting = pos === at("approve");
  const state = waiting ? "Waiting for your yes" : next === "you" ? "Listening…" : next === "agent" ? "Speaking" : "Working…";
  const handoff = [
    { mark: "◆", c: "text-ochre", text: "Coupling alignment not checked", show: true },
    { mark: "◆", c: "text-ochre", text: "Vibration before or after the warning?", show: true },
    { mark: "◇", c: "text-violet", text: "A-17, 108 °C seen on camera", show: pos >= at("camera") },
    { mark: "✓", c: "text-green", text: "PR-2001 ordered, due Mon", show: pos >= at("verified") },
  ];
  return (
    <div className="surface overflow-hidden text-left rounded-2xl" aria-label="Product preview: a live session on compressor C-204">
      <div className="flex items-center gap-3 px-4 h-10 border-b border-rule bg-paper/60">
        <span className="inline-flex items-center gap-2 text-[12px] font-semibold text-red"><span className="w-2 h-2 rounded-full bg-red now-dot" />Live</span>
        <span className="label !tracking-[0.08em] truncate">C-204<span className="hidden sm:inline"> / Troubleshoot a fault</span></span>
        <span className="ml-auto font-mono text-[11px] text-pencil">S-1002</span>
      </div>
      <div className="grid md:grid-cols-[minmax(0,1fr)_200px]">
        <div className="relative h-[332px] overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,black_56px)]">
          <span aria-hidden className="absolute left-[85px] top-0 bottom-0 w-px bg-rule-strong" />
          <ol className="absolute inset-x-0 bottom-0 px-4 pb-3 flex flex-col">
            {items.map((i) => {
              const b = SCRIPT[i % SCRIPT.length];
              return (
                <li key={i} className="feed-in grid grid-cols-[52px_28px_minmax(0,1fr)] gap-x-2 items-start py-[5px]">
                  <span className="font-mono text-[10.5px] text-pencil pt-[7px]">{clock(i)}</span>
                  <span className="relative z-[1] w-7 h-7 rounded-full border-2 bg-sheet flex items-center justify-center" style={{ borderColor: TONE[b.kind].c, color: TONE[b.kind].c }}>{TONE[b.kind].icon}</span>
                  {b.kind === "approve" ? (
                    <div className={cx("rounded-lg border px-2.5 py-1.5 transition-colors duration-500", waiting && i === k - 1 ? "border-ochre bg-ochre-wash approve-pulse" : "border-ochre/50 bg-ochre-wash/60")}>
                      <div className="text-[10.5px] font-semibold text-ochre">Approval required · awaiting your yes</div>
                      <div className="text-[12.5px] font-semibold leading-snug">{b.text}</div>
                    </div>
                  ) : (
                    <p className={cx("min-w-0 pt-[5px] text-[12.5px] leading-snug", b.kind === "you" && "text-blue", b.kind === "verified" && "text-green font-semibold", b.kind === "handoff" && "text-teal font-semibold")}>
                      {b.kind === "you" ? `“${b.text}”` : b.text}
                      {b.tag && <span className="ml-1.5 align-[1px] whitespace-nowrap text-[9.5px] font-semibold px-1.5 py-[1px] rounded border" style={{ color: TONE[b.kind].c, borderColor: `color-mix(in oklab, ${TONE[b.kind].c} 45%, transparent)` }}>{b.tag}</span>}
                    </p>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
        <div className="hidden md:flex flex-col gap-3 border-l border-rule p-3 bg-paper/40">
          <div className="relative">
            <img src="/api/testkit/media/panel_alarm.png" alt="Simulated KS-75 panel showing the A-17 alarm" className="rounded border border-rule" />
            <span aria-hidden className={cx("absolute inset-0 rounded ring-2 ring-violet transition-opacity duration-500", pos === at("camera") ? "opacity-100" : "opacity-0")} />
          </div>
          <div>
            <div className="text-[12px] font-semibold">Handoff so far</div>
            <ul className="mt-1.5 grid gap-1 text-[11px] leading-snug text-ink-2">
              {handoff.filter((h) => h.show).map((h) => (
                <li key={h.text} className="feed-in flex gap-1.5"><span className={h.c}>{h.mark}</span>{h.text}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3 px-4 h-12 border-t border-rule bg-paper/60">
        <span className={cx("flex items-end gap-[3px] h-5", state === "Speaking" && "speaking")}>
          {Array.from({ length: 18 }, (_, i) => <span key={i} className="wave-bar w-[3px] rounded-full bg-teal" style={{ height: `${5 + Math.round(13 * Math.abs(Math.sin(i * 1.3)))}px`, animationDelay: `${(i % 6) * 0.08}s` }} />)}
        </span>
        <span className={cx("text-[12.5px] font-semibold", waiting && "text-ochre")}>{state}</span>
        <span className="ml-auto w-9 h-9 rounded-full border-2 border-teal text-teal flex items-center justify-center"><Mic size={16} /></span>
      </div>
    </div>
  );
}

/* ---------- 3D: the product on a plant floor (three.js, loaded only when scrolled near) ---------- */

const Floor3D = lazy(() => import("./Floor3D"));

function FloorEmbed() {
  const ref = useRef<HTMLDivElement>(null);
  const [near, setNear] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || near) return;
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) setNear(true); }, { rootMargin: "400px" });
    io.observe(el);
    return () => io.disconnect();
  }, [near]);
  return (
    <div ref={ref} className="surface overflow-hidden rounded-2xl h-[520px] sm:h-[620px]">
      {near ? <Suspense fallback={<div className="h-full grid place-items-center text-pencil">Loading the 3D view…</div>}><Floor3D className="h-full" backHref={null} /></Suspense>
        : <div className="h-full grid place-items-center text-pencil">3D view</div>}
    </div>
  );
}

/* ---------- page ---------- */

function Section({ id, eyebrow, title, sub, children, className }: { id?: string; eyebrow?: string; title: ReactNode; sub?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section id={id} className={cx("px-5 py-20 sm:py-24", className)}>
      <div className="max-w-[1180px] mx-auto">
        <div className="max-w-[720px]">
          {eyebrow && <div className="label !text-teal mb-4 flex items-center gap-3"><span className="w-8 h-px bg-teal" aria-hidden />{eyebrow}</div>}
          <h2 className="text-[34px] sm:text-[48px] leading-[1.02] font-semibold tracking-[-0.035em]">{title}</h2>
          {sub && <p className="mt-4 text-[17px] text-ink-2 leading-relaxed">{sub}</p>}
        </div>
        <div className="mt-12">{children}</div>
      </div>
    </section>
  );
}

function Feature({ icon, title, children, demo, className }: { icon: ReactNode; title: string; children: ReactNode; demo?: ReactNode; className?: string }) {
  return (
    <div className={cx("card p-6 flex flex-col gap-4", className)}>
      <span className="w-10 h-10 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center">{icon}</span>
      <div><h3 className="text-[18px] font-semibold tracking-[-0.01em]">{title}</h3><p className="mt-1.5 text-[15px] text-ink-2 leading-relaxed">{children}</p></div>
      {demo && <div className="mt-auto">{demo}</div>}
    </div>
  );
}

const Yes = () => <CheckCircle2 size={18} className="text-green mx-auto" aria-label="Yes" />;
const No = () => <span className="block text-center text-pencil" aria-label="No">—</span>;
const Part = () => <span className="block text-center text-[13px] text-ochre">partly</span>;

export default function Landing() {
  const me = useOnShift();
  const { start, busy, err } = useStartSession();
  const tick = useLiveTick(["tool", "session", "handoff", "state"]);
  const { data: assets } = useFetch<Asset[]>("/api/assets", [tick]);
  const { data: tools } = useFetch<ToolAction[]>("/api/tool-actions?limit=1000", [tick]);
  const { data: sessions } = useFetch<SessionRow[]>("/api/sessions", [tick]);
  const { data: handoffs } = useFetch<Handoff[]>("/api/handoffs", [tick]);
  const { data: costData } = useFetch<{ projection: { per_active_minute_usd: number; per_shift_usd: number; always_on_8h_shift_usd: number; assumptions: string } }>("/api/costs", []);
  const cost = costData?.projection;
  const demo = useMemo(() => assets?.find((a) => a.status === "DEGRADED") ?? assets?.[0], [assets]);
  const stats = useMemo(() => {
    const verified = (tools ?? []).filter((t) => (t.result as { verified?: boolean } | null)?.verified === true).length;
    const voice = (tools ?? []).filter((t) => t.caller === "agora_mcp").length;
    const open = (assets ?? []).reduce((n, a) => n + (a.open_loops ?? 0), 0);
    return [
      { v: sessions?.length ?? 0, l: "sessions recorded" },
      { v: voice, l: "tool calls made by the voice agent" },
      { v: verified, l: "changes verified by re-reading the database" },
      { v: handoffs?.length ?? 0, l: "handoffs written from records" },
      { v: open, l: "open questions carried across shifts" },
    ];
  }, [tools, sessions, handoffs, assets]);
  const tryIt = (assetId?: string, task?: string) => assetId && start(assetId, me.technician, me.shift, true, task, true);

  return (
    <div className="min-h-full bg-paper text-ink overflow-x-hidden">
      {/* nav */}
      <header className="sticky top-0 z-40 border-b border-rule/70 bg-paper/75 backdrop-blur">
        <div className="max-w-[1240px] mx-auto px-5 h-[72px] flex items-center gap-6">
          <Link to="/" className="flex items-center"><Wordmark /></Link>
          <nav className="hidden lg:flex items-center gap-7 mx-auto text-[14px] text-ink-2">
            <a href="#floor" className="hover:text-ink">On the floor</a><a href="#how" className="hover:text-ink">How it works</a><a href="#jobs" className="hover:text-ink">Use cases</a><a href="#proof" className="hover:text-ink">Why trust it</a>
            <a href="#connected" className="hover:text-ink">Integrations</a><a href="#cost" className="hover:text-ink">Cost</a><a href="#compare" className="hover:text-ink">Compare</a>
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <Link to="/board" className={btnClass("quiet", "sm", "hidden sm:inline-flex")}>Open console</Link>
            <button onClick={() => tryIt(demo?.asset_id)} disabled={busy || !demo} className={btnClass("primary", "sm", "!h-10 !px-4")}><Play size={15} />{busy ? "Starting…" : <><span className="sm:hidden">Try it</span><span className="hidden sm:inline">Try the live demo</span></>}</button>
          </div>
        </div>
      </header>

      {/* hero */}
      <section className="relative px-5 pt-14 sm:pt-24 pb-20">
        <div className="relative max-w-[1240px] mx-auto grid lg:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)] gap-12 items-center">
          <div>
            <div className="label !text-teal flex items-center gap-3"><span className="w-8 h-px bg-teal" aria-hidden />Voice AI at work / Agora + Murf Falcon</div>
            <h1 className="display mt-7 text-[52px] sm:text-[76px] lg:text-[68px] xl:text-[82px]">
              <span className="block whitespace-nowrap">Every shift</span><span className="block whitespace-nowrap">hands over.</span>
              <span className="block whitespace-nowrap"><span className="text-teal">Nothing</span> gets lost.</span>
            </h1>
            <p className="mt-8 text-[18px] text-ink-2 leading-relaxed max-w-[52ch]">
              A hands-free voice and camera copilot for maintenance technicians. It recalls what the last shift saw and ruled out, reads the panel,
              orders parts only after your spoken yes, and writes a handoff where every line traces back to a record.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <button onClick={() => tryIt(demo?.asset_id)} disabled={busy || !demo} className={btnClass("primary", "lg", "!h-[52px] !px-6 !rounded-[10px]")}>
                <Play size={18} />{busy ? "Starting the agent…" : "Try the live demo"}
              </button>
              <Link to="/board" className="h-[52px] px-4 rounded-[10px] text-[16px] font-medium inline-flex items-center gap-2 text-ink hover:bg-ink/5">Open the console <ChevronRight size={17} /></Link>
              <a href="#floor" className="h-[52px] px-2 text-[16px] font-medium inline-flex items-center gap-2 text-ink-2 hover:text-ink">See it on the floor</a>
            </div>
            <p className="mt-3 text-[13px] text-pencil">No machine needed: the demo shows recorded panels and lets you play recorded questions, or just talk.</p>
            {err && <p role="alert" className="mt-2 text-[14px] text-red">Could not start: {err}</p>}
          </div>
          <HeroPreview />
        </div>
      </section>

      {/* stack strip */}
      <div className="border-y border-rule">
        <div className="max-w-[1240px] mx-auto px-5 py-5 flex flex-wrap items-center justify-center gap-x-10 gap-y-3 text-[14px] text-ink-2">
          <span className="label">Real, not mocked</span>
          <span className="inline-flex items-center gap-2"><AudioLines size={16} />Agora Conversational AI</span>
          <span className="inline-flex items-center gap-2"><Mic size={16} />Murf Falcon voice</span>
          <span className="inline-flex items-center gap-2"><Eye size={16} />Vision on the live camera</span>
          <span className="inline-flex items-center gap-2"><Workflow size={16} />22 tools over MCP</span>
          <span className="inline-flex items-center gap-2"><Database size={16} />Every write re-read</span>
        </div>
      </div>

      <Section id="floor" eyebrow="On the floor" title="One worker, one machine, one voice session."
        sub="A worker in a headset walks up to a compressor that is running hot. Shifttrace recalls the last shift, checks the panel through the camera, drafts a part order that only goes through on a spoken yes, and hands the shift over to the team's tools. Drag to look around.">
        <FloorEmbed />
        <p className="mt-3 text-[13px] text-pencil">Illustration with synthetic data. <a href="/floor" className="text-ink-2 hover:text-ink underline underline-offset-4">Open full screen</a></p>
      </Section>

      {/* problem + how */}
      <Section id="how" eyebrow="How it works" title="The maintenance system remembers tickets. Shifttrace remembers what actually happened."
        sub="At shift change, what a technician saw, tried and ruled out lives in their head or a WhatsApp thread. Shifttrace captures it while they work, hands-free, and gives it to the next shift.">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { n: "01", icon: <History size={20} />, t: "Pick up where they left off", d: "“What happened on the last shift?” The agent reads the previous handoff and what is still open." },
            { n: "02", icon: <Camera size={20} />, t: "Show it the panel", d: "Point the camera. Readings are checked against the machine's limits in code, never guessed by the model." },
            { n: "03", icon: <ShieldCheck size={20} />, t: "Act, with your yes", d: "Check stock, draft an order, update the work order. Nothing is ordered until you say yes after the read-back." },
            { n: "04", icon: <ClipboardCheck size={20} />, t: "Hand over with proof", d: "A handoff written only from stored records, read aloud to the next technician." },
          ].map((s) => (
            <div key={s.n} className="card p-6">
              <div className="flex items-center justify-between"><span className="w-10 h-10 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center">{s.icon}</span><span className="font-mono text-[13px] text-pencil">{s.n}</span></div>
              <h3 className="mt-5 text-[18px] font-semibold tracking-[-0.01em]">{s.t}</h3>
              <p className="mt-1.5 text-[15px] text-ink-2 leading-relaxed">{s.d}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* track coverage */}
      <Section id="jobs" eyebrow="One engine, every frontline job" title="Not one use case. Every shift-based workplace."
        sub="Each job is a data pack (machines or zones, manuals and SOPs, limits, history) plus a task (goal, steps, allowed tools). Same voice, same proof, same spoken-yes rule.">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { icon: <Wrench size={20} />, t: "Field technician copilot", d: "Recalls the last shift, reads the panel, checks the manual, orders the bearing after your yes, updates the work order.", asset: "C-204", task: "troubleshoot", tools: "history · manual · stock · order · work order" },
            { icon: <Factory size={20} />, t: "Factory floor assistant", d: "Walks the conveyor's PM checklist step by step, refuses to skip lockout, reserves consumables, logs each step.", asset: "CV-310", task: "preventive_maintenance", tools: "checklist · readings · reserve · notes" },
            { icon: <Boxes size={20} />, t: "Warehouse and logistics", d: "Stock by location, a delayed inbound tracked, the pick face replenished from reserve after your yes, posted to the ERP.", asset: "DC2-ZB", task: "warehouse_ops", tools: "inventory · shipments · transfer · ERP" },
            { icon: <GraduationCap size={20} />, t: "Training and onboarding", d: "A spoken safety quiz from the manual. Answers are marked in code, the learning record is updated, retraining scheduled.", asset: "C-204", task: "onboarding", tools: "module · marking · learning record" },
            { icon: <Gauge size={20} />, t: "Facilities inspection round", d: "Readings by voice or camera, checked against limits in code; anything out of limit becomes a follow-up.", asset: "AHU-3", task: "inspection_round", tools: "readings · limits · follow-ups" },
            { icon: <CalendarClock size={20} />, t: "Shift handover and follow-ups", d: "The incoming shift asks what happened and what is open, answered only from records, read aloud.", asset: "CV-310", task: "shift_briefing", tools: "handoff · open items · read-only" },
          ].map((u) => (
            <div key={u.t} className="card p-6 flex flex-col">
              <span className="w-10 h-10 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center">{u.icon}</span>
              <h3 className="mt-4 text-[18px] font-semibold tracking-[-0.01em]">{u.t}</h3>
              <p className="mt-1.5 text-[15px] text-ink-2 leading-relaxed">{u.d}</p>
              <p className="mt-3 font-mono text-[12px] text-pencil">{u.tools}</p>
              <button onClick={() => tryIt(u.asset, u.task)} disabled={busy} className="mt-5 h-10 rounded-lg border border-rule-strong hover:border-teal hover:text-teal text-[14px] font-semibold inline-flex items-center justify-center gap-2"><Play size={15} />Try it live</button>
            </div>
          ))}
        </div>
      </Section>

      {/* required demo flow */}
      <Section eyebrow="The workflow, end to end" title="Initiate. Understand. Execute. Confirm. Follow up."
        sub="Every session runs the full loop through real systems, and every step leaves a record you can open in the audit log.">
        <ol className="grid md:grid-cols-5 gap-3">
          {[
            ["Initiate", "Talk hands-free. Agora Conversational AI hears you; Murf Falcon answers. The camera streams too."],
            ["Understand", "It pulls the previous handoff, open questions, the manual or SOP, stock, shipments and what the camera shows."],
            ["Execute", "22 MCP tools act on real records: orders, stock transfers, work orders, readings, learning records."],
            ["Confirm", "Critical actions wait for your spoken yes after a read-back. Failures are said plainly. Every write is re-read."],
            ["Follow up", "Handoff written from records, follow-ups scheduled, ERP posted, and the next shift briefed by voice."],
          ].map(([t, d], i) => (
            <li key={t} className="card p-5">
              <div className="font-mono text-[12px] text-teal">0{i + 1}</div>
              <div className="mt-2 text-[17px] font-semibold">{t}</div>
              <p className="mt-1.5 text-[14px] text-ink-2 leading-relaxed">{d}</p>
            </li>
          ))}
        </ol>
      </Section>

      {/* proof bento */}
      <Section id="proof" eyebrow="Why a supervisor can trust it" title="Proof, not chat." sub="Voice copilots answer questions. Shifttrace keeps a record you could hand to an auditor, and it refuses to pretend.">
        <div className="grid md:grid-cols-6 gap-4">
          <Feature className="md:col-span-3" icon={<FileCheck2 size={20} />} title="Every line has a source"
            demo={<div className="grid gap-2 text-[13px]">
              {[["var(--blue)", "Technician", "“It shook first, then the warning came on.”"], ["var(--violet)", "Camera, unverified", "Display reads A-17, 108 °C"], ["var(--ochre)", "AI hypothesis", "DE bearing wear, not confirmed"], ["var(--green)", "Verified change", "WO-1187 set to waiting for parts"]].map(([c, l, t]) => (
                <div key={l} className="flex items-center gap-3 rounded-lg border border-rule bg-paper/60 px-3 py-2"><span className="text-[11px] font-semibold px-1.5 py-0.5 rounded border shrink-0" style={{ color: c, borderColor: `color-mix(in oklab, ${c} 45%, transparent)` }}>{l}</span><span className="truncate text-ink-2">{t}</span></div>))}
            </div>}>
            What the technician said, what the camera model read, what the AI suspects and what the system changed are never mixed up. Model guesses are always marked unverified.
          </Feature>
          <Feature className="md:col-span-3" icon={<ShoppingCart size={20} />} title="Nothing is ordered without your yes"
            demo={<div className="rounded-lg border border-ochre/70 bg-ochre-wash p-4"><div className="text-[12px] font-semibold text-ochre">Approval required</div><div className="text-[15px] font-semibold mt-0.5">1 × Bearing 6316-C3 for WO-1187</div><div className="mt-2 flex items-center gap-2 text-[13px] text-ochre"><Mic size={15} />Say “yes” after the read-back</div></div>}>
            The model cannot approve its own action. An order goes out only on the technician's own transcribed words after the agent reads it back, or a click in the console.
          </Feature>
          <Feature className="md:col-span-2" icon={<Database size={20} />} title="Every change re-read">
            Each write is read back on a fresh database connection before the agent is told it worked. Only then is it shown as verified.
          </Feature>
          <Feature className="md:col-span-2" icon={<ShieldAlert size={20} />} title="It catches itself overclaiming">
            If the agent says “I've ordered it” or quotes the manual without a matching tool call, a claim check flags it and makes the agent correct itself out loud.
          </Feature>
          <Feature className="md:col-span-2" icon={<BookOpen size={20} />} title="Any machine, any task">
            Machines, manuals, limits and safety rules are data packs. Troubleshooting, preventive maintenance, inspection rounds and briefings are tasks, each with its own tool allowlist.
          </Feature>
        </div>
      </Section>

      {/* integrations + improvement loop */}
      <Section id="connected" eyebrow="Real systems, real loop" title="It acts in your systems, and it gets better every run."
        sub="Verified actions go out as signed events to the tools a site already runs. And every live run is scored, every failure logged with its root cause, fixed and pinned by a test.">
        <div className="grid md:grid-cols-2 gap-4">
          <div className="card p-6">
            <div className="flex items-center gap-2.5"><span className="w-10 h-10 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center"><Plug size={20} /></span><h3 className="text-[18px] font-semibold">Connected systems</h3></div>
            <p className="mt-2 text-[15px] text-ink-2">Orders, stock transfers, escalations, follow-ups, handoffs and out-of-limit readings become events: Slack and Teams messages, Jira or GitHub issues, calendar entries, and HMAC-signed webhooks for ERP, CMMS or Zapier, Make and n8n. Each delivery is logged and retried.</p>
            <div className="mt-4 flex flex-wrap gap-2 text-[13px]">{["Slack", "Microsoft Teams", "Jira", "GitHub Issues", "Webhooks (ERP, CMMS)", "Calendar (.ics)"].map((t) => <span key={t} className="px-2.5 py-1 rounded-full border border-rule-strong text-ink-2">{t}</span>)}</div>
            <Link to="/integrations" className="mt-5 inline-flex items-center gap-1.5 text-[14px] font-semibold text-teal hover:underline">See the event log <ArrowRight size={15} /></Link>
          </div>
          <div className="card p-6">
            <div className="flex items-center gap-2.5"><span className="w-10 h-10 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center"><FlaskConical size={20} /></span><h3 className="text-[18px] font-semibold">The improvement loop</h3></div>
            <p className="mt-2 text-[15px] text-ink-2">Recorded speech and camera scenes drive the real agent through dozens of scenarios. Each step is scored, and failures such as an invented order, a misread number or a missed camera reading are diagnosed, fixed in code or prompt, and pinned by regression tests. The dataset, runs and fixes are all visible.</p>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center">{[["Run", "live agent"], ["Fix", "root cause"], ["Pin", "regression test"]].map(([a, b]) => <div key={a} className="rounded-lg border border-rule p-2.5"><div className="text-[15px] font-semibold">{a}</div><div className="text-[12px] text-pencil">{b}</div></div>)}</div>
            <Link to="/quality" className="mt-5 inline-flex items-center gap-1.5 text-[14px] font-semibold text-teal hover:underline">See agent quality <ArrowRight size={15} /></Link>
          </div>
        </div>
      </Section>

      {/* devices + cost */}
      <Section id="cost" eyebrow="Built for the floor, priced for it" title="On the devices crews already carry. Billed only while someone is talking."
        sub="A factory does not stream video to an AI all day. Shifttrace opens a session for a job, pauses itself after silence, and keeps the camera off until it is needed.">
        <div className="grid md:grid-cols-2 gap-4">
          <div className="card p-6">
            <div className="flex items-center gap-2.5"><span className="w-10 h-10 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center"><ScanBarcode size={20} /></span><h3 className="text-[18px] font-semibold">Rugged handhelds and scanners</h3></div>
            <ul className="mt-3 grid gap-2 text-[15px] text-ink-2">
              <li>Runs in the browser on Android rugged mobile computers and wearables (for example Zebra TC and WS series); no app install.</li>
              <li>Scan a machine's QR or asset tag to open it; scan a part, bin or shipment label mid-session and the agent looks it up. Works with Zebra DataWedge keystroke output or any keyboard-wedge scanner.</li>
              <li>Push-to-talk for loud floors: hold Space, or map the device's PTT button to F9.</li>
              <li>Events feed tools such as task and messaging platforms through signed webhooks.</li>
            </ul>
          </div>
          <div className="card p-6">
            <div className="flex items-center gap-2.5"><span className="w-10 h-10 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center"><Wallet size={20} /></span><h3 className="text-[18px] font-semibold">What it costs to run</h3></div>
            {cost ? (
              <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                {[["per voice minute", `$${cost.per_active_minute_usd.toFixed(3)}`], ["per worker per shift", `$${cost.per_shift_usd.toFixed(2)}`], ["if streamed all shift", `$${cost.always_on_8h_shift_usd.toFixed(2)}`]].map(([l, v], i) => (
                  <div key={l} className="rounded-lg border border-rule p-3"><div className="text-[22px] font-semibold" style={{ color: i === 2 ? "var(--red)" : undefined }}>{v}</div><div className="text-[12px] text-pencil">{l}</div></div>))}
              </div>
            ) : null}
            <ul className="mt-4 grid gap-1.5 text-[14px] text-ink-2">
              <li>Agent exists only during a session; auto-pause after silence leaves the call, so nothing is billed.</li>
              <li>Camera on demand: most minutes are audio, which is billed lower than video.</li>
              <li>Every session shows its own measured cost; rates are set per contract.</li>
            </ul>
            <p className="mt-3 text-[12px] text-pencil">{cost?.assumptions}. Public list prices; your contract decides the bill.</p>
          </div>
        </div>
      </Section>

      {/* comparison */}
      <Section id="compare" eyebrow="Where it fits" title="Not another CMMS. Not just a chatbot."
        sub="It works alongside the maintenance system you already have. What it adds is the memory between shifts and the proof behind every action.">
        <div className="card overflow-x-auto">
          <table className="w-full text-[15px] min-w-[640px]">
            <thead><tr className="border-b border-rule text-left">
              <th className="p-4 font-medium text-pencil w-[44%]"></th>
              <th className="p-4 font-medium text-pencil text-center">CMMS or field-service app</th>
              <th className="p-4 font-medium text-pencil text-center">Voice copilot</th>
              <th className="p-4 font-semibold text-center text-teal">Shifttrace</th>
            </tr></thead>
            <tbody>
              {([
                ["Hands-free voice and live camera", <No />, <Yes />, <Yes />],
                ["Remembers what the last shift saw, tried and ruled out", <Part />, <No />, <Yes />],
                ["Every statement labelled with where it came from", <No />, <Part />, <Yes />],
                ["Orders only after the technician's spoken yes", <No />, <No />, <Yes />],
                ["Changes re-read from the database before reporting done", <Part />, <No />, <Yes />],
                ["Catches the AI claiming something it did not do", <No />, <No />, <Yes />],
                ["Handoff written from records and read aloud to the next shift", <No />, <Part />, <Yes />],
              ] as [string, ReactNode, ReactNode, ReactNode][]).map(([label, a, b, c]) => (
                <tr key={label} className="border-b border-rule last:border-0"><td className="p-4">{label}</td><td className="p-4">{a}</td><td className="p-4">{b}</td><td className="p-4 bg-teal/[0.04]">{c}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* live numbers */}
      <Section id="live" eyebrow="Live from this deployment" title="Numbers from the database, not a slide." sub="Counted from the records behind this console and updated live while a session runs: start the demo and watch them move. The plant data is synthetic; every agent call, approval and verification is real.">
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {stats.map((s) => (
            <div key={s.l} className="card p-6"><div className="text-[40px] font-semibold tracking-[-0.03em] leading-none">{s.v}</div><div className="mt-2 text-[14px] text-ink-2">{s.l}</div></div>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/audit" className={btnClass("default", "md")}>Open the audit log</Link>
          <Link to="/handoffs" className={btnClass("quiet", "md")}>Read a handoff</Link>
        </div>
      </Section>

      {/* use cases */}
      <Section eyebrow="Try a scenario" title="Four sites, live right now." sub="Each one is a data pack with its own asset, manual or SOP, limits, history and simulated status board. Start a live session on any of them.">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {(assets ?? []).filter((a) => a.metadata?.panel).map((a) => (
            <div key={a.asset_id} className="card p-6 flex flex-col" data-scenario={a.asset_id}>
              <div className="flex items-center justify-between"><span className="font-mono text-[13px] text-pencil">{a.asset_id}</span><span className={cx("text-[12px] font-semibold", a.status === "DEGRADED" ? "text-ochre" : "text-pencil")}>{a.status.toLowerCase()}</span></div>
              <h3 className="mt-2 text-[19px] font-semibold tracking-[-0.01em]">{a.name}</h3>
              <p className="mt-1 text-[14px] text-ink-2">{a.location}</p>
              <p className="mt-3 text-[14px] text-pencil">{a.open_loops ?? 0} open questions from earlier shifts</p>
              <button onClick={() => tryIt(a.asset_id)} disabled={busy} className="mt-5 h-10 rounded-lg border border-rule-strong hover:border-teal hover:text-teal text-[14px] font-semibold inline-flex items-center justify-center gap-2"><Play size={15} />Start a live session</button>
            </div>
          ))}
        </div>
      </Section>

      {/* final CTA */}
      <section className="px-5 pb-24">
        <div className="max-w-[1180px] mx-auto card glow p-10 sm:p-14 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-grid opacity-60 pointer-events-none" aria-hidden />
          <h2 className="relative text-[34px] sm:text-[44px] font-semibold tracking-[-0.03em] leading-tight">Hear it. Watch the record write itself.</h2>
          <p className="relative mt-4 text-[17px] text-ink-2 max-w-[60ch] mx-auto">Two minutes: ask about the last shift, show the panel, approve an order by voice, hand over. Then open the audit log.</p>
          <div className="relative mt-8 flex flex-wrap justify-center gap-3">
            <button onClick={() => tryIt(demo?.asset_id)} disabled={busy || !demo} className="h-12 px-6 rounded-xl bg-teal text-[#04201c] text-[16px] font-semibold hover:brightness-110 inline-flex items-center gap-2"><Play size={18} />Try the live demo</button>
            <Link to="/board" className="h-12 px-5 rounded-xl border border-rule-strong hover:bg-sheet text-[16px] inline-flex items-center gap-2">Open the console <ArrowRight size={17} /></Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-rule px-5 py-8">
        <div className="max-w-[1180px] mx-auto flex flex-wrap items-center gap-x-6 gap-y-2 text-[13px] text-pencil">
          <span className="flex items-center gap-2 text-ink-2"><Logo size={18} />Shifttrace</span>
          <span>Build with Agora, Bengaluru 2026 · PS31 Voice AI at Work</span>
          <span className="ml-auto">Machines, people and suppliers are fictional. Agora, Murf and the model calls are real.</span>
        </div>
      </footer>
    </div>
  );
}

export function Logo({ size = 26 }: { size?: number }) {
  // A hi-vis tag with the trace: the line that joins every entry of a shift.
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <rect width="32" height="32" rx="8" fill="var(--teal)" />
      <path d="M5 19h6l3-9 4 14 3-8h6" stroke="var(--on-accent)" strokeWidth="2.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Wordmark({ size = 26, sub }: { size?: number; sub?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <Logo size={size} />
      <span className="grid leading-none">
        <span className="nameplate text-[18px] font-semibold tracking-[-0.03em]">shifttrace</span>
        {sub && <span className="label !text-[9.5px] mt-1 whitespace-nowrap">Shift voice agent</span>}
      </span>
    </span>
  );
}

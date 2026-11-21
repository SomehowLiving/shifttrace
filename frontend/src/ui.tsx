import { useState, type CSSProperties, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { ChevronDown, ChevronRight } from "lucide-react";
import { hhmm, media, type Evidence, type ToolAction } from "./api";

export function cx(...c: (string | false | null | undefined)[]) { return c.filter(Boolean).join(" "); }

/* ---------- buttons and headings ---------- */

type BtnKind = "primary" | "default" | "quiet" | "danger" | "approve";
export function btnClass(kind: BtnKind = "default", size: "sm" | "md" | "lg" = "md", className?: string) {
  const k = {
    primary: "bg-accent text-on-accent border-accent hover:brightness-105 font-semibold shadow-[inset_0_1px_0_rgb(255_255_255/.25)]",
    default: "bg-raised text-ink border-rule-strong hover:border-pencil hover:bg-ink/[0.06]",
    quiet: "bg-transparent text-ink-2 border-transparent hover:text-ink hover:bg-ink/5",
    danger: "bg-transparent text-red border-red/70 hover:bg-red/5 font-semibold",
    approve: "bg-green text-paper border-green hover:opacity-90 font-semibold",
  }[kind];
  const s = { sm: "h-8 px-2.5 text-[14px]", md: "h-10 px-4 text-[15px]", lg: "h-12 px-5 text-[16px]" }[size];
  return cx("inline-flex items-center justify-center gap-2 rounded-[7px] border transition-[background-color,border-color,filter] whitespace-nowrap", s, k, className);
}
export function Btn({ children, onClick, kind = "default", size = "md", disabled, className, title, type }: {
  children: ReactNode; onClick?: () => void; kind?: BtnKind; size?: "sm" | "md" | "lg"; disabled?: boolean; className?: string; title?: string; type?: "button" | "submit";
}) {
  return <button type={type ?? "button"} title={title} aria-label={title} disabled={disabled} onClick={onClick} className={btnClass(kind, size, className)}>{children}</button>;
}

/** A section of the log: heavy rule, plain heading. No boxes. */
export function Section({ title, note, right, children, className, id }: { title: ReactNode; note?: ReactNode; right?: ReactNode; children: ReactNode; className?: string; id?: string }) {
  return (
    <section id={id} className={cx("border-t border-rule pt-4", className)}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 mb-2">
        <h2 className="text-[18px] font-semibold">{title}</h2>
        {right}
      </div>
      {note && <p className="text-[14px] text-pencil -mt-1 mb-2 max-w-[70ch]">{note}</p>}
      {children}
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="text-pencil text-[15px] py-2">{children}</p>;
}

/* ---------- state: ink colour + shape + word ---------- */

export type Tone = "alarm" | "caution" | "ok" | "info" | "model" | "quiet";
const INK: Record<Tone, string> = { alarm: "var(--red)", caution: "var(--ochre)", ok: "var(--green)", info: "var(--blue)", model: "var(--violet)", quiet: "var(--pencil)" };
const STATE: Record<string, [Tone, string]> = {
  OPEN: ["caution", "open"], IN_PROGRESS: ["info", "in progress"], WAITING_PARTS: ["caution", "waiting for parts"],
  ESCALATED: ["alarm", "escalated"], RESOLVED: ["ok", "resolved"], CLOSED: ["quiet", "closed"],
  DEGRADED: ["caution", "degraded"], RUNNING: ["quiet", "running"], STOPPED: ["alarm", "stopped"], FAULT: ["alarm", "fault"],
  ACTIVE: ["alarm", "live"], ENDED: ["quiet", "ended"],
  PENDING_APPROVAL: ["caution", "needs approval"], SUBMITTED: ["ok", "submitted"], REJECTED: ["alarm", "rejected"], CANCELLED: ["quiet", "cancelled"],
  PUBLISHED: ["quiet", "published"], RESERVED: ["ok", "reserved"], OUT: ["alarm", "out of stock"],
  ok: ["ok", "done"], error: ["alarm", "failed"], approval_required: ["caution", "needs approval"],
  open: ["caution", "open"], ruled_out: ["quiet", "ruled out"], confirmed: ["ok", "confirmed"], answered: ["ok", "answered"],
  unverified: ["model", "unverified"], verified: ["ok", "verified"],
  PENDING_CONFIRMATION: ["caution", "needs confirmation"], DONE: ["ok", "done"], FAILED: ["alarm", "failed"],
  DELAYED: ["alarm", "delayed"], IN_TRANSIT: ["info", "in transit"], LOADING: ["info", "loading"], DELIVERED: ["ok", "delivered"], PICKED_UP: ["info", "picked up"],
  PASSED: ["ok", "passed"], NEEDS_REVIEW: ["caution", "needs review"], POSTED: ["ok", "posted"],
};
export function stateOf(v: string): [Tone, string] { return STATE[v] ?? ["quiet", v.replace(/_/g, " ").toLowerCase()]; }

export function Glyph({ tone, size = 10 }: { tone: Tone; size?: number }) {
  const c = INK[tone];
  const p = { width: size, height: size, viewBox: "0 0 10 10", "aria-hidden": true } as const;
  if (tone === "alarm") return <svg {...p}><path d="M5 .6 9.7 9.3H.3Z" fill={c} /></svg>;
  if (tone === "caution") return <svg {...p}><path d="M5 .4 9.6 5 5 9.6.4 5Z" fill={c} /></svg>;
  if (tone === "ok") return <svg {...p}><path d="M1.4 5.3 4 7.8 8.8 2.2" stroke={c} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>;
  if (tone === "model") return <svg {...p}><path d="M5 1 9 5 5 9 1 5Z" fill="none" stroke={c} strokeWidth="1.6" /></svg>;
  if (tone === "info") return <svg {...p}><circle cx="5" cy="5" r="4" fill={c} /></svg>;
  return <svg {...p}><circle cx="5" cy="5" r="3.3" fill="none" stroke={c} strokeWidth="1.4" /></svg>;
}

/** A stamp: the word in ink colour with its shape, outlined like a rubber stamp. Normal states stay pencil-grey. */
export function Stamp({ value, tone: forced, label: forcedLabel, className, title }: { value?: string | null; tone?: Tone; label?: string; className?: string; title?: string }) {
  if (!value && !forced) return null;
  const [t0, l0] = value ? stateOf(value) : ["quiet" as Tone, ""];
  const tone = forced ?? t0; const label = forcedLabel ?? l0;
  return (
    <span title={title} className={cx("inline-flex items-center gap-1.5 h-6 px-2 rounded-[6px] text-[12.5px] font-medium whitespace-nowrap", className)}
      style={{ color: INK[tone], background: tone === "quiet" ? "color-mix(in oklab, var(--ink) 6%, transparent)" : `color-mix(in oklab, ${INK[tone]} 13%, transparent)`,
        boxShadow: `inset 0 0 0 1px color-mix(in oklab, ${INK[tone]} ${tone === "quiet" ? 14 : 24}%, transparent)` }}>
      <Glyph tone={tone} />{label}
    </span>
  );
}
/** Back-compat names. */
export const Status = Stamp;
export const Pill = Stamp;

export function Count({ n, tone }: { n: number; tone?: "caution" | "alarm" }) {
  const hot = n > 0 && tone;
  return <span className={cx("inline-flex items-center justify-center min-w-6 h-6 px-1.5 rounded-full text-[13px] font-bold", hot ? "" : "bg-ink/8 text-ink-2")}
    style={hot ? { background: tone === "alarm" ? "color-mix(in oklab, var(--red) 15%, transparent)" : "var(--ochre-wash)", color: tone === "alarm" ? "var(--red)" : "var(--ochre)" } : undefined}>{n}</span>;
}

/* ---------- provenance marks ---------- */

export const SOURCE: Record<string, { label: string; color: string; note: string; shape: "circle" | "diamond" | "ring" | "square" | "check" | "bar" | "triangle" }> = {
  technician: { label: "technician", color: "var(--blue)", shape: "circle", note: "What a person said or did." },
  camera_model: { label: "camera, model reading", color: "var(--violet)", shape: "diamond", note: "A vision model's reading of a camera frame. Unverified, not a diagnosis." },
  microphone_model: { label: "audio, model reading", color: "var(--violet)", shape: "diamond", note: "A model's reading of audio. Unverified." },
  agent_inference: { label: "AI hypothesis", color: "var(--ochre)", shape: "ring", note: "A possibility to check. Never a confirmed cause." },
  cmms: { label: "system record", color: "var(--ink-2)", shape: "square", note: "A record in the maintenance system." },
  tool_result: { label: "verified change", color: "var(--green)", shape: "check", note: "A change the system made, then confirmed by re-reading the database." },
  manual: { label: "service manual", color: "var(--pencil)", shape: "bar", note: "Text from the service manual." },
  claim_guard: { label: "claim check failed", color: "var(--red)", shape: "triangle", note: "The agent said something was done or looked up, but no matching tool call succeeded. It was told to correct itself." },
};

export function SourceMark({ source, size = 13 }: { source: string; size?: number }) {
  const s = SOURCE[source]; const c = s?.color ?? "var(--pencil)";
  const p = { width: size, height: size, viewBox: "0 0 12 12", "aria-hidden": true } as const;
  switch (s?.shape ?? "circle") {
    case "circle": return <svg {...p}><circle cx="6" cy="6" r="4.8" fill={c} /></svg>;
    case "diamond": return <svg {...p}><path d="M6 1 11 6 6 11 1 6Z" fill="var(--paper)" stroke={c} strokeWidth="1.8" /></svg>;
    case "ring": return <svg {...p}><circle cx="6" cy="6" r="4.4" fill="var(--paper)" stroke={c} strokeWidth="1.8" strokeDasharray="2.4 1.6" /></svg>;
    case "square": return <svg {...p}><rect x="1.6" y="1.6" width="8.8" height="8.8" rx="1" fill={c} /></svg>;
    case "check": return <svg {...p}><rect x="1" y="1" width="10" height="10" rx="2" fill={c} /><path d="M3.3 6.2 5.2 8 8.8 4" stroke="var(--paper)" strokeWidth="1.7" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>;
    case "bar": return <svg {...p}><rect x="2" y="1.5" width="8" height="9" rx="1" fill="var(--paper)" stroke={c} strokeWidth="1.5" /><path d="M4 4.5h4M4 7h4" stroke={c} strokeWidth="1.2" /></svg>;
    case "triangle": return <svg {...p}><path d="M6 .8 11.4 10.8H.6Z" fill={c} /></svg>;
  }
}

export function MarksKey() {
  return (
    <details className="text-[14px] text-pencil">
      <summary className="cursor-pointer inline-flex items-center gap-1 hover:text-ink">What the marks mean <ChevronDown size={14} /></summary>
      <ul className="mt-2 grid sm:grid-cols-2 gap-x-8 gap-y-1.5 max-w-[880px]">
        <li className="flex items-start gap-2"><span className="mt-1"><AgentMark /></span><span><span className="text-ink font-semibold">Shifttrace.</span> What the voice agent said.</span></li>
        {Object.entries(SOURCE).map(([k, v]) => <li key={k} className="flex items-start gap-2"><span className="mt-1"><SourceMark source={k} /></span><span><span className="text-ink font-semibold">{v.label[0].toUpperCase() + v.label.slice(1)}.</span> {v.note}</span></li>)}
      </ul>
    </details>
  );
}

export const AgentMark = () => <svg width="13" height="13" viewBox="0 0 12 12" aria-hidden><circle cx="6" cy="6" r="4.4" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.8" /></svg>;
export const TickMark = () => <svg width="13" height="13" viewBox="0 0 12 12" aria-hidden><path d="M2 6h8" stroke="var(--rule-strong)" strokeWidth="2" strokeLinecap="round" /></svg>;

/* ---------- the trace ---------- */

/** One line of the log: time in the margin, a mark on the trace line, the entry. */
export function TraceRow({ time, mark, children, className, sub }: { time?: ReactNode; mark?: ReactNode; children: ReactNode; className?: string; sub?: boolean }) {
  return (
    <li className={cx("grid grid-cols-[var(--time-w,64px)_32px_minmax(0,1fr)] items-start", sub ? "py-1" : "py-2", className)}>
      <span className={cx("text-right pr-1 text-pencil whitespace-nowrap", sub ? "text-[13px] pt-px" : "text-[14px] pt-0.5")}>{time}</span>
      <span className={cx("relative z-[1] flex justify-center", sub ? "pt-1" : "pt-1.5")}>{mark}</span>
      <div className="min-w-0">{children}</div>
    </li>
  );
}

/** The band that opens a shift in the log. */
export function ShiftBand({ left, title, meta, right, live }: { left?: ReactNode; title: ReactNode; meta?: ReactNode; right?: ReactNode; live?: boolean }) {
  return (
    <li className="grid grid-cols-[var(--time-w,64px)_32px_minmax(0,1fr)] items-center mt-4 first:mt-0 border-y border-rule-strong bg-sheet py-2">
      <span className="text-right pr-1 text-[13px] text-pencil whitespace-nowrap">{left}</span>
      <span className="relative z-[1] flex justify-center">
        {live ? <span className="w-3 h-3 rounded-full bg-red now-dot" /> : <span className="w-3 h-3 rounded-2xl bg-ink" />}
      </span>
      <div className="min-w-0 flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
        <span className="text-[16px] font-bold">{title}</span>
        {meta && <span className="text-[14px] text-pencil">{meta}</span>}
        {right && <span className="ml-auto pr-3">{right}</span>}
      </div>
    </li>
  );
}

export const traceStyle = (timeW = 64): CSSProperties => ({ ["--time-w" as string]: `${timeW}px`, ["--rail-x" as string]: `${timeW + 15}px` });

export function EvidenceEntry({ e, time }: { e: Evidence; time?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const loop = e.event_type === "hypothesis" || e.event_type === "open_question";
  const more = !!(e.detail || e.media_ref || e.model_id || e.verified_by);
  return (
    <TraceRow time={time ?? hhmm(e.ts)} mark={<SourceMark source={e.source_type} />} className={cx(e.status === "error" && "bg-red/5")}>
      <div className={cx("text-[16px] leading-snug [overflow-wrap:anywhere]", e.status === "ruled_out" && "line-through text-pencil")}>
        {loop && <span className="text-pencil">{e.event_type === "hypothesis" ? "Hypothesis: " : "Question: "}</span>}{e.title}
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[14px] text-pencil">
        <span title={SOURCE[e.source_type]?.note}>{SOURCE[e.source_type]?.label ?? e.source_type}</span>
        {loop && e.status && <Stamp value={e.status} />}
        {e.event_type === "visual_observation" && <Stamp value={e.verified_by ? "verified" : "unverified"} />}
        {e.status === "error" && <Stamp value="error" />}
        {more && <button onClick={() => setOpen(!open)} aria-expanded={open} className="inline-flex items-center gap-0.5 hover:text-ink">{open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}{e.media_ref ? "detail and frame" : "detail"}</button>}
        <span className="ml-auto pr-2 text-[13px]" title="Evidence ID">#{e.id}</span>
      </div>
      {open && (
        <div className="mt-2 grid gap-1.5 text-[15px] text-ink-2 border-l-2 border-rule pl-3">
          {e.detail && <p className="whitespace-pre-wrap">{e.detail}</p>}
          {e.model_id && <p className="text-[14px] text-pencil">Model: {e.model_id}</p>}
          {e.verified_by && <p className="text-[14px] text-pencil">Confirmed by {e.verified_by}</p>}
          {e.media_ref && <img src={media(e.media_ref)} alt="Camera frame at the time of the observation" className="rounded-[7px] border border-rule max-h-56 w-fit" />}
        </div>
      )}
    </TraceRow>
  );
}

export function ToolEntry({ t }: { t: ToolAction }) {
  const [open, setOpen] = useState(false);
  const d = describeTool(t);
  const [tone, label] = outcomeOf(t);
  const message = (t.result as { message?: string } | null)?.message;
  return (
    <TraceRow sub time={hhmm(t.ts)} mark={tone === "alarm" ? <Glyph tone="alarm" size={11} /> : <TickMark />}>
      <button onClick={() => setOpen(!open)} aria-expanded={open} className="text-left w-full flex flex-wrap items-center gap-x-2 gap-y-1 text-[14px] text-ink-2 hover:text-ink">
        <span>{d.action}{d.target ? <span className="text-pencil"> {d.target}</span> : null}</span>
        {tone !== "quiet" && <Stamp tone={tone} label={label} />}
      </button>
      {message && tone === "alarm" && <p className="text-[14px] text-red mt-0.5">{message}</p>}
      {open && <RawCall t={t} />}
    </TraceRow>
  );
}

export function SpeechEntry({ role, who, text, final, time }: { role: "user" | "agent" | "system"; who: string; text: string; final: boolean; time?: string }) {
  return (
    <TraceRow time={time} mark={role === "agent" ? <AgentMark /> : role === "system" ? <Glyph tone="quiet" size={11} /> : <SourceMark source="technician" />}
      className={cx(!final && "opacity-70")}>
      <div className="text-[14px] text-pencil">{role === "agent" ? "Shifttrace" : role === "system" ? "System note to the agent" : who}{!final ? ", speaking…" : ""}</div>
      <p className={cx("text-[17px] leading-snug max-w-[68ch]", role === "user" && "text-blue", role === "system" && "text-[15px] text-ink-2")}>
        {role === "user" ? `“${text}”` : text}
      </p>
    </TraceRow>
  );
}

/* ---------- tool calls in plain words ---------- */

const s = (v: unknown) => (v === undefined || v === null || v === "" ? "" : String(v));
export function describeTool(t: Pick<ToolAction, "tool_name" | "input" | "result">): { action: string; target: string } {
  const i = (t.input ?? {}) as Record<string, unknown>;
  const r = (t.result ?? {}) as Record<string, unknown>;
  switch (t.tool_name) {
    case "get_previous_handoff": return { action: "Read the previous handoff", target: s(r.handoff_id) };
    case "get_asset_history": return { action: "Read the machine history", target: s(i.asset_id) };
    case "get_open_work_orders": return { action: "Read open work orders", target: s(i.asset_id) };
    case "get_open_items": return { action: "Read open questions", target: s(i.asset_id) };
    case "search_maintenance_manual": return { action: "Searched the manual", target: s(i.query) ? `“${s(i.query)}”` : "" };
    case "check_inventory": return { action: "Checked stock", target: s(i.part) };
    case "reserve_spare_part": return { action: "Reserved a part", target: [s(i.quantity), s(i.part)].filter(Boolean).join(" × ") };
    case "create_procurement_request": return { action: "Drafted an order", target: [s(i.quantity), s(i.part)].filter(Boolean).join(" × ") };
    case "approve_procurement_request": return { action: "Sent an order after spoken approval", target: s(i.request_id ?? r.request_id) };
    case "console_approve_procurement": return { action: "Order approved in the console", target: s(i.request_id ?? r.request_id) };
    case "console_reject_procurement": return { action: "Order declined in the console", target: s(i.request_id ?? r.request_id) };
    case "update_work_order": return { action: "Updated the work order", target: [s(r.work_order_id ?? i.work_order_id), s(i.status)].filter(Boolean).join(" to ") };
    case "escalate_incident": return { action: "Escalated", target: s(i.reason) };
    case "record_observation": return { action: "Recorded an observation", target: s(i.summary) };
    case "record_reading": return { action: "Recorded a reading", target: [s(i.reading), [s(i.value), s(i.unit)].filter(Boolean).join(" ")].filter(Boolean).join(": ") };
    case "update_open_item": return { action: "Updated an open question", target: [s(i.item_id ?? i.event_id), s(i.status)].filter(Boolean).join(" to ") };
    case "create_shift_handoff": return { action: "Wrote the shift handoff", target: s(r.handoff_id) };
    case "track_shipment": return { action: "Tracked a shipment", target: s(i.reference) || "all shipments" };
    case "create_stock_transfer": return { action: "Drafted a stock transfer", target: `${s(i.quantity)} × ${s(i.part)}, ${s(i.from_location)} to ${s(i.to_location)}` };
    case "confirm_stock_transfer": return { action: "Moved stock after spoken yes", target: [s(i.transfer_id ?? r.transfer_id), s(r.erp_ref) && `ERP ${s(r.erp_ref)}`].filter(Boolean).join(", ") };
    case "console_confirm_transfer": return { action: "Stock transfer confirmed in the console", target: [s(i.transfer_id), s(r.erp_ref) && `ERP ${s(r.erp_ref)}`].filter(Boolean).join(", ") };
    case "console_cancel_transfer": return { action: "Stock transfer cancelled in the console", target: s(i.transfer_id) };
    case "schedule_follow_up": return { action: "Scheduled a follow-up", target: [s(i.title), s(r.due) && `due ${s(r.due)}`].filter(Boolean).join(", ") };
    case "get_training_module": return { action: "Started a training module", target: s(r.title) };
    case "record_training_answer": return { action: "Marked a training answer", target: [s(i.question_id), s(r.result)].filter(Boolean).join(": ") };
    case "finish_training_module": return { action: "Updated the learning record", target: r.score !== undefined ? `${s(r.title)}: ${s(r.score)}%, ${s(r.status).toLowerCase().replace("_", " ")}` : "" };
    default: return { action: t.tool_name.replace(/_/g, " "), target: "" };
  }
}

/** Tools that change state (mirror of backend tools.MUTATING plus console decisions). */
export const WRITE_TOOLS = new Set(["reserve_spare_part", "create_procurement_request", "approve_procurement_request", "update_work_order",
  "escalate_incident", "record_observation", "record_reading", "update_open_item", "create_shift_handoff", "console_approve_procurement", "console_reject_procurement",
  "create_stock_transfer", "confirm_stock_transfer", "console_confirm_transfer", "console_cancel_transfer", "schedule_follow_up", "record_training_answer", "finish_training_module"]);

export function outcomeOf(t: ToolAction): [Tone, string] {
  const r = (t.result ?? {}) as { verified?: boolean };
  if (t.status === "approval_required") return ["caution", "needs approval"];
  if (t.status !== "ok") return ["alarm", "failed"];
  if (r.verified === true) return ["ok", "verified"];
  if (WRITE_TOOLS.has(t.tool_name)) return ["info", "recorded"];
  return ["quiet", "read"];
}

export function Outcome({ t }: { t: ToolAction }) {
  const [tone, label] = outcomeOf(t);
  return <Stamp tone={tone} label={label} title={tone === "ok" ? "Confirmed by re-reading the database on a fresh connection." : undefined} />;
}

export const callerLabel = (c: string) => (c === "agora_mcp" ? "voice agent" : c === "console" ? "console" : c);

export function RawCall({ t }: { t: ToolAction }) {
  return (
    <div className="py-2 grid gap-2">
      <div className="text-[13px] text-pencil">Tool <span className="font-mono text-ink-2">{t.tool_name}</span>, call #{t.id}, by {callerLabel(t.caller)}, {t.duration_ms} ms</div>
      <pre className="font-mono text-[12px] bg-sheet border border-rule rounded-[7px] p-2 overflow-auto max-h-44 whitespace-pre-wrap">{JSON.stringify(t.input, null, 1)}</pre>
      <pre className="font-mono text-[12px] bg-sheet border border-rule rounded-[7px] p-2 overflow-auto max-h-72 whitespace-pre-wrap">{JSON.stringify(t.result, null, 1)}</pre>
    </div>
  );
}

/* ---------- page furniture ---------- */

export function PageHead({ title, sub, right, eyebrow }: { title: ReactNode; sub?: ReactNode; right?: ReactNode; eyebrow?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && <div className="label !text-teal mb-3">{eyebrow}</div>}
        <h1 className="text-[34px] sm:text-[44px] leading-[1.02] font-semibold">{title}</h1>
        {sub && <div className="text-[15.5px] text-ink-2 mt-2.5 max-w-[68ch] leading-relaxed">{sub}</div>}
      </div>
      {right && <div className="flex flex-wrap items-center gap-2">{right}</div>}
    </div>
  );
}

/** A titled part of a page, ruled like a logbook section (no card). */
export function Panel({ title, hint, right, children, className, id }: { title?: ReactNode; hint?: ReactNode; right?: ReactNode; children: ReactNode; className?: string; flush?: boolean; id?: string }) {
  if (!title) return <section id={id} className={cx("border-t border-rule", className)}>{children}</section>;
  return <Section id={id} title={title} note={hint} right={right} className={className}>{children}</Section>;
}

/** Records: the places you look things up (not where you work). One page with three tabs. */
export function RecordsTabs() {
  const tab = (to: string, label: string) => (
    <NavLink to={to} className={({ isActive }) => cx("inline-flex items-center h-10 px-3 text-[15px] border-b-2 -mb-px whitespace-nowrap", isActive ? "border-ink font-bold text-ink" : "border-transparent text-pencil hover:text-ink")}>{label}</NavLink>
  );
  return (
    <div className="grid gap-1">
      <span className="text-[13px] text-pencil">Records</span>
      <nav aria-label="Records" className="flex overflow-x-auto border-b border-rule">{tab("/audit", "Audit log")}{tab("/actions", "Orders and stock")}{tab("/handoffs", "Handoffs")}</nav>
    </div>
  );
}

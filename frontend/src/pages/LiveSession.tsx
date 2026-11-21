import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  AlertTriangle, ArrowLeft, ArrowLeftRight, AudioLines, BookOpen, Camera, CameraOff, CheckCircle2, ChevronDown, Database, Info, Lightbulb, Maximize2,
  Mic, MicOff, Pause, ScanBarcode, ScanEye, Search, Send, ShieldAlert, ShoppingCart, SwitchCamera, User, XCircle,
} from "lucide-react";
import { api, fmtDateTime, fmtTime, media, type Asset, type Evidence, type Handoff, type Health, type SessionDetail, type ToolAction, type VoiceCreds, type WorkOrder } from "../api";
import { useFetch, useLiveEvent, useLiveTick } from "../live";
import { VoiceLink, type TurnItem } from "../voice";
import { Btn, Empty, Glyph, RawCall, SOURCE, Stamp, WRITE_TOOLS, cx, describeTool, outcomeOf } from "../ui";
import { testFeed, testFeedPreferred } from "../testfeed";
import { NextLine, SceneStrip, useTestKit } from "../testkit-panel";
import { useScanner } from "../scan";
import { ScanButton } from "../scanner";

type VState = { rtc: string; agentJoined: boolean; agentState: string | null; rtm: string };
interface AssetDetail { asset: Asset; open_items: Evidence[]; work_orders: WorkOrder[]; manual_sections: { chunk_id: string; section: string; title: string }[] }
interface Limit { label: string; unit: string; normal?: [number, number]; limit_high?: number; limit_low?: number; section?: string }

function pick(obj: unknown, path: string): unknown {
  return path.split(".").reduce<unknown>((o, k) => (o && typeof o === "object" ? (o as Record<string, unknown>)[k] : undefined), obj);
}

function Pipeline({ cfg }: { cfg: unknown }) {
  if (!cfg) return <Empty>No agent configuration recorded (voice not started).</Empty>;
  const mcp = (pick(cfg, "llm.mcp_servers") as { endpoint?: string; allowed_tools?: string[] }[] | undefined)?.[0];
  const presets = String(pick(cfg, "_preset") ?? "").split(",").filter(Boolean);
  const managed = (prefix: string) => presets.find((x) => x.startsWith(prefix));
  const rows: [string, string][] = [
    ["Hears", `${pick(cfg, "asr.vendor") ?? "?"} ${pick(cfg, "asr.params.model") ?? managed("deepgram") ?? ""}${managed("deepgram") ? " (Agora managed)" : ""}`],
    ["Thinks", `${pick(cfg, "llm.params.model") ?? managed("openai") ?? "?"}${managed("openai") ? " (Agora managed)" : ""}`],
    ["Speaks", `${pick(cfg, "tts.vendor") ?? "?"} ${pick(cfg, "tts.params.model") ?? ""}, voice ${pick(cfg, "tts.params.voiceId") ?? "?"}`],
    ["Acts", mcp ? `${mcp.allowed_tools?.length ?? "all"} tools over MCP` : "no tools"],
  ];
  return <dl className="grid grid-cols-[56px_1fr] gap-x-3 gap-y-1 text-[13px]">{rows.map(([k, v]) => <Fragment key={k}><dt className="text-pencil">{k}</dt><dd className="break-all">{v}</dd></Fragment>)}</dl>;
}

function Elapsed({ since, running }: { since: string; running: boolean }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => { if (!running) return; const t = window.setInterval(() => setNow(Date.now()), 1000); return () => window.clearInterval(t); }, [running]);
  const s = Math.max(0, Math.floor((now - new Date(since).getTime()) / 1000));
  const p = (n: number) => String(n).padStart(2, "0");
  return <span className="text-[24px] font-bold tracking-[0.02em]" title="Session time">{p(Math.floor(s / 3600))}:{p(Math.floor((s % 3600) / 60))}:{p(s % 60)}</span>;
}

/* ---------- the session trace ---------- */

// Timestamps are to the second; within one second a turn usually goes: technician speaks, agent looks things up, records, replies.
const rank = (x: Entry) => x.kind === "speech" ? (x.role === "user" ? 0 : x.role === "agent" ? 3 : 4) : x.kind === "tool" ? 1 : 2;
type Entry =
  | { kind: "speech"; key: string; ts: string; role: "user" | "agent" | "system"; text: string; final: boolean }
  | { kind: "tool"; key: string; ts: string; t: ToolAction }
  | { kind: "evidence"; key: string; ts: string; e: Evidence };

const TONES: Record<string, string> = { blue: "var(--blue)", ink: "var(--ink-2)", violet: "var(--violet)", pencil: "var(--pencil)", green: "var(--green)", ochre: "var(--ochre)", teal: "var(--teal)", red: "var(--red)" };

function Node({ icon, tone }: { icon: ReactNode; tone: keyof typeof TONES }) {
  return <span className="relative z-[1] w-8 h-8 rounded-full border-2 bg-paper flex items-center justify-center" style={{ borderColor: TONES[tone], color: TONES[tone] }}>{icon}</span>;
}
function Tag({ icon, label, tone }: { icon: ReactNode; label: string; tone: keyof typeof TONES }) {
  return <span className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-[7px] border text-[12px] font-semibold whitespace-nowrap" style={{ color: TONES[tone], borderColor: `color-mix(in oklab, ${TONES[tone]} 45%, transparent)` }}>{icon}{label}</span>;
}

function Row({ time, node, tag, children, faded }: { time: string; node: ReactNode; tag?: ReactNode; children: ReactNode; faded?: boolean }) {
  return (
    <li className={cx("grid grid-cols-[52px_40px_minmax(0,1fr)_auto] gap-x-2 items-start py-2.5 border-b border-rule/60", faded && "opacity-70")}>
      <span className="text-[13px] text-pencil pt-1.5 text-right">{time}</span>
      <span className="flex justify-center">{node}</span>
      <div className="min-w-0 pt-0.5">{children}</div>
      <span className="hidden sm:block pt-0.5">{tag}</span>
    </li>
  );
}

function SpeechRow({ x, who }: { x: Extract<Entry, { kind: "speech" }>; who: string }) {
  const t = fmtTime(x.ts).slice(0, 8);
  if (x.role === "user") return (
    <Row time={t} faded={!x.final} node={<Node icon={<Mic size={15} />} tone="blue" />} tag={<Tag icon={<Mic size={13} />} label="Speech" tone="blue" />}>
      <div className="text-[13px] text-pencil">{who}{!x.final ? ", speaking…" : ""}</div>
      <p className="text-[16px] leading-snug text-blue">“{x.text}”</p>
    </Row>
  );
  if (x.role === "system") return (
    <Row time={t} node={<Node icon={<Info size={15} />} tone="pencil" />} tag={<Tag icon={<Info size={13} />} label="System note" tone="pencil" />}>
      <div className="text-[13px] text-pencil">Note from the console to the agent</div>
      <p className="text-[14px] text-ink-2">{x.text}</p>
    </Row>
  );
  return (
    <Row time={t} faded={!x.final} node={<Node icon={<AudioLines size={15} />} tone="ink" />} tag={<Tag icon={<AudioLines size={13} />} label="Agent" tone="ink" />}>
      <div className="text-[13px] text-pencil">Shifttrace{!x.final ? ", speaking…" : ""}</div>
      <p className="text-[16px] leading-snug max-w-[70ch]">{x.text}</p>
    </Row>
  );
}

function ToolRowLive({ t }: { t: ToolAction }) {
  const [open, setOpen] = useState(false);
  const d = describeTool(t); const [tone, label] = outcomeOf(t);
  const failed = tone === "alarm";
  const icon = t.tool_name === "search_maintenance_manual" ? <BookOpen size={15} /> : t.tool_name === "check_inventory" ? <Search size={15} /> : <Database size={15} />;
  return (
    <Row time={fmtTime(t.ts).slice(0, 8)} node={<Node icon={failed ? <XCircle size={15} /> : icon} tone={failed ? "red" : tone === "caution" ? "ochre" : "pencil"} />}
      tag={failed ? <Tag icon={<XCircle size={13} />} label="Failed" tone="red" /> : tone === "caution" ? <Tag icon={<AlertTriangle size={13} />} label={label} tone="ochre" /> : <Tag icon={<Database size={13} />} label="Lookup" tone="pencil" />}>
      <button onClick={() => setOpen(!open)} aria-expanded={open} className="text-left">
        <span className="text-[15px]">{d.action}</span>{d.target && <span className="text-[14px] text-pencil"> {d.target}</span>}
        <ChevronDown size={14} className={cx("inline ml-1 text-pencil transition-transform", open && "rotate-180")} />
      </button>
      {failed && (t.result as { message?: string } | null)?.message && <p className="text-[14px] text-red">{(t.result as { message?: string }).message}</p>}
      {open && <RawCall t={t} />}
    </Row>
  );
}

function EvidenceRowLive({ e }: { e: Evidence }) {
  const [open, setOpen] = useState(false);
  const src = e.source_type;
  const loop = e.event_type === "hypothesis" || e.event_type === "open_question";
  const spec: { icon: ReactNode; tone: keyof typeof TONES; label: string } =
    src === "camera_model" || src === "microphone_model" ? { icon: <ScanEye size={15} />, tone: "violet", label: e.verified_by ? "Camera, confirmed" : "Camera, unverified" }
    : src === "tool_result" ? { icon: <CheckCircle2 size={15} />, tone: "green", label: "Verified change" }
    : src === "agent_inference" ? { icon: <Lightbulb size={15} />, tone: "ochre", label: "AI hypothesis" }
    : src === "claim_guard" ? { icon: <ShieldAlert size={15} />, tone: "red", label: "Claim check failed" }
    : src === "technician" ? { icon: <User size={15} />, tone: "blue", label: "Technician" }
    : { icon: <Database size={15} />, tone: "teal", label: "System record" };
  return (
    <Row time={fmtTime(e.ts).slice(0, 8)} node={<Node icon={spec.icon} tone={spec.tone} />} tag={<Tag icon={spec.icon} label={spec.label} tone={spec.tone} />}>
      <div className="text-[13px] text-pencil">{loop ? (e.event_type === "hypothesis" ? "Hypothesis, to check" : "Open question") : e.event_type === "visual_observation" ? "Seen on camera" : SOURCE[src]?.label ?? src}</div>
      <p className={cx("text-[16px] leading-snug [overflow-wrap:anywhere]", e.status === "ruled_out" && "line-through text-pencil", src === "claim_guard" && "text-red")}>{e.title}</p>
      {e.media_ref && (
        <a href={media(e.media_ref)} target="_blank" rel="noreferrer" className="mt-2 block w-fit relative group" title="Open the camera frame">
          <img src={media(e.media_ref)} alt="Camera frame for this observation" className="h-28 rounded-[7px] border border-rule-strong" />
          <span className="absolute right-1.5 top-1.5 text-[11px] px-1.5 py-0.5 rounded-2xl bg-black/70 text-white">View</span>
        </a>
      )}
      {(loop && e.status) && <div className="mt-1"><Stamp value={e.status} /></div>}
      {(e.detail || e.model_id) && <button onClick={() => setOpen(!open)} className="mt-1 block text-[13px] text-pencil hover:text-ink">{open ? "Hide detail" : "Detail"}</button>}
      {open && <div className="mt-1 text-[14px] text-ink-2 whitespace-pre-wrap border-l-2 border-rule pl-3">{e.detail}{e.model_id && <span className="block text-[12px] text-pencil mt-1">Model: {e.model_id}</span>}</div>}
    </Row>
  );
}

/* ---------- side panels ---------- */

function MachineContext({ d, last, wo }: { d: AssetDetail | null; last?: Handoff; wo?: WorkOrder }) {
  const [tab, setTab] = useState<"overview" | "safety">("overview");
  const [chunk, setChunk] = useState<string | null>(null);
  const { data: chunkData } = useFetch<{ body: string }>(chunk ? `/api/manual/${chunk}` : null, [chunk]);
  if (!d) return <div className="p-4 text-pencil">Loading machine…</div>;
  const a = d.asset; const meta = a.metadata as Record<string, unknown>;
  const safety = (meta.safety_notes as string[] | undefined) ?? [];
  const limits = (meta.limits as Limit[] | undefined) ?? [];
  const tabBtn = (id: typeof tab, label: string) => (
    <button role="tab" aria-selected={tab === id} onClick={() => setTab(id)} className={cx("h-10 px-3 text-[14px] border-b-2 -mb-px", tab === id ? "border-teal text-ink font-bold" : "border-transparent text-pencil hover:text-ink")}>{label}</button>
  );
  return (
    <div className="grid gap-4">
      <div className="bg-sheet border border-rule rounded-xl p-4">
        <div className="flex items-start justify-between gap-2">
          <div><div className="text-[24px] font-bold leading-none">{a.asset_id}</div><div className="text-[16px] mt-1">{a.name.replace(a.asset_id, "").trim() || a.asset_type}</div></div>
          <Stamp value={a.status} />
        </div>
        <p className="text-[13px] text-pencil mt-2">{a.location}</p>
      </div>
      <div className="bg-sheet border border-rule rounded-xl">
        <div role="tablist" className="flex border-b border-rule px-2">{tabBtn("overview", "Overview")}{tabBtn("safety", "Safety and manual")}</div>
        {tab === "overview" ? (
          <div className="p-4 grid gap-4 text-[14px]">
            <dl className="grid grid-cols-[96px_1fr] gap-y-1.5">
              <dt className="text-pencil">Make</dt><dd>{a.manufacturer}</dd>
              <dt className="text-pencil">Model</dt><dd>{a.model}</dd>
              <dt className="text-pencil">Serial</dt><dd>{a.serial_no}</dd>
              {meta.running_hours ? <><dt className="text-pencil">Hours</dt><dd>{String(meta.running_hours)}</dd></> : null}
              {wo && <><dt className="text-pencil">Work order</dt><dd className="flex flex-wrap items-center gap-1.5"><b>{wo.work_order_id}</b><Stamp value={wo.status} /></dd></>}
            </dl>
            {last && (
              <div className="border-t border-rule pt-3">
                <div className="text-[13px] font-bold">Previous shift</div>
                <div className="text-[13px] text-pencil">{last.created_by}, {last.report.session.shift}, {fmtDateTime(last.created_at)}</div>
                <p className="mt-1 text-[14px] text-ink-2">{last.report.headline}</p>
                <Link to={`/handoffs/${last.handoff_id}`} target="_blank" className="text-[13px] text-blue underline">Read {last.handoff_id}</Link>
              </div>
            )}
            <div className="border-t border-rule pt-3">
              <div className="text-[13px] font-bold flex items-center gap-2" style={{ color: d.open_items.length ? "var(--ochre)" : undefined }}>Still open ({d.open_items.length})</div>
              {d.open_items.length ? <ul className="mt-1.5 grid gap-1.5">{d.open_items.map((e) => <li key={e.id} className="grid grid-cols-[14px_1fr] gap-x-2"><span className="pt-1"><Glyph tone="caution" /></span>{e.title}</li>)}</ul>
                : <p className="text-pencil mt-1">Nothing open.</p>}
            </div>
          </div>
        ) : (
          <div className="p-4 grid gap-4 text-[14px]">
            {safety.length > 0 && <div className="border-l-4 border-red pl-3"><div className="text-[13px] font-bold text-red">Safety</div><ul className="grid gap-1 mt-1">{safety.map((n, i) => <li key={i}>{n}</li>)}</ul></div>}
            {limits.length > 0 && (
              <div>
                <div className="text-[13px] font-bold mb-1">Reading limits</div>
                <dl className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1">
                  {limits.map((l, i) => <Fragment key={i}><dt className="text-pencil">{l.label}</dt><dd className="text-right">{l.normal ? `${l.normal[0]}–${l.normal[1]}` : ""}{l.limit_high !== undefined ? `, max ${l.limit_high}` : ""} {l.unit}</dd></Fragment>)}
                </dl>
              </div>
            )}
            <div>
              <div className="text-[13px] font-bold mb-1">Manual, {a.model}</div>
              <ul>{d.manual_sections.map((m) => (
                <li key={m.chunk_id}>
                  <button onClick={() => setChunk(chunk === m.chunk_id ? null : m.chunk_id)} className={cx("w-full text-left py-1 flex gap-2 hover:text-ink", chunk === m.chunk_id ? "font-bold" : "text-ink-2")}><span className="w-8 text-pencil shrink-0">{m.section}</span>{m.title}</button>
                  {chunk === m.chunk_id && chunkData && <p className="pb-2 text-[13px] text-ink-2 whitespace-pre-wrap">{chunkData.body}</p>}
                </li>))}</ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function HandoffSoFar({ s, open }: { s: SessionDetail; open: Evidence[] }) {
  const done = s.evidence.filter((e) => e.source_type === "tool_result");
  const seen = s.evidence.filter((e) => ["visual_observation", "audio_observation", "technician_statement"].includes(e.event_type));
  const failed = s.tool_actions.filter((t) => t.status === "error" && WRITE_TOOLS.has(t.tool_name));
  const pending = s.procurement.filter((p) => p.status === "PENDING_APPROVAL");
  const pendingT = (s.transfers ?? []).filter((t) => t.status === "PENDING_CONFIRMATION");
  const Group = ({ title, n, tone, children }: { title: string; n: number; tone?: string; children: ReactNode }) => (
    <div className="py-2.5 border-t border-rule first:border-0">
      <div className="text-[13px] font-bold" style={{ color: n && tone ? tone : undefined }}>{title} <span className="font-normal text-pencil">({n})</span></div>
      {n ? <ul className="mt-1 grid gap-1 text-[13px]">{children}</ul> : null}
    </div>
  );
  const li = (key: string | number, mark: ReactNode, text: string) => <li key={key} className="grid grid-cols-[14px_1fr] gap-x-2"><span className="pt-1">{mark}</span><span className="text-ink-2">{text}</span></li>;
  return (
    <div className="bg-sheet border border-rule rounded-xl p-4">
      <div className="flex items-baseline justify-between"><h2 className="text-[15px] font-bold">Handoff so far</h2><span className="text-[12px] text-pencil">fills in as you work</span></div>
      <div className="mt-1">
        <Group title="Still open" n={open.length} tone="var(--ochre)">{open.slice(0, 5).map((e) => li(e.id, <Glyph tone="caution" />, e.title))}</Group>
        <Group title="Done and verified" n={done.length} tone="var(--green)">{done.map((e) => li(e.id, <Glyph tone="ok" />, e.title))}</Group>
        <Group title="Seen and said" n={seen.length}>{seen.map((e) => li(e.id, <Glyph tone={e.source_type === "technician" ? "info" : "model"} />, e.title))}</Group>
        {(failed.length + pending.length + pendingT.length) > 0 && <Group title="Not done" n={failed.length + pending.length + pendingT.length} tone="var(--red)">
          {pending.map((p) => li(p.request_id, <Glyph tone="caution" />, `Order ${p.request_id} waiting for approval`))}
          {pendingT.map((t) => li(t.transfer_id, <Glyph tone="caution" />, `Transfer ${t.transfer_id} waiting for confirmation`))}
          {failed.map((t) => li(t.id, <Glyph tone="alarm" />, (t.result as { message?: string } | null)?.message ?? t.tool_name))}
        </Group>}
      </div>
    </div>
  );
}

/** Live level bars: your mic level while you talk, a moving wave while the agent speaks. */
function Waveform({ link, state }: { link: React.RefObject<VoiceLink | null>; state: string | null }) {
  const [lv, setLv] = useState(0);
  useEffect(() => {
    const t = window.setInterval(() => { try { setLv(link.current?.mic?.getVolumeLevel() ?? 0); } catch { setLv(0); } }, 90);
    return () => window.clearInterval(t);
  }, [link]);
  const speaking = state === "speaking";
  const color = speaking ? "var(--green)" : state === "thinking" ? "var(--ochre)" : state === "listening" ? "var(--teal)" : "var(--rule-strong)";
  return (
    <div className={cx("flex items-center gap-[3px] h-12", speaking && "speaking")} aria-hidden>
      {Array.from({ length: 34 }, (_, i) => {
        const shape = 0.35 + 0.65 * Math.abs(Math.sin(i * 0.9) * Math.cos(i * 0.37));
        const h = speaking ? shape : Math.max(0.08, Math.min(1, lv * 4 * shape + 0.06));
        return <span key={i} className="wave-bar w-[3px] rounded-full" style={{ height: `${Math.round(h * 44) + 4}px`, background: color, animationDelay: `${(i % 7) * 0.08}s` }} />;
      })}
    </div>
  );
}

export default function LiveSession() {
  const { sessionId = "" } = useParams();
  const nav = useNavigate();
  const tick = useLiveTick(["tool", "evidence", "approval", "state", "transcript", "handoff", "session"]);
  const { data: s, error } = useFetch<SessionDetail & { agent_config: unknown }>(`/api/sessions/${sessionId}`, [tick]);
  const { data: wos } = useFetch<WorkOrder[]>("/api/work-orders", [tick]);
  const { data: assetDetail } = useFetch<AssetDetail>(s ? `/api/assets/${s.asset_id}` : null, [tick, s?.asset_id]);
  const { data: handoffs } = useFetch<Handoff[]>(s ? `/api/handoffs?asset_id=${encodeURIComponent(s.asset_id)}` : null, [tick, s?.asset_id]);
  const tunnelTick = useLiveTick(["tunnel", "session"]);
  const { data: health } = useFetch<Health>("/api/health", [tunnelTick]);

  const stored = useMemo(() => {
    try { return JSON.parse(sessionStorage.getItem(`voice:${sessionId}`) ?? "null") as { voice: VoiceCreds | null; voice_error: string | null } | null; } catch { return null; }
  }, [sessionId]);
  // Tabs that started the session remember the choice; a tab that joins later uses the viewer's preference (default on).
  const feedOn = useMemo(() => { try { const v = sessionStorage.getItem(`testfeed:${sessionId}`); return v ? v === "on" : testFeedPreferred(); } catch { return testFeedPreferred(); } }, [sessionId]);
  const kit = useTestKit(s?.asset_id ?? "", s?.task_id, feedOn && !!s);
  const link = useRef<VoiceLink | null>(null);
  const camEl = useRef<HTMLDivElement>(null);
  const [vs, setVs] = useState<VState>({ rtc: "DISCONNECTED", agentJoined: false, agentState: null, rtm: "DISCONNECTED" });
  const [turns, setTurns] = useState<TurnItem[]>([]);
  const [issues, setIssues] = useState<string[]>([]);
  const [micMuted, setMicMuted] = useState(false);
  const [camOn, setCamOn] = useState(true);
  // ---- cost controls: idle pause, camera on demand, push-to-talk, live cost meter ----
  const { data: site } = useFetch<Record<string, string>>("/api/site-settings", []);
  const [paused, setPaused] = useState(false);
  const [ptt, setPtt] = useState(false);
  const [scanNote, setScanNote] = useState<string | null>(null);
  const lastActive = useRef(Date.now());
  const camTimer = useRef<number | undefined>(undefined);
  const costTick = useLiveTick(["transcript", "session", "voice"]);
  const { data: cost } = useFetch<{ total_usd: number; voice_minutes: number; camera_minutes: number; lines: { item: string; qty: number; unit: string; usd: number }[]; paused_now: boolean }>(
    `/api/sessions/${sessionId}/cost`, [costTick, Math.floor(Date.now() / 15000)]);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const traceBox = useRef<HTMLDivElement>(null);
  const stick = useRef(true);

  const isActive = s?.status === "ACTIVE";
  const [creds, setCreds] = useState<VoiceCreds | null>(stored?.voice ?? null);
  const credsFromStore = useRef(!!stored?.voice);
  const tokenRecovered = useRef(false);
  // Session numbers restart at S-1001 after a data reset, so a tab can hold voice credentials from an older session
  // with the same number (expired token, old channel). Drop them if they do not match this session's current agent.
  useEffect(() => {
    if (!s || !creds || !credsFromStore.current || !s.channel) return;
    credsFromStore.current = false;
    if (creds.channel !== s.channel) {
      setCreds(null);
      try { sessionStorage.removeItem(`voice:${sessionId}`); } catch { /* ignore */ }
      setIssues((p) => ["This tab had voice credentials from an older session with the same number. They were discarded: press Join by voice.", ...p]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [s?.channel, creds]);
  const linkChannel = useRef<string | null>(null);
  const [voiceLost, setVoiceLost] = useState<string | null>(null);
  const autoRestarted = useRef(0);
  const wasJoined = useRef(false);

  useEffect(() => {
    if (!creds || s?.status !== "ACTIVE" || linkChannel.current === creds.channel) return;
    const old = link.current;
    const l = new VoiceLink(sessionId, creds, {
      onState: setVs,
      onTurns: setTurns,
      onIssue: (m) => setIssues((p) => [m, ...p].slice(0, 5)),
    });
    link.current = l;
    linkChannel.current = creds.channel;
    wasJoined.current = false;
    (old ? old.disconnect() : Promise.resolve())
      .then(() => { if (feedOn) testFeed.install(); else testFeed.uninstall(); return l.connect({ camera: true, facingMode: "environment" }); })
      .then(() => { if (l.cam && camEl.current) l.cam.play(camEl.current, { fit: "cover", mirror: false }); })
      .catch((e) => {
        const msg = String(e?.message ?? e);
        // An expired or stale token cannot be fixed by retrying; get a fresh agent and fresh credentials once.
        if (/token|dynamic key|CAN_NOT_GET_GATEWAY_SERVER/i.test(msg) && !tokenRecovered.current) {
          tokenRecovered.current = true;
          setIssues((p) => ["The voice connection had expired. Starting a fresh voice agent…", ...p]);
          void restartVoice();
          return;
        }
        setIssues((p) => [`Could not join the Agora channel: ${msg}`, ...p]);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [creds, s?.status, sessionId]);

  // Agent left the call (Agora reported it, or it vanished from the channel for >10 s).
  useLiveEvent("voice", (d) => {
    const e = d as { session_id?: string; status?: string; message?: string };
    if (e.session_id === sessionId && e.status && !["RESTARTED", "RUNNING", "PAUSED"].includes(e.status) && !pausedRef.current) setVoiceLost(e.message || e.status);
  });
  useEffect(() => {
    if (vs.agentJoined) { wasJoined.current = true; setVoiceLost(null); return; }
    if (!wasJoined.current || vs.rtc !== "CONNECTED") return;
    const t = window.setTimeout(() => setVoiceLost("the voice agent left the channel"), 10000);
    return () => window.clearTimeout(t);
  }, [vs.agentJoined, vs.rtc]);

  const pausedRef = useRef(false);
  pausedRef.current = paused;
  const reportCam = (on: boolean) => { void api.post(`/api/sessions/${sessionId}/camera`, { on }).catch(() => undefined); };
  /** Leave the channel and stop the agent: nothing is billed while paused. The session and its record stay open. */
  const pauseVoice = async (reason: "idle" | "manual") => {
    if (pausedRef.current) return;
    setPaused(true); pausedRef.current = true; setVoiceLost(null);
    const l = link.current; link.current = null; linkChannel.current = null;
    window.clearTimeout(camTimer.current);
    await l?.disconnect();
    await api.post(`/api/sessions/${sessionId}/voice/pause`, { reason, idle_min: reason === "idle" ? Number(site?.idle_pause_min ?? 3) : null }).catch(() => undefined);
  };
  const resumeVoice = async () => { setPaused(false); pausedRef.current = false; lastActive.current = Date.now(); await restartVoice(); };
  const showCamera = async (seconds = 60) => {
    await link.current?.setCameraEnabled(true); setCamOn(true); reportCam(true);
    window.clearTimeout(camTimer.current);
    if ((site?.camera_mode ?? "always") === "on_demand" && !feedOn) {
      camTimer.current = window.setTimeout(async () => { await link.current?.setCameraEnabled(false); setCamOn(false); reportCam(false); }, seconds * 1000);
    }
  };
  const restartVoice = async () => {
    setBusy("restart");
    try {
      const r = await api.post<{ voice: VoiceCreds | null; voice_error: string | null }>(`/api/sessions/${sessionId}/voice/restart`);
      if (r.voice) {
        sessionStorage.setItem(`voice:${sessionId}`, JSON.stringify({ voice: r.voice, voice_error: null }));
        setVoiceLost(null);
        credsFromStore.current = false;
        setIssues([]);
        setCreds(r.voice);
      } else {
        setIssues((p) => [`Restart failed: ${r.voice_error}`, ...p]);
      }
    } finally { setBusy(null); }
  };
  // One automatic recovery attempt per 2 minutes; after that the button is there.
  useEffect(() => {
    if (!voiceLost || !isActive || Date.now() - autoRestarted.current < 120000) return;
    autoRestarted.current = Date.now();
    void restartVoice();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voiceLost, isActive]);

  useEffect(() => () => { const l = link.current; link.current = null; void (l ? l.disconnect() : Promise.resolve()).then(() => testFeed.uninstall()); }, []);
  // Keep the log pinned to "now" unless the reader has scrolled up to look at something.
  useEffect(() => {
    const el = traceBox.current; if (!el) return;
    const onScroll = () => { stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120; };
    el.addEventListener("scroll", onScroll); return () => el.removeEventListener("scroll", onScroll);
  });
  useEffect(() => { const el = traceBox.current; if (el && stick.current) el.scrollTop = el.scrollHeight; });
  useEffect(() => { lastActive.current = Date.now(); }, [turns]);
  // Idle pause: after N minutes with no speech from either side, stop the agent and leave the channel.
  useEffect(() => {
    const idleMs = Number(site?.idle_pause_min ?? 3) * 60000;
    if (!creds || paused || s?.status !== "ACTIVE" || !idleMs) return;
    const t = window.setInterval(() => {
      try { if ((link.current?.mic?.getVolumeLevel() ?? 0) > 0.08) lastActive.current = Date.now(); } catch { /* no mic */ }
      if (Date.now() - lastActive.current > idleMs) void pauseVoice("idle");
    }, 2000);
    return () => window.clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [creds, paused, s?.status, site?.idle_pause_min]);
  // Camera on demand: once connected, keep the camera off until the worker taps Show camera (billed as audio meanwhile).
  useEffect(() => {
    if (vs.rtc !== "CONNECTED") return;
    if ((site?.camera_mode ?? "always") === "on_demand" && !feedOn) { void link.current?.setCameraEnabled(false); setCamOn(false); reportCam(false); }
    else reportCam(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vs.rtc, site?.camera_mode]);
  // Push-to-talk (noisy floors; Zebra devices can map their PTT button to F9): mic open only while held.
  useEffect(() => {
    if (!ptt) return;
    void link.current?.setMicMuted(true); setMicMuted(true);
    const isTalkKey = (e: KeyboardEvent) => e.key === "F9" || (e.code === "Space" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName));
    const down = (e: KeyboardEvent) => { if (isTalkKey(e) && !e.repeat) { e.preventDefault(); void link.current?.setMicMuted(false); setMicMuted(false); lastActive.current = Date.now(); } };
    const up = (e: KeyboardEvent) => { if (isTalkKey(e)) { e.preventDefault(); void link.current?.setMicMuted(true); setMicMuted(true); } };
    window.addEventListener("keydown", down); window.addEventListener("keyup", up);
    return () => { window.removeEventListener("keydown", down); window.removeEventListener("keyup", up); };
  }, [ptt]);
  // Barcode / QR scans (Zebra DataWedge keystrokes or any wedge scanner) go to the agent as what the worker scanned.
  useScanner((code) => {
    lastActive.current = Date.now();
    setScanNote(`Scanned ${code}`);
    window.setTimeout(() => setScanNote(null), 6000);
    if (link.current?.ai) void link.current.sendText(`I scanned a barcode: ${code}`).catch(() => undefined);
  });

  if (error) return <div className="p-6 text-red">Could not load this session: {error}</div>;
  if (!s) return <div className="p-6 text-pencil">Opening the session…</div>;

  const wo = wos?.find((w) => w.asset_id === s.asset_id && !["CLOSED", "RESOLVED"].includes(w.status));
  const pending = s.procurement.filter((p) => p.status === "PENDING_APPROVAL");
  // One ordered log: speech (stored, with live text streaming on top), lookups, failed or pending writes, evidence.
  // Successful writes appear through the evidence they produced, so each change is listed once.
  const liveByKey = new Map(turns.filter((t) => t.text).map((t) => [t.key, t]));
  const speech: Entry[] = s.transcripts.map((t) => {
    const lv = liveByKey.get(`${t.role}-${t.turn_id}`);
    return { kind: "speech", key: `tr${t.id}`, ts: t.ts, role: t.role, text: lv?.text || t.text, final: lv ? lv.final : true };
  });
  const storedKeys = new Set(s.transcripts.map((t) => `${t.role}-${t.turn_id}`));
  const storedText = new Set(s.transcripts.map((t) => `${t.role}:${t.text}`));
  for (const t of liveByKey.values()) {
    if (storedKeys.has(t.key) || storedText.has(`${t.role}:${t.text}`)) continue;
    const ts = typeof t.time === "number" && t.time > 1e12 ? new Date(t.time).toISOString() : new Date().toISOString();
    speech.push({ kind: "speech", key: `lv${t.key}`, ts, role: t.role, text: t.text, final: t.final });
  }
  const entries: Entry[] = [
    ...speech,
    ...s.tool_actions.filter((t) => !WRITE_TOOLS.has(t.tool_name) || t.status !== "ok").map((t): Entry => ({ kind: "tool", key: `ta${t.id}`, ts: t.ts, t })),
    ...s.evidence.map((e): Entry => ({ kind: "evidence", key: `ev${e.id}`, ts: e.ts, e })),
  ].sort((x, y) => x.ts.localeCompare(y.ts) || rank(x) - rank(y) || x.key.localeCompare(y.key));
  const live = vs.rtc === "CONNECTED";

  const end = async () => {
    setBusy("end");
    await link.current?.disconnect(); link.current = null;
    await api.post(`/api/sessions/${sessionId}/end`);
    setBusy(null);
  };
  const handoff = async () => { setBusy("handoff"); try { await api.post(`/api/sessions/${sessionId}/handoff`); } finally { setBusy(null); } };
  const decide = async (id: string, approve: boolean) => {
    setBusy(id);
    try { await api.post(`/api/procurement/${id}/${approve ? "approve" : "reject"}`, { session_id: sessionId }); } finally { setBusy(null); }
  };
  const sendTyped = async () => {
    const t = typed.trim(); if (!t || !link.current) return;
    setTyped("");
    try { await link.current.sendText(t); } catch (e) { setIssues((p) => [(e as Error).message, ...p]); }
  };

  const agentState = live && (vs.agentJoined || turns.some((t) => t.role === "agent")) ? vs.agentState : null;
  const agentReady = live && (vs.agentJoined || turns.some((t) => t.role === "agent"));
  const stateLabel = paused ? "Paused" : !creds ? "Voice off" : !live ? "Connecting…" : !agentReady ? "Waiting for the agent…"
    : agentState === "listening" ? "Listening…" : agentState === "thinking" ? "Thinking…" : agentState === "speaking" ? "Speaking" : "Ready";
  const stateHint = paused ? "No cost while paused" : !creds ? "Press Join by voice above to talk" : agentState === "listening" ? "Speak naturally. You can interrupt."
    : agentState === "speaking" ? "Murf Falcon voice" : agentState === "thinking" ? "Looking things up" : agentReady ? "Ask about this machine" : "";
  const openList = assetDetail?.open_items ?? [];
  const lastHandoff = handoffs?.find((h) => h.session_id !== s.session_id);

  const finish = async () => {
    setBusy("finish");
    try {
      const r = await api.post<{ handoff_id?: string }>(`/api/sessions/${sessionId}/handoff`);
      if (isActive) { await link.current?.disconnect(); link.current = null; await api.post(`/api/sessions/${sessionId}/end`); }
      if (r?.handoff_id) nav(`/handoffs/${r.handoff_id}`);
    } catch (e) { setIssues((p) => [`Could not finish: ${(e as Error).message}`, ...p]); }
    finally { setBusy(null); }
  };
  const decideTransfer = async (id: string, confirm: boolean) => {
    setBusy(id);
    try { await api.post(`/api/transfers/${id}/${confirm ? "confirm" : "cancel"}`, { session_id: sessionId }); } finally { setBusy(null); }
  };
  const capture = async () => {
    try { await link.current?.sendText("Look at the camera now, tell me what you see, and record it as an observation."); }
    catch (e) { setIssues((p) => [(e as Error).message, ...p]); }
  };

  return (
    <div className="lg:h-screen flex flex-col bg-paper">
      {/* session bar: no site navigation here, one job */}
      <header className="border-b border-rule bg-sheet">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5">
          <Link to="/board" className="inline-flex items-center gap-1.5 text-[14px] text-pencil hover:text-ink"><ArrowLeft size={16} />Shift board</Link>
          <span className="w-px h-6 bg-rule hidden sm:block" />
          {isActive ? <span className="inline-flex items-center gap-2 text-red text-[15px] font-bold tracking-[0.04em]"><span className="w-2.5 h-2.5 rounded-full bg-red now-dot" />LIVE SESSION</span> : <Stamp value={s.status} />}
          <span className="h-8 px-2.5 inline-flex items-center rounded-[7px] bg-paper border border-rule text-[14px] font-bold">{s.session_id}</span>
          <Link to={`/machines/${s.asset_id}`} className="text-[18px] font-bold hover:underline">{assetDetail?.asset.name ?? s.asset_id}</Link>
          {s.task && (
            <details className="relative" data-testid="task-chip">
              <summary className="cursor-pointer list-none inline-flex items-center gap-1.5 rounded-[7px] border border-rule-strong px-2.5 h-8 text-[14px] font-bold">
                {s.task.label}{s.task.read_only ? <span className="font-normal text-pencil">, read and note only</span> : null}<ChevronDown size={15} />
              </summary>
              <div className="absolute z-40 mt-1 w-[min(540px,88vw)] bg-sheet border border-rule-strong rounded-xl shadow-2xl p-4 grid gap-2 text-[14px]">
                <p>{s.task.goal}</p>
                <ol className="list-decimal pl-5 grid gap-1 text-ink-2">{s.task.procedure.map((p, i) => <li key={i}>{p}</li>)}</ol>
                {s.task.restricted_tools && <p className="text-[13px] text-pencil">The agent can only use: {s.task.restricted_tools.join(", ")}.</p>}
              </div>
            </details>
          )}
          {feedOn && <span className="h-7 px-2 inline-flex items-center rounded-[7px] border border-violet/60 text-violet text-[12px] font-bold">TEST FEED</span>}
          <div className="ml-auto flex flex-wrap items-center gap-3">
            <Elapsed since={s.started_at} running={isActive} />
            {cost && (
              <details className="relative" data-testid="cost-chip">
                <summary className="cursor-pointer list-none h-8 px-2.5 inline-flex items-center gap-1.5 rounded-[7px] border border-rule-strong text-[13px]" title="Estimated running cost of this session">
                  ≈ ${cost.total_usd.toFixed(3)}{cost.paused_now && isActive ? <span className="text-pencil">, paused</span> : null}
                </summary>
                <div className="absolute right-0 z-40 mt-1 w-[340px] bg-sheet border border-rule-strong rounded-xl shadow-2xl p-4 text-[13px] grid gap-2">
                  <div className="font-bold">Estimated cost of this session</div>
                  <table className="w-full"><tbody>{cost.lines.map((l) => <tr key={l.item}><td className="py-0.5 text-ink-2">{l.item}</td><td className="text-right text-pencil">{l.qty} {l.unit}</td><td className="text-right pl-2">${l.usd.toFixed(4)}</td></tr>)}</tbody></table>
                  <p className="text-pencil">{cost.voice_minutes} voice minutes, {cost.camera_minutes} with camera. List-price estimate; the agent is billed only while voice is live, never while paused.</p>
                </div>
              </details>
            )}
            <Link to={`/audit?session=${s.session_id}`} className="text-[14px] text-blue underline">Audit log</Link>
            {isActive && <button onClick={end} disabled={busy === "end"} className="text-[14px] text-red hover:underline">End without handoff</button>}
            {isActive ? <Btn kind="primary" onClick={finish} disabled={busy === "finish"}>{busy === "finish" ? "Writing the handoff…" : "Finish and hand over"}</Btn>
              : <Btn onClick={handoff} disabled={busy === "handoff"}>{busy === "handoff" ? "Writing…" : s.handoff ? "Rewrite the handoff" : "Write the handoff"}</Btn>}
          </div>
        </div>
        <div className="px-4 pb-2 grid gap-1.5 empty:hidden">
          {isActive && voiceLost && <Notice tone="caution"><span><b>The voice agent dropped:</b> {voiceLost}. The session and its record are safe.</span><Btn kind="primary" size="sm" onClick={restartVoice} disabled={busy === "restart"}>{busy === "restart" ? "Restarting…" : "Restart voice agent"}</Btn></Notice>}
          {isActive && health && health.tunnel?.healthy === false && <Notice tone="alarm"><span><b>Agora cannot reach the maintenance tools</b> ({health.tunnel.error ?? "tunnel down"}). The agent has been told not to claim any lookup or action.</span></Notice>}
          {(stored?.voice_error || issues.length > 0) && <Notice tone="alarm"><span className="grid gap-0.5">{stored?.voice_error && <span><b>The voice agent did not start:</b> {stored.voice_error}</span>}{issues.map((m, i) => <span key={i}>{m}</span>)}</span></Notice>}
          {isActive && paused && <Notice tone="quiet"><span><b>Voice paused to save cost.</b> {Number(site?.idle_pause_min ?? 3) ? `No speech for ${site?.idle_pause_min ?? 3} minutes, so the agent was stopped and the call left.` : "Paused by you."} Nothing is billed until you resume; the session and its record stay open.</span><Btn kind="primary" size="sm" onClick={resumeVoice} disabled={busy === "restart"}>{busy === "restart" ? "Resuming…" : "Resume voice"}</Btn></Notice>}
          {isActive && !creds && !paused && <Notice tone="caution"><span><b>This tab is not connected to the voice agent.</b> Join to talk, use the camera and the test feed. This starts a fresh agent for the session; its record is kept.</span><Btn kind="primary" size="sm" onClick={restartVoice} disabled={busy === "restart"}>{busy === "restart" ? "Joining…" : "Join by voice"}</Btn></Notice>}
          {!isActive && s.handoff && <Notice tone="quiet"><span>Session ended. Handed over in <Link to={`/handoffs/${s.handoff.handoff_id}`} className="text-blue underline font-bold">{s.handoff.handoff_id}</Link>.</span></Notice>}
          {!isActive && !s.handoff && s.status === "ENDED" && <Notice tone="quiet"><span>Session ended without a handoff.</span></Notice>}
        </div>
      </header>

      <div className="flex-1 min-h-0 grid gap-4 p-4 lg:grid-cols-[290px_minmax(0,1fr)_340px] xl:grid-cols-[310px_minmax(0,1fr)_380px]">
        <div className="order-3 lg:hidden"><HandoffSoFar s={s} open={openList} /></div>
        <aside className="order-4 lg:order-none lg:overflow-y-auto min-h-0 lg:pr-1"><MachineContext d={assetDetail} last={lastHandoff} wo={wo} /></aside>

        <section className="order-2 lg:order-none min-h-0 flex flex-col bg-sheet border border-rule rounded-xl" aria-label="Session trace">
          <div className="flex items-baseline justify-between gap-3 px-4 pt-3 pb-2 border-b border-rule">
            <h2 className="text-[17px] font-bold">Session trace</h2>
            <span className="text-[13px] text-pencil">Everything said, looked up, seen and changed, in order</span>
          </div>
          <div ref={traceBox} className="flex-1 min-h-[320px] lg:overflow-y-auto px-3">
            <ol className="relative before:content-[''] before:absolute before:top-0 before:bottom-0 before:left-[79px] before:w-[2px] before:bg-rule-strong/60">
              {entries.map((x) => x.kind === "speech" ? <SpeechRow key={x.key} x={x} who={s.technician} /> : x.kind === "tool" ? <ToolRowLive key={x.key} t={x.t} /> : <EvidenceRowLive key={x.key} e={x.e} />)}
              {entries.length === 0 && <li className="py-6 pl-[96px] text-pencil">Nothing yet. {creds ? "Ask: “What happened to this machine on the last shift?”" : ""}</li>}
              {isActive && (
                <li className="grid grid-cols-[52px_40px_1fr] gap-x-2 items-center py-3">
                  <span className="text-[13px] text-red font-bold text-right">now</span>
                  <span className="flex justify-center"><span className="relative z-[1] w-3 h-3 rounded-full bg-red now-dot" /></span>
                  <span className="text-[14px] text-pencil">{stateLabel}</span>
                </li>
              )}
            </ol>
          </div>
          {pending.map((p) => (
            <div key={p.request_id} role="region" aria-label="Approval required" className="m-3 mt-0 rounded-xl border-2 border-ochre bg-ochre-wash p-4 grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)_auto] items-start">
              <ShoppingCart size={30} className="text-ochre hidden sm:block mt-1" />
              <div className="min-w-0">
                <div className="text-[15px] font-bold text-ochre">Approval required: procurement request awaiting your yes</div>
                <div className="mt-1 text-[20px] font-bold leading-snug">{p.quantity} × {p.part_name}</div>
                <dl className="mt-1.5 grid grid-cols-[80px_1fr] gap-y-0.5 text-[14px]">
                  <dt className="text-pencil">Request</dt><dd>{p.request_id}, for {p.work_order_id}</dd>
                  <dt className="text-pencil">Supplier</dt><dd>{p.supplier}</dd>
                  <dt className="text-pencil">Drafted</dt><dd>{fmtTime(p.created_at)}</dd>
                </dl>
                <p className="mt-2 text-[13px] text-ink-2"><Info size={13} className="inline mr-1" />Nothing is ordered until a person approves: say “yes” after the agent reads it back, or use the buttons.</p>
              </div>
              <div className="grid gap-2 sm:w-44">
                <div className="flex items-center gap-2 text-ochre text-[15px] font-bold"><Mic size={20} />Say “yes” to approve</div>
                <Btn kind="approve" disabled={busy === p.request_id} onClick={() => decide(p.request_id, true)}>Approve & submit</Btn>
                <Btn kind="quiet" disabled={busy === p.request_id} onClick={() => decide(p.request_id, false)}>Decline</Btn>
              </div>
            </div>
          ))}
          {(s.transfers ?? []).filter((t) => t.status === "PENDING_CONFIRMATION").map((t) => (
            <div key={t.transfer_id} role="region" aria-label="Confirmation required" className="m-3 mt-0 rounded-xl border-2 border-ochre bg-ochre-wash p-4 grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)_auto] items-start">
              <ArrowLeftRight size={30} className="text-ochre hidden sm:block mt-1" />
              <div className="min-w-0">
                <div className="text-[15px] font-bold text-ochre">Confirmation required: stock transfer awaiting your yes</div>
                <div className="mt-1 text-[20px] font-bold leading-snug">{t.quantity} × {t.part_name}</div>
                <dl className="mt-1.5 grid grid-cols-[80px_1fr] gap-y-0.5 text-[14px]">
                  <dt className="text-pencil">Transfer</dt><dd>{t.transfer_id}</dd>
                  <dt className="text-pencil">From</dt><dd>{t.from_location}</dd>
                  <dt className="text-pencil">To</dt><dd>{t.to_location}</dd>
                </dl>
                <p className="mt-2 text-[13px] text-ink-2"><Info size={13} className="inline mr-1" />Nothing moves and nothing is posted to the ERP until a person confirms: say “yes” after the read-back, or use the buttons.</p>
              </div>
              <div className="grid gap-2 sm:w-44">
                <div className="flex items-center gap-2 text-ochre text-[15px] font-bold"><Mic size={20} />Say “yes” to move it</div>
                <Btn kind="approve" disabled={busy === t.transfer_id} onClick={() => decideTransfer(t.transfer_id, true)}>Confirm & move</Btn>
                <Btn kind="quiet" disabled={busy === t.transfer_id} onClick={() => decideTransfer(t.transfer_id, false)}>Cancel</Btn>
              </div>
            </div>
          ))}
        </section>

        <aside className="order-1 lg:order-none lg:overflow-y-auto min-h-0 grid auto-rows-max gap-4 content-start lg:pl-1">
          <div className="bg-sheet border border-rule rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-3 py-2">
              <h2 className="text-[15px] font-bold">Camera</h2>
              <span className="flex items-center gap-3 text-[13px]">
                {live && camOn ? <span className="inline-flex items-center gap-1.5 text-green"><span className="w-2 h-2 rounded-full bg-green" />{feedOn ? "Test feed" : "Live"}</span> : <span className="text-pencil">{live ? "Paused" : "Off"}</span>}
                <button onClick={() => camEl.current?.requestFullscreen?.()} title="Full screen" className="text-pencil hover:text-ink"><Maximize2 size={15} /></button>
              </span>
            </div>
            <div className="relative aspect-[4/3] bg-black">
              <div ref={camEl} className="absolute inset-0" />
              {!live && <div className="absolute inset-0 flex items-center justify-center text-[#8a96a0] text-[14px] text-center px-3">{creds ? "Connecting…" : "No live camera"}</div>}
              {live && !camOn && <div className="absolute inset-0 flex items-center justify-center text-[#8a96a0] text-[14px] bg-black">Camera paused</div>}
            </div>
            {feedOn && creds && isActive && <div className="p-3 border-t border-rule"><SceneStrip t={kit} /></div>}
          </div>
          <div className="hidden lg:block"><HandoffSoFar s={s} open={openList} /></div>
          <details className="text-[13px] group px-1">
            <summary className="cursor-pointer list-none inline-flex items-center gap-1 text-pencil hover:text-ink">Voice pipeline <ChevronDown size={14} className="group-open:rotate-180 transition-transform" /></summary>
            <div className="mt-2"><Pipeline cfg={s.agent_config} /></div>
            <p className="mt-1 text-[12px] text-pencil break-all">Audio {vs.rtc.toLowerCase()}, messages {vs.rtm.toLowerCase()}{s.agent_id ? `, agent ${s.agent_id}` : ""}</p>
          </details>
        </aside>
      </div>

      {/* voice dock: always reachable */}
      {isActive && (
        <footer className="sticky bottom-0 z-30 border-t border-rule bg-sheet/95 backdrop-blur">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3 px-4 py-3">
            <div className="flex items-center gap-4 min-w-0">
              <div className="hidden md:block"><Waveform link={link} state={agentState} /></div>
              <div className="min-w-0" aria-live="polite"><div className="text-[17px] font-bold leading-tight">{stateLabel}</div><div className="text-[13px] text-pencil">{stateHint}</div></div>
            </div>
            <button onClick={async () => { await link.current?.setMicMuted(!micMuted); setMicMuted(!micMuted); }} disabled={!live}
              title={micMuted ? "Unmute microphone" : "Mute microphone"} aria-label={micMuted ? "Unmute microphone" : "Mute microphone"}
              className={cx("w-16 h-16 rounded-full border-[3px] flex items-center justify-center shrink-0 transition-colors", micMuted ? "border-red text-red bg-red/10" : "border-teal text-teal bg-teal/10 hover:bg-teal/20")}>
              {micMuted ? <MicOff size={26} /> : <Mic size={26} />}
            </button>
            <div className="flex items-center gap-2">
              {(site?.camera_mode ?? "always") === "on_demand" && !feedOn
                ? <Btn size="lg" disabled={!live || !link.current?.cam} title="Turn the camera on for 60 seconds" onClick={() => showCamera(60)}>{camOn ? <Camera size={18} /> : <CameraOff size={18} />}<span className="hidden sm:inline">{camOn ? "Camera on" : "Show camera"}</span></Btn>
                : <Btn size="lg" disabled={!live || !link.current?.cam} title={camOn ? "Pause camera" : "Resume camera"} onClick={async () => { await link.current?.setCameraEnabled(!camOn); reportCam(!camOn); setCamOn(!camOn); }}>{camOn ? <Camera size={18} /> : <CameraOff size={18} />}</Btn>}
              {!feedOn && <Btn size="lg" disabled={!live || !link.current?.cam} title="Switch camera" onClick={async () => { const lbl = await link.current?.flipCamera(); if (lbl === null) setIssues((p) => ["Only one camera available.", ...p]); }}><SwitchCamera size={18} /></Btn>}
              <Btn size="lg" disabled={!agentReady || !link.current?.ai} title="Ask the agent to record what the camera shows" onClick={capture}><ScanEye size={18} /><span className="hidden sm:inline">Capture evidence</span></Btn>
              <Btn size="lg" kind={ptt ? "primary" : "default"} disabled={!live} title="Push to talk: hold Space or F9 (map a Zebra PTT button to F9)" onClick={async () => { const on = !ptt; setPtt(on); if (!on) { await link.current?.setMicMuted(false); setMicMuted(false); } }}><span className="text-[13px]">PTT</span></Btn>
              <Btn size="lg" disabled={!live} title="Pause voice: stop the agent and leave the call; nothing is billed until you resume" onClick={() => pauseVoice("manual")}><Pause size={18} /></Btn>
              <ScanButton size="lg" />
            </div>
            {scanNote && <span className="inline-flex items-center gap-1.5 text-[13px] text-teal"><ScanBarcode size={16} />{scanNote}</span>}
            <form className="flex items-center gap-2 grow min-w-[220px] max-w-[460px]" onSubmit={(e) => { e.preventDefault(); void sendTyped(); }}>
              <input value={typed} onChange={(e) => setTyped(e.target.value)} disabled={!link.current?.ai} aria-label="Type a message to the agent"
                placeholder={link.current?.ai ? "Too noisy? Type to the agent…" : "Typing works when voice is live"} className="flex-1 min-w-0 h-12 px-3 rounded-[7px] bg-paper border border-rule-strong text-[15px] outline-none focus:border-teal" />
              <Btn size="lg" type="submit" disabled={!typed.trim() || !link.current?.ai} title="Send"><Send size={17} /></Btn>
            </form>
            {feedOn && creds && <div className="ml-auto min-w-0"><NextLine t={kit} ready={agentReady} /></div>}
          </div>
          {kit.err && <p role="alert" className="px-4 pb-2 text-[13px] text-red">{kit.err}</p>}
        </footer>
      )}
    </div>
  );
}

function Notice({ tone, children }: { tone: "alarm" | "caution" | "quiet"; children: ReactNode }) {
  return (
    <div role={tone === "quiet" ? "status" : "alert"} className={cx("rounded-[7px] border-l-4 px-3 py-1.5 text-[14px] flex flex-wrap items-center gap-3",
      tone === "alarm" ? "border-red bg-red/10" : tone === "caution" ? "border-ochre bg-ochre-wash" : "border-rule-strong bg-paper text-ink-2")}>{children}</div>
  );
}

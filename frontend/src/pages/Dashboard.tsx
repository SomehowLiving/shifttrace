import { useMemo, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Play } from "lucide-react";
import { fmtDateTime, fmtTime, type Asset, type Handoff, type Procurement, type SessionRow, type TaskList, type ToolAction, type Transfer } from "../api";
import { useFetch, useLiveTick } from "../live";
import { useOnShift } from "../shift";
import { useStartSession } from "../start";
import { Btn, Glyph, Outcome, Stamp, callerLabel, cx, describeTool } from "../ui";

const ATTENTION: Record<string, number> = { FAULT: 0, STOPPED: 0, DEGRADED: 1 };

export function useTaskLabels(): Record<string, string> {
  const { data } = useFetch<TaskList>("/api/tasks", []);
  return useMemo(() => Object.fromEntries((data?.tasks ?? []).map((t) => [t.id, t.label])), [data]);
}

/** One reading on the instrument strip. Grey while normal; colour only when it needs someone. */
function Reading({ label, value, note, tone, to }: { label: string; value: ReactNode; note?: ReactNode; tone?: "red" | "ochre" | "green"; to?: string }) {
  const body = (
    <div className={cx("card h-full px-5 pt-4 pb-5 transition-colors", to && "hover:border-rule-strong")}>
      <div className="label">{label}</div>
      <div className="mt-4 text-[44px] leading-none font-semibold tracking-[-0.05em] nameplate" style={{ color: tone ? `var(--${tone})` : undefined }}>{value}</div>
      {note && <div className="mt-2.5 text-[13px] text-pencil">{note}</div>}
    </div>
  );
  return to ? <Link to={to} className="block">{body}</Link> : body;
}

/** The one bold block on the board: the machine that most needs a person, with how it got here. */
function Priority({ a, h, onTest, busy }: { a: Asset; h?: Handoff; onTest: () => void; busy: boolean }) {
  const loops = h?.report.open_loops ?? [];
  const chain = [h && `Handoff ${h.handoff_id} from ${h.created_by}`, `${a.open_loops ?? loops.length} still open`, `${a.open_work_orders ?? 0} work order${a.open_work_orders === 1 ? "" : "s"} open`, "next shift picks up"].filter(Boolean) as string[];
  return (
    <section aria-label={`Priority: ${a.name}`} className="relative overflow-hidden rounded-2xl bg-accent text-on-accent">
      <span aria-hidden className="pointer-events-none select-none absolute -right-3 -top-6 nameplate font-bold leading-none tracking-[-0.06em] text-[150px] opacity-[0.07]">{a.asset_id}</span>
      <div className="flex items-center justify-between gap-3 px-6 h-14 border-b border-black/10">
        <span className="text-[15px] font-semibold whitespace-nowrap">Needs a person first</span>
        {h && <span className="hidden sm:inline font-mono text-[11.5px] tracking-[0.1em] uppercase opacity-70">Left open {fmtDateTime(h.created_at)}</span>}
      </div>
      <div className="relative px-6 pt-5 pb-6 grid gap-3 max-w-[760px]">
        <div className="font-mono text-[11.5px] tracking-[0.12em] uppercase opacity-70">{a.asset_id} / {a.location}</div>
        <h2 className="text-[28px] sm:text-[34px] leading-[1.05] font-semibold tracking-[-0.03em]">{h?.report.headline ?? `${a.name} is ${a.status.toLowerCase()}.`}</h2>
        {loops[0] && <p className="text-[15.5px] leading-relaxed opacity-80 max-w-[62ch]">Still open: {loops[0].text}{loops.length > 1 ? `, and ${loops.length - 1} more.` : "."}</p>}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[12px] opacity-75">
          {chain.map((c, i) => <span key={c} className="inline-flex items-center gap-2">{i > 0 && <ArrowRight size={12} aria-hidden />}<span className={i === chain.length - 1 ? "font-semibold opacity-100" : ""}>{c}</span></span>)}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <Link to={`/machines/${a.asset_id}`} className="h-11 px-5 rounded-[9px] bg-on-accent text-accent text-[15px] font-semibold inline-flex items-center gap-2 hover:opacity-90">Open {a.asset_id}</Link>
          <button onClick={onTest} disabled={busy} className="h-11 px-4 rounded-[9px] text-[15px] font-semibold inline-flex items-center gap-2 hover:bg-black/10 disabled:opacity-60"><Play size={16} />{busy ? "Starting…" : "Try it with the test feed"}</button>
        </div>
      </div>
    </section>
  );
}

export default function Dashboard() {
  const me = useOnShift();
  const tick = useLiveTick(["state", "session", "handoff", "evidence", "approval", "tool"]);
  const { data: assets } = useFetch<Asset[]>("/api/assets", [tick]);
  const { data: sessions } = useFetch<SessionRow[]>("/api/sessions", [tick]);
  const { data: handoffs } = useFetch<Handoff[]>("/api/handoffs", [tick]);
  const { data: tools } = useFetch<ToolAction[]>("/api/tool-actions?limit=500", [tick]);
  const { data: orders } = useFetch<Procurement[]>("/api/procurement", [tick]);
  const { data: transfers } = useFetch<Transfer[]>("/api/transfers", [tick]);
  const taskLabel = useTaskLabels();
  const { start, busy, err } = useStartSession();

  const byId = useMemo(() => Object.fromEntries((handoffs ?? []).map((h) => [h.handoff_id, h])), [handoffs]);
  const sorted = useMemo(() => [...(assets ?? [])].sort((a, b) =>
    (ATTENTION[a.status] ?? 9) - (ATTENTION[b.status] ?? 9) || (b.open_loops ?? 0) - (a.open_loops ?? 0) || a.asset_id.localeCompare(b.asset_id)), [assets]);
  const active = sessions?.filter((x) => x.status === "ACTIVE") ?? [];
  const attention = sorted.filter((a) => a.status in ATTENTION).length;
  const loops = sorted.reduce((n, a) => n + (a.open_loops ?? 0), 0);
  const verified = (tools ?? []).filter((t) => (t.result as { verified?: boolean } | null)?.verified === true).length;
  const pending = [...(orders ?? []).filter((o) => o.status === "PENDING_APPROVAL"), ...(transfers ?? []).filter((t) => t.status === "PENDING_CONFIRMATION")];
  const today = new Date().toLocaleDateString([], { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const top = sorted[0];
  const topHandoff = top?.latest_handoff ? byId[top.latest_handoff.handoff_id] : undefined;

  return (
    <div className="px-4 sm:px-8 py-8 lg:py-10 max-w-[1360px] mx-auto grid grid-cols-[minmax(0,1fr)] gap-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="label !text-teal">{today}, {me.shift}</div>
          <h1 className="mt-3 text-[40px] sm:text-[56px] leading-[0.95] font-semibold">Shift board</h1>
          <p className="mt-3 text-[16px] text-ink-2">{me.technician} on shift. {attention ? `${attention} of ${sorted.length} machines need attention.` : "Everything is running normally."}</p>
        </div>
        {top && !active.length && (
          <Btn kind="primary" size="lg" disabled={busy} onClick={() => start(top.asset_id, me.technician, me.shift, true, undefined, true)}><Play size={17} />{busy ? "Starting…" : `Start test session on ${top.asset_id}`}</Btn>
        )}
      </div>
      {err && <p role="alert" className="-mt-4 text-[14px] text-red">Could not start: {err}</p>}

      {active.map((a) => (
        <Link key={a.session_id} to={`/session/${a.session_id}`} className="card flex flex-wrap items-center gap-x-5 gap-y-2 px-5 h-auto py-4 !border-red/40 hover:!border-red/70">
          <span className="inline-flex items-center gap-2 text-red font-semibold"><span className="w-2 h-2 rounded-full bg-red now-dot" />Live now</span>
          <span className="text-[15px]"><b className="font-semibold">{a.technician}</b> on {a.asset_id}{a.task_id && taskLabel[a.task_id] ? `, ${taskLabel[a.task_id].toLowerCase()}` : ""}</span>
          <span className="label">started {fmtTime(a.started_at).slice(0, 5)}</span>
          <span className="ml-auto inline-flex items-center gap-1.5 text-[14px] font-semibold">Open session <ArrowRight size={16} /></span>
        </Link>
      ))}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Reading label="Live sessions" value={active.length} note={active.length ? "Agent on the call now" : "None right now"} tone={active.length ? "red" : undefined} />
        <Reading label="Need attention" value={attention} note={`of ${sorted.length} machines`} tone={attention ? "ochre" : undefined} />
        <Reading label="Open questions" value={loops} note="carried across shifts" tone={loops ? "ochre" : undefined} />
        <Reading label="Verified changes" value={verified} note={<span className="inline-flex items-center gap-1">re-read from the database <ArrowRight size={12} /></span>} to="/audit" />
      </div>

      {pending.length > 0 && (
        <Link to="/actions" className="card flex flex-wrap items-center gap-3 px-5 py-4 !border-ochre/40 hover:!border-ochre/70">
          <Glyph tone="caution" size={12} />
          <span className="text-[15px]"><b className="text-ochre font-semibold">{pending.length} {pending.length === 1 ? "action is" : "actions are"} waiting for a person's yes.</b> <span className="text-ink-2">Nothing is ordered or moved until someone confirms.</span></span>
          <span className="ml-auto inline-flex items-center gap-1.5 text-[14px] font-semibold">Review <ArrowRight size={16} /></span>
        </Link>
      )}

      <div className="grid gap-5 grid-cols-[minmax(0,1fr)] xl:grid-cols-[minmax(0,1fr)_400px] items-start">
        {top ? <Priority a={top} h={topHandoff} busy={busy} onTest={() => start(top.asset_id, me.technician, me.shift, true, undefined, true)} /> : <div />}
        <section className="card xl:row-span-2" aria-label="Live activity">
          <div className="flex items-center justify-between px-5 h-14 border-b border-rule"><h2 className="text-[16px] font-semibold">Live activity</h2><Link to="/audit" className="text-[13px] text-ink-2 hover:text-ink inline-flex items-center gap-1">Audit log <ArrowRight size={13} /></Link></div>
          <ul className="px-5 pb-2">
            {(tools ?? []).slice(0, 7).map((t) => { const d = describeTool(t); return (
              <li key={t.id} className="py-3.5 border-t border-rule first:border-0 grid grid-cols-[1fr_auto] gap-x-3">
                <span className="min-w-0"><span className="text-[14.5px] font-medium">{d.action}</span>{d.target && <span className="block text-[13px] text-ink-2 truncate">{d.target}</span>}
                  <span className="block text-[12px] text-pencil mt-0.5">{callerLabel(t.caller)}{t.session_id ? `, ${t.session_id}` : ""}</span></span>
                <span className="grid justify-items-end content-start gap-1.5"><span className="font-mono text-[11.5px] text-pencil">{fmtTime(t.ts).slice(0, 5)}</span><Outcome t={t} /></span>
              </li>); })}
            {!tools?.length && <li className="py-4 text-[14px] text-pencil">No tool calls yet. Start a session to see them here live.</li>}
          </ul>
          <div className="border-t border-rule px-5 h-12 flex items-center justify-between"><h2 className="text-[14px] font-semibold">Recent handoffs</h2><Link to="/handoffs" className="text-[13px] text-ink-2 hover:text-ink inline-flex items-center gap-1">All <ArrowRight size={13} /></Link></div>
          <ul className="px-5 pb-3">{(handoffs ?? []).slice(0, 3).map((h) => (
            <li key={h.handoff_id} className="border-t border-rule">
              <Link to={`/handoffs/${h.handoff_id}`} className="block py-3 group">
                <span className="text-[14px]"><span className="code font-semibold">{h.report.asset.asset_id}</span> <span className="text-ink-2">from {h.created_by}</span></span>
                <span className="block text-[13px] text-ink-2 line-clamp-2 group-hover:text-ink">{h.report.headline}</span>
                <span className="block text-[12px] text-pencil mt-0.5">{fmtDateTime(h.created_at)}, {h.report.open_loops.length} left open</span>
              </Link>
            </li>))}</ul>
        </section>

        <section aria-label="Machines">
          <div className="flex items-baseline justify-between mb-3 mt-3"><h2 className="text-[20px] font-semibold">Machines</h2><span className="label">Needs attention first</span></div>
          <div className="grid md:grid-cols-2 gap-3">
            {sorted.map((a) => {
              const h = a.latest_handoff ? byId[a.latest_handoff.handoff_id] : undefined;
              return (
                <article key={a.asset_id} data-asset={a.asset_id} className="card p-5 flex flex-col gap-3.5 hover:border-rule-strong transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0"><div className="label">{a.asset_id}</div>
                      <h3 className="mt-1.5 text-[19px] font-semibold leading-snug"><Link to={`/machines/${a.asset_id}`} className="hover:text-teal">{a.name}</Link></h3>
                      <div className="text-[13px] text-pencil truncate">{a.location}</div></div>
                    <Stamp value={a.status} />
                  </div>
                  {h ? (
                    <div className="grid gap-1.5">
                      <div className="text-[12px] text-pencil">Left open by {h.created_by}, {fmtDateTime(h.created_at)}</div>
                      {(h.report.open_loops.length ? h.report.open_loops.slice(0, 2) : []).map((l, i) => (
                        <div key={i} className="grid grid-cols-[14px_1fr] gap-x-2 text-[14px] text-ink-2"><span className="pt-1"><Glyph tone="caution" size={9} /></span><span className="line-clamp-2">{l.text}</span></div>
                      ))}
                      {h.report.open_loops.length > 2 && <div className="text-[12px] text-pencil pl-6">and {h.report.open_loops.length - 2} more</div>}
                      {!h.report.open_loops.length && <div className="text-[14px] text-ink-2">Nothing left open.</div>}
                    </div>
                  ) : <div className="text-[14px] text-pencil">No handover on record yet.</div>}
                  <div className="mt-auto pt-3 flex items-center gap-2 border-t border-rule">
                    <span className="text-[13px] text-pencil">{a.open_work_orders ?? 0} open work orders</span>
                    <Link to={`/machines/${a.asset_id}`} className="ml-auto h-8 px-3 rounded-[7px] border border-rule-strong text-[13.5px] font-medium inline-flex items-center gap-1.5 hover:border-teal hover:text-teal transition-colors">Open {a.asset_id}<ArrowRight size={14} /></Link>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}

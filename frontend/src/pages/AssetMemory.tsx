import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { dayLabel, fmtDateTime, hhmm, type Asset, type Evidence, type Handoff, type SessionRow, type WorkOrder } from "../api";
import { useFetch, useLiveTick } from "../live";
import { StartPanel } from "../start";
import { Empty, EvidenceEntry, Glyph, MarksKey, Section, ShiftBand, SourceMark, Stamp, TraceRow, cx, traceStyle } from "../ui";
import { useTaskLabels } from "./Dashboard";

interface AssetDetail {
  asset: Asset; work_orders: WorkOrder[]; sessions: SessionRow[]; evidence: Evidence[]; open_items: Evidence[];
  handoffs: { handoff_id: string; session_id: string; created_at: string; created_by: string }[];
  manual_sections: { chunk_id: string; section: string; title: string }[];
}

export function Crumbs({ items }: { items: { to?: string; label: string }[] }) {
  return (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-[14px] text-pencil">
      {items.map((it, i) => (
        <span key={i} className="inline-flex items-center gap-1">
          {i > 0 && <ChevronRight size={14} />}
          {it.to ? <Link to={it.to} className="hover:text-ink underline">{it.label}</Link> : <span className="text-ink-2">{it.label}</span>}
        </span>
      ))}
    </nav>
  );
}

export default function AssetMemory() {
  const { assetId = "" } = useParams();
  const tick = useLiveTick(["state", "evidence", "handoff", "session", "approval"]);
  const { data, error } = useFetch<AssetDetail>(`/api/assets/${assetId}`, [tick]);
  const { data: handoffs } = useFetch<Handoff[]>(`/api/handoffs?asset_id=${encodeURIComponent(assetId)}`, [tick]);
  const taskLabel = useTaskLabels();
  const [shown, setShown] = useState(2);
  const [chunk, setChunk] = useState<string | null>(null);
  const { data: chunkData } = useFetch<{ section: string; title: string; body: string }>(chunk ? `/api/manual/${chunk}` : null, [chunk]);

  const shifts = useMemo(() => {
    if (!data) return [];
    const by = new Map<string, Evidence[]>();
    for (const e of data.evidence) { const k = e.session_id ?? "—"; by.set(k, [...(by.get(k) ?? []), e]); }
    return [...data.sessions].sort((a, b) => b.started_at.localeCompare(a.started_at))
      .map((s) => ({ s, items: (by.get(s.session_id) ?? []).sort((a, b) => a.ts.localeCompare(b.ts) || a.id - b.id), h: handoffs?.find((h) => h.session_id === s.session_id) }))
      .filter((x) => x.items.length || x.h);
  }, [data, handoffs]);

  if (error) return <div className="p-6 text-red">Could not open this machine: {error}</div>;
  if (!data) return <div className="p-6 text-pencil">Opening the log…</div>;
  const a = data.asset;
  const meta = a.metadata as Record<string, unknown>;
  const safety = (meta.safety_notes as string[] | undefined) ?? [];
  const openWos = data.work_orders.filter((w) => !["CLOSED", "RESOLVED"].includes(w.status));

  return (
    <div className="px-4 py-6 max-w-[1400px] mx-auto grid gap-6">
      <div className="grid gap-1.5">
        <Crumbs items={[{ to: "/board", label: "Shift board" }, { label: a.asset_id }]} />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <h1 className="text-[32px] leading-tight font-bold tracking-[-0.015em]">{a.name}</h1>
          <Stamp value={a.status} />
        </div>
        <p className="text-[15px] text-ink-2">
          {a.location}. {a.manufacturer} {a.model}, serial {a.serial_no}.{meta.running_hours ? ` ${String(meta.running_hours)} running hours.` : ""}{meta.serves ? ` Serves ${String(meta.serves)}.` : ""}
          {meta.panel ? <> <a href={`/panel/${a.asset_id}`} target="_blank" rel="noreferrer" className="text-blue underline">Simulated panel</a></> : null}
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px] items-start">
        <div className="lg:col-start-2 lg:row-start-1 lg:sticky lg:top-20 grid gap-6">
          <StartPanel assetId={a.asset_id} assetName={a.name} />
          {safety.length > 0 && (
            <div className="border-l-4 border-red pl-3">
              <h2 className="text-[15px] font-bold text-red">Safety on this machine</h2>
              <ul className="mt-1 grid gap-1 text-[15px]">{safety.map((n, i) => <li key={i}>{n}</li>)}</ul>
            </div>
          )}
        </div>

        <div className="lg:col-start-1 lg:row-start-1 lg:row-span-2 grid gap-8 min-w-0">
          <Section title={data.open_items.length ? `Still open (${data.open_items.length})` : "Nothing left open"} note="Hypotheses and questions no shift has closed yet. Ask the agent about any of them.">
            {data.open_items.length === 0 ? <Empty>Every question has an answer on record.</Empty> : (
              <ul>{data.open_items.map((e) => (
                <li key={e.id} className="grid grid-cols-[22px_1fr] gap-x-2 py-2 border-b border-rule last:border-0">
                  <span className="pt-1.5"><SourceMark source={e.source_type} /></span>
                  <div><div className="text-[17px] leading-snug">{e.title}</div>
                    <div className="text-[14px] text-pencil mt-0.5">{e.event_type === "hypothesis" ? "Hypothesis" : "Question"} from {e.raised_by_technician ? `${e.raised_by_technician}'s shift` : "an earlier shift"}, {fmtDateTime(e.ts)}, #{e.id}</div></div>
                </li>))}</ul>
            )}
          </Section>

          <Section title="Log" note="Newest shift first. Read each shift top to bottom." right={<MarksKey />}>
            <ol className="trace" style={traceStyle(84)}>
              {shifts.slice(0, shown).map(({ s, items, h }) => (
                <FragmentShift key={s.session_id} s={s} items={items} h={h} task={s.task_id ? taskLabel[s.task_id] : undefined} />
              ))}
            </ol>
            {shifts.length > shown && <button onClick={() => setShown(shifts.length)} className="mt-3 text-[15px] text-blue underline">Show {shifts.length - shown} earlier {shifts.length - shown === 1 ? "shift" : "shifts"}</button>}
          </Section>
        </div>

        <div className="lg:col-start-2 lg:row-start-2 grid gap-6">
          <Section title="Work orders">
            <ul>{[...openWos, ...data.work_orders.filter((w) => !openWos.includes(w))].map((w) => (
              <li key={w.work_order_id} className={cx("py-2 border-b border-rule last:border-0", !openWos.includes(w) && "text-pencil")}>
                <div className="flex flex-wrap items-center gap-2"><b>{w.work_order_id}</b><Stamp value={w.status} /></div>
                <div className="text-[15px]">{w.title}</div>
                {w.log.length > 0 && openWos.includes(w) && <div className="text-[14px] text-pencil mt-0.5">Latest: {w.log[w.log.length - 1].author}, {w.log[w.log.length - 1].note}</div>}
              </li>))}</ul>
          </Section>
          <Section title={`Manual, ${a.model}`} note="Fictional. The agent cites these sections.">
            <ul>{data.manual_sections.map((m) => (
              <li key={m.chunk_id} className="border-b border-rule last:border-0">
                <button onClick={() => setChunk(chunk === m.chunk_id ? null : m.chunk_id)} aria-expanded={chunk === m.chunk_id}
                  className={cx("w-full text-left text-[15px] py-1.5 flex gap-3 hover:text-ink", chunk === m.chunk_id ? "font-bold" : "text-ink-2")}>
                  <span className="w-8 shrink-0 text-pencil">{m.section}</span><span>{m.title}</span>
                </button>
                {chunk === m.chunk_id && chunkData && <p className="pb-3 text-[15px] text-ink-2 whitespace-pre-wrap">{chunkData.body}</p>}
              </li>
            ))}</ul>
          </Section>
        </div>
      </div>
    </div>
  );
}

function FragmentShift({ s, items, h, task }: { s: SessionRow; items: Evidence[]; h?: Handoff; task?: string }) {
  return (
    <>
      <ShiftBand left={dayLabel(s.started_at)} live={s.status === "ACTIVE"}
        title={<Link to={`/session/${s.session_id}`} className="hover:underline">{s.technician}, {s.shift_label}</Link>}
        meta={<>{task ? `${task}. ` : ""}Session {s.session_id}</>} right={s.status === "ACTIVE" ? <Stamp value="ACTIVE" /> : undefined} />
      {items.map((e) => <EvidenceEntry key={e.id} e={e} />)}
      {h && (
        <TraceRow time={hhmm(h.created_at)} mark={<Glyph tone="ok" size={12} />}>
          <div className="text-[14px] text-pencil">Handed over</div>
          <p className="text-[16px] max-w-[70ch]">{h.report.headline} <Link to={`/handoffs/${h.handoff_id}`} className="text-blue underline whitespace-nowrap">Read {h.handoff_id}</Link></p>
        </TraceRow>
      )}
    </>
  );
}

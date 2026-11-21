import { type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { FileSpreadsheet, FileText, Printer } from "lucide-react";
import { dayLabel, fmtDateTime, hhmm, media, type Handoff } from "../api";
import { useFetch, useLiveTick } from "../live";
import { HandOver } from "../start";
import { Btn, Empty, Glyph, MarksKey, PageHead, SOURCE, SourceMark, Stamp } from "../ui";
import { Crumbs } from "./AssetMemory";

export function HandoffList() {
  const tick = useLiveTick(["handoff", "reset"]);
  const { data } = useFetch<Handoff[]>("/api/handoffs", [tick]);
  return (
    <div className="px-4 py-8 max-w-[1000px] mx-auto grid gap-6">
      <PageHead title="Handoffs" sub="What each shift did, what was verified and what it left open. The next shift's agent reads these aloud." />
      <ol className="border-t border-rule">
        {data?.length === 0 && <li><Empty>No handoffs yet. Finish a session to write one.</Empty></li>}
        {data?.map((h) => (
          <li key={h.handoff_id} className="border-b border-rule">
            <Link to={`/handoffs/${h.handoff_id}`} className="grid grid-cols-[96px_minmax(0,1fr)] gap-x-4 py-3 hover:bg-ink/[0.03]">
              <span className="text-[14px] text-pencil pt-0.5">{dayLabel(h.created_at)}<span className="block">{hhmm(h.created_at)}</span></span>
              <span className="min-w-0">
                <span className="text-[17px]"><b>{h.report.asset.asset_id}</b> {h.report.asset.name}</span>
                <span className="text-[15px] text-pencil"> from {h.created_by}, {h.report.session.shift}</span>
                <span className="block text-[16px] text-ink-2 mt-0.5">{h.report.headline}</span>
                <span className="block text-[14px] text-pencil mt-0.5">{h.handoff_id}, {h.report.open_loops.length} left open</span>
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Part({ title, count, children, tone }: { title: string; count?: number; tone?: "caution" | "alarm"; children: ReactNode }) {
  return (
    <section className="py-4 border-t border-rule-strong">
      <h3 className="text-[17px] font-bold" style={tone && count ? { color: tone === "alarm" ? "var(--red)" : "var(--ochre)" } : undefined}>
        {title}{count !== undefined && <span className="font-normal text-pencil"> ({count})</span>}
      </h3>
      <div className="mt-2">{children}</div>
    </section>
  );
}

const Line = ({ mark, children, sub }: { mark: ReactNode; children: ReactNode; sub?: ReactNode }) => (
  <li className="grid grid-cols-[18px_1fr] gap-x-2.5 text-[16px] leading-snug"><span className="pt-1">{mark}</span><span>{children}{sub && <span className="block text-[14px] text-pencil mt-0.5">{sub}</span>}</span></li>
);

export function HandoffView() {
  const { handoffId = "" } = useParams();
  const tick = useLiveTick(["handoff"]);
  const { data: h, error } = useFetch<Handoff>(`/api/handoffs/${handoffId}`, [tick]);
  if (error) return <div className="p-6 text-red">Could not open this handoff: {error}</div>;
  if (!h) return <div className="p-6 text-pencil">Opening the handoff…</div>;
  const r = h.report;
  return (
    <div className="px-4 py-6 max-w-[920px] mx-auto grid gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3 no-print">
        <Crumbs items={[{ to: "/handoffs", label: "Handoffs" }, { label: h.handoff_id }]} />
        <div className="flex flex-wrap items-center gap-1">
          <a href={`/api/handoffs/${h.handoff_id}/report.xlsx`} className="inline-flex items-center gap-1.5 h-8 px-2.5 rounded-[7px] text-[14px] text-ink-2 hover:text-ink hover:bg-ink/5" title="Download as an Excel workbook"><FileSpreadsheet size={15} />Excel</a>
          <a href={`/api/handoffs/${h.handoff_id}/report.html?download=true`} className="inline-flex items-center gap-1.5 h-8 px-2.5 rounded-[7px] text-[14px] text-ink-2 hover:text-ink hover:bg-ink/5" title="Download a self-contained report page to attach or forward"><FileText size={15} />Report file</a>
          <Btn kind="quiet" size="sm" onClick={() => window.print()}><Printer size={15} />Print</Btn>
        </div>
      </div>

      <article className="bg-sheet border border-rule-strong shadow-[0_1px_0_var(--rule),0_8px_24px_-12px_rgba(0,0,0,.18)] rounded-2xl px-5 sm:px-8 py-6">
        <header className="flex flex-wrap items-baseline justify-between gap-2 pb-3 border-b border-rule">
          <span className="text-[15px] font-bold">Shift handoff {h.handoff_id}</span>
          <span className="text-[14px] text-pencil">Filed {fmtDateTime(h.created_at)}</span>
        </header>
        <h1 className="mt-4 text-[30px] leading-tight font-bold tracking-[-0.015em]">{r.asset.name}</h1>
        <p className="text-[15px] text-ink-2 mt-1">
          From {r.session.technician}, {r.session.shift}{r.task ? `, ${r.task.label.toLowerCase()}` : ""}.{" "}
          {r.session.session_id && <Link className="text-blue underline" to={`/session/${r.session.session_id}`}>Session {r.session.session_id}</Link>}
          {r.carried_over_from && <>, continues <Link className="text-blue underline" to={`/handoffs/${r.carried_over_from}`}>{r.carried_over_from}</Link></>}
        </p>
        <p className="mt-4 text-[20px] leading-snug max-w-[62ch]">{r.headline}</p>
        {r.work_order && <p className="mt-3 flex flex-wrap items-center gap-2 text-[15px]"><b>{r.work_order.work_order_id}</b><Stamp value={r.work_order.status} /><span className="text-ink-2">{r.work_order.title}</span></p>}

        <div className="mt-5">
          <Part title="Still open" count={r.open_loops.length} tone="caution">
            {r.open_loops.length ? <ul className="grid gap-2">{r.open_loops.map((l, i) => (
              <Line key={i} mark={<Glyph tone="caution" size={11} />} sub={`${l.type === "hypothesis" ? "Hypothesis" : "Question"}${l.raised_by ? `, raised on ${l.raised_by}'s shift` : ""}${l.event_id ? `, #${l.event_id}` : ""}`}>{l.text}</Line>))}</ul>
              : <Empty>Nothing. Every question from this shift was answered.</Empty>}
          </Part>
          {r.actions_failed_or_pending.length > 0 && (
            <Part title="Not done" count={r.actions_failed_or_pending.length} tone="alarm">
              <ul className="grid gap-2">{r.actions_failed_or_pending.map((a, i) => (
                <Line key={i} mark={<Glyph tone={a.status === "PENDING_APPROVAL" ? "caution" : "alarm"} size={11} />} sub={a.detail ?? undefined}>{a.text}</Line>))}</ul>
            </Part>
          )}
          <Part title="Done and verified" count={r.actions_completed.length}>
            {r.actions_completed.length ? <ul className="grid gap-2">{r.actions_completed.map((a, i) => (
              <Line key={i} mark={<Glyph tone="ok" size={12} />} sub={a.detail}>{a.text}</Line>))}</ul> : <Empty>No changes were made.</Empty>}
          </Part>
          <Part title="Seen and said" count={r.observations.length}>
            {r.observations.length ? <ul className="grid gap-2.5">{r.observations.map((o, i) => (
              <Line key={i} mark={<SourceMark source={o.source} />} sub={`${SOURCE[o.source]?.label ?? o.source}${o.ts ? `, ${fmtDateTime(o.ts)}` : ""}${o.event_id ? `, #${o.event_id}` : ""}`}>
                {o.text}{o.media_ref && <img src={media(o.media_ref)} alt="Camera frame for this observation" className="mt-1.5 max-h-32 rounded-2xl border border-rule block" />}
              </Line>))}</ul> : <Empty>No observations.</Empty>}
            <div className="mt-3"><MarksKey /></div>
          </Part>
          {(r.ruled_out.length + (r.confirmed?.length ?? 0)) > 0 && (
            <Part title="Ruled out or confirmed">
              <ul className="grid gap-1.5 text-[16px]">
                {r.ruled_out.map((x, i) => <li key={`r${i}`} className="text-pencil"><span className="line-through">{x.text}</span>{x.reason && <span>: {x.reason}</span>}</li>)}
                {r.confirmed?.map((x, i) => <li key={`c${i}`} className="flex flex-wrap items-center gap-2">{x.text} <Stamp value={x.status ?? "confirmed"} /></li>)}
              </ul>
            </Part>
          )}
          {r.parts.length > 0 && (
            <Part title="Parts" count={r.parts.length}>
              <ul className="grid gap-1.5 text-[16px]">{r.parts.map((p, i) => <li key={i}>{p.name}: <b>{p.state}</b> <span className="text-[14px] text-pencil">{p.part_id}{p.ref ? `, ${p.ref}` : ""}</span></li>)}</ul>
            </Part>
          )}
          <Part title="Suggested next steps">
            <ol className="list-decimal pl-5 grid gap-1.5 text-[16px] text-ink-2">{r.suggested_next_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
            <p className="text-[14px] text-pencil mt-2">Suggestions from the record, not instructions. Follow site procedure.</p>
          </Part>
          {r.follow_ups && r.follow_ups.length > 0 && (
            <Part title="Follow-ups scheduled" count={r.follow_ups.length}>
              <ul className="grid gap-1.5 text-[16px]">{r.follow_ups.map((f) => <li key={f.follow_up_id}>{f.title} <span className="text-[14px] text-pencil">{f.follow_up_id}, {f.assignee}, due {f.due ?? "no date"}</span></li>)}</ul>
            </Part>
          )}
          <Part title="Spoken summary for the next shift">
            <blockquote className="border-l-2 border-teal pl-4 text-[16px] text-ink-2 max-w-[68ch]">{r.spoken_summary}</blockquote>
          </Part>
        </div>
        <footer className="mt-2 pt-3 border-t border-rule text-[13px] text-pencil grid gap-1">
          <p>Written by {r.generated_by}. Every line maps to a stored evidence item, tool result or database record.</p>
          {r.records_consulted && r.records_consulted.length > 0 && <p>Records read: {r.records_consulted.map((c) => c.tool.replace(/_/g, " ")).join(", ")}.</p>}
          {r.manual_refs.length > 0 && <p>Manual sections: {r.manual_refs.join(", ")}.</p>}
          <p className="no-print"><Link to={r.session.session_id ? `/audit?session=${r.session.session_id}` : "/audit"} className="text-blue underline">Audit log for this session</Link></p>
        </footer>
      </article>

      <section className="no-print border-t border-rule pt-3 grid gap-2" aria-label="Hand over">
        <h2 className="text-[19px] font-bold">Hand over {r.asset.asset_id}</h2>
        <HandOver assetId={r.asset.asset_id} from={r.session.technician} />
      </section>
    </div>
  );
}

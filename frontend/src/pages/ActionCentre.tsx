import { useState } from "react";
import { Link } from "react-router-dom";
import { api, fmtDateTime, type FollowUp, type Part, type Procurement, type Transfer, type WorkOrder } from "../api";
import { useFetch, useLiveTick } from "../live";
import { Btn, Empty, PageHead, Panel, Status, cx } from "../ui";

interface Reservation { reservation_id: string; part_id: string; part_name: string; quantity: number; work_order_id: string; session_id: string; status: string; created_at: string }
interface Shipment { shipment_id: string; direction: string; carrier: string; carrier_ref: string; status: string; origin: string; destination: string; eta: string; items: { part_id: string; name: string; quantity: number }[]; last_event: string; updated_at: string }
interface Learning { trainee: string; module_id: string; title: string; asset_id: string; status: string; score: number | null; attempts: number; updated_at: string }
interface Escalation { escalation_id: string; work_order_id: string; asset_id: string; session_id: string; severity: string; reason: string; status: string; created_at: string }

const th = "font-medium text-[13px] text-pencil px-4 py-2.5 text-left whitespace-nowrap";
const td = "px-4 py-2.5 align-top";

export default function ActionCentre() {
  const tick = useLiveTick(["state", "tool", "approval", "flags"]);
  const { data: parts } = useFetch<Part[]>("/api/inventory", [tick]);
  const { data: prs } = useFetch<Procurement[]>("/api/procurement", [tick]);
  const { data: res } = useFetch<Reservation[]>("/api/reservations", [tick]);
  const { data: esc } = useFetch<Escalation[]>("/api/escalations", [tick]);
  const { data: wos } = useFetch<WorkOrder[]>("/api/work-orders", [tick]);
  const { data: transfers } = useFetch<Transfer[]>("/api/transfers", [tick]);
  const { data: shipments } = useFetch<Shipment[]>("/api/shipments", [tick]);
  const { data: followUps } = useFetch<FollowUp[]>("/api/follow-ups", [tick]);
  const { data: learning } = useFetch<Learning[]>("/api/learning-records", [tick]);
  const decideT = async (t: Transfer, ok: boolean) => {
    setBusy(t.transfer_id);
    try { await api.post(`/api/transfers/${t.transfer_id}/${ok ? "confirm" : "cancel"}`, { session_id: t.session_id }); } finally { setBusy(null); }
  };
  const [busy, setBusy] = useState<string | null>(null);
  const pending = prs?.filter((p) => p.status === "PENDING_APPROVAL") ?? [];
  const decide = async (p: Procurement, approve: boolean) => {
    setBusy(p.request_id);
    try { await api.post(`/api/procurement/${p.request_id}/${approve ? "approve" : "reject"}`, { session_id: p.session_id }); } finally { setBusy(null); }
  };

  return (
    <div className="px-4 py-6 grid gap-5 max-w-[1400px] mx-auto">
      <PageHead title="Stock, orders and follow-ups"
        sub={<>Work orders, stock, reservations and purchasing in the (fictional) maintenance system. Everything here is read back from the database. For who did what and when, see the <Link to="/audit" className="text-blue hover:underline">audit log</Link>.</>}
        right={<a href="/api/reports/operations.xlsx" className="h-10 px-4 rounded-lg border border-rule-strong hover:bg-sheet text-[14px] inline-flex items-center gap-2" title="Sessions with handoff and audit links, tool calls, orders, transfers, stock, follow-ups, training, events">Export to Excel</a>} />

      {pending.length > 0 && (
        <Panel title={`Waiting for your approval (${pending.length})`} hint="Nothing is ordered until a person approves: by saying yes after the agent reads the order back, or here."
          className="bg-ochre-wash px-3 pb-2 border-ochre">
          <ul>{pending.map((p) => (
            <li key={p.request_id} className="flex flex-wrap items-center gap-3 py-2.5 border-t border-rule first:border-0">
              <span className="min-w-0 grow"><span className="text-[15px]">Order <b>{p.quantity} × {p.part_name}</b> for {p.work_order_id ?? "no work order"}</span>
                <span className="block text-[13px] text-pencil"><span className="ref">{p.request_id}</span>, drafted by {p.created_by} {fmtDateTime(p.created_at)}, supplier {p.supplier}</span></span>
              <Btn kind="approve" disabled={busy === p.request_id} onClick={() => decide(p, true)}>Approve & submit</Btn>
              <Btn kind="quiet" disabled={busy === p.request_id} onClick={() => decide(p, false)}>Decline</Btn>
            </li>))}</ul>
        </Panel>
      )}

      <div className="grid xl:grid-cols-2 gap-5 items-start">
        <Panel title="Orders" hint="Procurement requests, with who approved each one and how." flush>
          {!prs?.length ? <div className="px-4 pb-3"><Empty>No orders yet. The agent drafts one when a part is out of stock.</Empty></div> : (
            <div className="overflow-x-auto"><table className="w-full text-[14px]">
              <thead><tr className="border-y border-rule">{["Order", "Status", "Approved by", "Supplier"].map((h) => <th key={h} className={th}>{h}</th>)}</tr></thead>
              <tbody>{prs.map((p) => (
                <tr key={p.request_id} className="border-b border-rule last:border-0">
                  <td className={td}><div>{p.quantity} × {p.part_name}</div>
                    <div className="text-[13px] text-pencil"><span className="ref">{p.request_id}</span>, {p.work_order_id}{p.session_id && <>, <Link to={`/session/${p.session_id}`} className="ref text-blue hover:underline">{p.session_id}</Link></>}</div></td>
                  <td className={td}><Status value={p.status} />{p.failure_reason && <div className="text-[13px] text-red mt-1 max-w-60">{p.failure_reason}</div>}</td>
                  <td className={cx(td, "text-ink-2")}>{p.approved_by ? <>{p.approved_by}, {p.approval_via === "voice" ? "by voice" : "in the console"}{p.approval_evidence && <div className="text-[13px] text-pencil max-w-64">{p.approval_evidence}</div>}</> : <span className="text-pencil">not yet</span>}</td>
                  <td className={cx(td, "text-ink-2")}>{p.supplier}{p.supplier_ref && <div className="text-[13px] text-pencil"><span className="ref">{p.supplier_ref}</span>, due {p.expected_by}</div>}</td>
                </tr>))}</tbody>
            </table></div>
          )}
        </Panel>

        <Panel title="Stock" hint="Out-of-stock parts first. Available means on hand minus reserved." flush>
          <div className="overflow-x-auto"><table className="w-full text-[14px]">
            <thead><tr className="border-y border-rule">{["Part", "Available", "On hand", "Reserved", "Lead time", "Location"].map((h) => <th key={h} className={th}>{h}</th>)}</tr></thead>
            <tbody>{parts?.slice().sort((a, b) => Number(a.available > 0) - Number(b.available > 0)).map((p) => (
              <tr key={p.part_id} className="border-b border-rule last:border-0">
                <td className={td}><div>{p.name}</div><div className="ref text-[13px] text-pencil">{p.part_id}</div></td>
                <td className={td}>{p.available === 0 ? <Status value="OUT" /> : <span className="font-semibold">{p.available}</span>}</td>
                <td className={cx(td, "text-ink-2")}>{p.on_hand}</td>
                <td className={cx(td, "text-ink-2")}>{p.reserved}</td>
                <td className={cx(td, "text-ink-2 whitespace-nowrap")}>{p.lead_time_days} days</td>
                <td className={cx(td, "text-ink-2")}>{p.location}</td>
              </tr>))}</tbody>
          </table></div>
        </Panel>

        <Panel title="Work orders" flush>
          <ul>{wos?.map((w) => (
            <li key={w.work_order_id} className="px-4 py-3 border-t border-rule">
              <div className="flex flex-wrap items-center gap-2"><Status value={w.status} /><span className="ref">{w.work_order_id}</span><span className="text-[13px] text-pencil">{w.asset_id}, priority {w.priority}</span>
                <span className="ml-auto text-[13px] text-pencil">Updated {fmtDateTime(w.updated_at)}</span></div>
              <div className="text-[15px] mt-1">{w.title}</div>
              {w.log.length > 0 && <div className="text-[14px] text-ink-2 mt-0.5">Latest: {w.log[w.log.length - 1].author}: {w.log[w.log.length - 1].note}</div>}
            </li>))}</ul>
        </Panel>

        <div className="grid gap-5">
          <Panel title="Reservations">
            {!res?.length ? <Empty>No parts reserved.</Empty> : <ul>{res.map((r) => (
              <li key={r.reservation_id} className="flex flex-wrap items-center gap-2 py-2 border-t border-rule first:border-0 text-[15px]">
                {r.quantity} × {r.part_name}<span className="text-[13px] text-pencil"><span className="ref">{r.reservation_id}</span> for {r.work_order_id}</span><Status value={r.status} className="ml-auto" />
              </li>))}</ul>}
          </Panel>
          <Panel title="Escalations">
            {!esc?.length ? <Empty>No escalations.</Empty> : <ul>{esc.map((e) => (
              <li key={e.escalation_id} className="py-2 border-t border-rule first:border-0">
                <div className="flex items-center gap-2"><Status value={e.severity === "high" ? "ESCALATED" : e.status} /><span className="ref text-[13px] text-pencil">{e.escalation_id}, {e.work_order_id}</span></div>
                <div className="text-[15px] mt-1">{e.reason}</div>
              </li>))}</ul>}
          </Panel>
        </div>
            </div>

      <div className="grid xl:grid-cols-2 gap-5 items-start">
        <Panel title="Stock transfers" hint="Moves between locations. Stock moves and the ERP is posted only after a person confirms." flush>
          {!transfers?.length ? <div className="px-4 pb-3"><Empty>No transfers yet. In a warehouse session, ask the agent to replenish a pick face.</Empty></div> : (
            <ul>{transfers.map((t) => (
              <li key={t.transfer_id} className="px-4 py-3 border-t border-rule flex flex-wrap items-center gap-x-3 gap-y-1">
                <Status value={t.status} />
                <span className="text-[15px]">{t.quantity} × {t.part_name}</span>
                <span className="text-[13px] text-pencil">{t.from_location} to {t.to_location}, {t.transfer_id}{t.erp_ref ? `, ERP ${t.erp_ref}` : ""}{t.confirmed_by ? `, confirmed by ${t.confirmed_by} ${t.confirmation_via === "voice" ? "by voice" : "in the console"}` : ""}</span>
                {t.status === "PENDING_CONFIRMATION" && <span className="ml-auto flex gap-2"><Btn kind="approve" size="sm" disabled={busy === t.transfer_id} onClick={() => decideT(t, true)}>Confirm & move</Btn><Btn kind="quiet" size="sm" disabled={busy === t.transfer_id} onClick={() => decideT(t, false)}>Cancel</Btn></span>}
                {t.failure_reason && <span className="w-full text-[13px] text-red">{t.failure_reason}</span>}
              </li>))}</ul>
          )}
        </Panel>

        <Panel title="Shipments" hint="Carrier tracking records the agent reads." flush>
          <ul>{shipments?.map((sh) => (
            <li key={sh.shipment_id} className="px-4 py-3 border-t border-rule">
              <div className="flex flex-wrap items-center gap-2"><Status value={sh.status} /><b>{sh.shipment_id}</b><span className="text-[13px] text-pencil">{sh.direction}, {sh.carrier}, ref {sh.carrier_ref}</span>
                <span className="ml-auto text-[13px] text-pencil">ETA {fmtDateTime(sh.eta)}</span></div>
              <div className="text-[14px] mt-1">{sh.origin} to {sh.destination}: {sh.items.map((i) => `${i.quantity} × ${i.name}`).join(", ")}</div>
              <div className="text-[13px] text-ink-2">{sh.last_event}</div>
            </li>))}</ul>
        </Panel>

        <Panel title="Follow-ups" hint="Scheduled by the agent when you agreed, so nothing waits on memory." flush>
          {!followUps?.length ? <div className="px-4 pb-3"><Empty>No follow-ups scheduled.</Empty></div> : (
            <ul>{followUps.map((f) => (
              <li key={f.follow_up_id} className="px-4 py-3 border-t border-rule flex flex-wrap items-center gap-x-3 gap-y-1">
                <Status value={f.status} /><span className="text-[15px]">{f.title}</span>
                <span className="text-[13px] text-pencil">{f.follow_up_id}, {f.assignee}, due {f.due_date ?? f.due_text ?? "no date"}, {f.asset_id}</span>
                {f.due_date && <span className="ml-auto inline-flex items-center gap-3 text-[13px]"><span className="text-pencil">Add to calendar:</span>
                  {f.calendar?.google_calendar && <a href={f.calendar.google_calendar} target="_blank" rel="noreferrer" className="text-blue hover:underline">Google</a>}
                  {f.calendar?.outlook_calendar && <a href={f.calendar.outlook_calendar} target="_blank" rel="noreferrer" className="text-blue hover:underline">Outlook</a>}
                  <a href={`/api/follow-ups/${f.follow_up_id}.ics`} className="text-blue hover:underline">.ics</a></span>}
              </li>))}</ul>
          )}
        </Panel>

        <Panel title="Learning records" hint="Training results. Answers are marked in code against the manual, not by the model." flush>
          {!learning?.length ? <div className="px-4 pb-3"><Empty>No training recorded.</Empty></div> : (
            <ul>{learning.map((l) => (
              <li key={`${l.trainee}-${l.module_id}`} className="px-4 py-3 border-t border-rule flex flex-wrap items-center gap-x-3 gap-y-1">
                <Status value={l.status} /><span className="text-[15px]"><b>{l.trainee}</b>, {l.title}</span>
                <span className="text-[13px] text-pencil">{l.score ?? "–"}%, {l.attempts} attempt{l.attempts === 1 ? "" : "s"}, {fmtDateTime(l.updated_at)}</span>
              </li>))}</ul>
          )}
        </Panel>
      </div>
    </div>
  );
}

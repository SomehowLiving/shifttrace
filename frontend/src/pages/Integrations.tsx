import { useState } from "react";
import { CalendarPlus, Check, FileSpreadsheet, Link2, MessageCircle, Paperclip, Plug, RefreshCw, Send, Sheet, X } from "lucide-react";
import { api, fmtDateTime } from "../api";
import { useFetch, useLiveTick } from "../live";
import { Btn, Empty, PageHead, Stamp, cx } from "../ui";

interface Connector { id: string; name: string; env: Record<string, boolean>; required: string[]; events: string | string[]; enabled: boolean; local?: boolean; attaches?: string }
interface Delivery { id: number; connector: string; target: string; status: string; http_status: number | null; detail: string; attempts: number; ts: string }
interface Ev { id: number; ts: string; event_type: string; ref: string | null; summary: string; asset_id: string; session_id: string | null; deliveries: Delivery[] }
interface Status { connectors: Connector[]; events: Ev[]; received: { id: number; ts: string; event_type: string; signature_valid: number }[]; counts: { events: number; delivered: number; failed: number }; console_url?: string }

const HOWTO: Record<string, string> = {
  telegram: "Create a bot with @BotFather, add it to the team's group, then set the bot token and the group's chat id.",
  whatsapp: "Meta WhatsApp Cloud API: a business phone number id, an access token and the recipient. Outside a 24-hour reply window WhatsApp only delivers approved templates: set WHATSAPP_TEMPLATE.",
  excel: "Excel Online: a Power Automate flow 'When an HTTP request is received' then 'Add a row into a table'. Google Sheets: an Apps Script web app that appends the row. Paste the flow or script URL.",
  slack: "Slack incoming webhook URL.", teams: "Teams Workflows (incoming webhook) URL.",
};
const ICON: Record<string, typeof Plug> = { telegram: MessageCircle, whatsapp: MessageCircle, excel: Sheet, slack: MessageCircle, teams: MessageCircle };

const TITLES: Record<string, string> = {
  "order.submitted": "Order submitted", "transfer.posted": "Stock transfer posted", "work_order.updated": "Work order updated",
  "escalation.raised": "Escalation raised", "follow_up.scheduled": "Follow-up scheduled", "handoff.published": "Handoff published",
  "training.recorded": "Learning record updated", "reading.out_of_limit": "Reading out of limit", "integration.test": "Test event",
};

export default function Integrations() {
  const tick = useLiveTick(["integration", "tool", "state", "approval", "handoff"]);
  const { data, reload } = useFetch<Status>("/api/integrations", [tick]);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const local = data?.connectors.find((c) => c.id === "local");
  const external = data?.connectors.filter((c) => !c.local) ?? [];
  const live = data?.connectors.filter((c) => c.enabled) ?? [];

  const toggleLocal = async () => { setBusy("local"); try { await api.post("/api/integrations/local-receiver", { enabled: !local?.enabled }); reload(); } finally { setBusy(null); } };
  const test = async () => {
    setBusy("test"); setMsg(null);
    try {
      const r = await api.post<{ results: { connector: string; status: string }[] }>("/api/integrations/test");
      setMsg(r.results.length ? r.results.map((x) => `${x.connector}: ${x.status}`).join(", ") : "No system is connected yet, so nothing was sent.");
      reload();
    } finally { setBusy(null); }
  };
  const retry = async (e: Ev, connector: string) => { setBusy(`${e.id}-${connector}`); try { await api.post(`/api/integrations/retry/${e.id}?connector=${connector}`); reload(); } finally { setBusy(null); } };

  return (
    <div className="px-5 sm:px-8 py-8 max-w-[1320px] mx-auto grid gap-8">
      <PageHead title="Connected systems"
        sub="Every action the agent completes and verifies becomes a business event, sent to the systems your site already uses: chat (Slack, Teams, Telegram, WhatsApp), spreadsheets (Excel, Google Sheets), ticketing, calendars and any webhook (ERP, CMMS or automation tools). Each message links back to the record, and the handoff report is attached where the channel accepts files. Nothing is sent until a connector is set up."
        right={<><a href="/api/integrations/calendar.ics" className="h-10 px-4 rounded-lg border border-rule-strong hover:bg-sheet text-[14px] inline-flex items-center gap-2"><CalendarPlus size={16} />Follow-ups calendar (.ics)</a>
          <a href="/api/reports/operations.xlsx" className="h-10 px-4 rounded-lg border border-rule-strong hover:bg-sheet text-[14px] inline-flex items-center gap-2"><FileSpreadsheet size={16} />Operations workbook (.xlsx)</a>
          <Btn kind="primary" onClick={test} disabled={busy === "test"}><Send size={16} />{busy === "test" ? "Sending…" : "Send test event"}</Btn></>} />
      {msg && <p role="status" className="-mt-4 text-[14px] text-ink-2">{msg}</p>}
      {data?.console_url && <p className="-mt-4 text-[13px] text-pencil inline-flex flex-wrap items-center gap-1.5"><Link2 size={14} />Links in messages point at <span className="font-mono text-ink-2">{data.console_url}</span>. Set PUBLIC_CONSOLE_URL to the console's address on the site network.</p>}

      <div className="grid grid-cols-3 gap-3">
        {[["Events", data?.counts.events ?? 0, "verified actions recorded"], ["Delivered", data?.counts.delivered ?? 0, "to connected systems"], ["Failed", data?.counts.failed ?? 0, "or partly sent, after retries"]].map(([l, v, n]) => (
          <div key={String(l)} className="card px-5 pt-4 pb-5"><div className="label">{l}</div><div className="mt-4 text-[40px] font-semibold leading-none tracking-[-0.05em] nameplate" style={{ color: l === "Failed" && Number(v) > 0 ? "var(--red)" : undefined }}>{v}</div><div className="mt-1.5 text-[13px] text-ink-2">{n}</div></div>
        ))}
      </div>

      <section aria-label="Connectors">
        <h2 className="text-[17px] font-semibold mb-3">Connectors</h2>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {external.map((c) => (
            <div key={c.id} className={cx("card p-5 flex flex-col gap-3", c.enabled && "border-green/40")}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5"><span className="w-9 h-9 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center">{(() => { const I = ICON[c.id] ?? Plug; return <I size={18} />; })()}</span><span className="text-[16px] font-semibold">{c.name}</span></div>
                {c.enabled ? <Stamp tone="ok" label="connected" /> : <Stamp tone="quiet" label="not set up" />}
              </div>
              <div className="text-[13px] text-ink-2">Sends: {c.events === "all" ? "every event" : (c.events as string[]).map((e) => TITLES[e] ?? e).join(", ")}</div>
              {c.attaches && <div className="text-[13px] text-ink-2 inline-flex items-center gap-1.5"><Paperclip size={13} />Attaches the {c.attaches}</div>}
              <ul className="grid gap-1 text-[13px] font-mono">
                {Object.entries(c.env).map(([k, set]) => <li key={k} className="flex items-center gap-2">{set ? <Check size={14} className="text-green" /> : <X size={14} className="text-pencil" />}<span className={set ? "" : "text-pencil"}>{k}</span></li>)}
              </ul>
              {!c.enabled && <p className="text-[12px] text-pencil mt-auto">{HOWTO[c.id] ? `${HOWTO[c.id]} ` : ""}Add {c.required.join(", ")} to backend/.env and restart.</p>}
            </div>
          ))}
          {local && (
            <div className={cx("card p-5 flex flex-col gap-3", local.enabled && "border-violet/50")}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5"><span className="w-9 h-9 rounded-lg bg-violet/10 text-violet flex items-center justify-center"><Plug size={18} /></span><span className="text-[16px] font-semibold">Local test receiver</span></div>
                {local.enabled ? <Stamp tone="model" label="on" /> : <Stamp tone="quiet" label="off" />}
              </div>
              <p className="text-[13px] text-ink-2">Delivers signed webhooks to this console's own endpoint and checks the signature, so you can watch the full pipeline without any external account. It is a local test, not an external system.</p>
              <div className="text-[13px] text-pencil">{data?.received.length ? `${data.received.length} received recently, ${data.received.filter((r) => r.signature_valid).length} with a valid signature` : "Nothing received yet"}</div>
              <Btn kind={local.enabled ? "default" : "primary"} onClick={toggleLocal} disabled={busy === "local"} className="mt-auto">{local.enabled ? "Turn off" : "Turn on"}</Btn>
            </div>
          )}
        </div>
      </section>

      <section aria-label="Event log">
        <div className="flex items-baseline justify-between mb-3"><h2 className="text-[17px] font-semibold">Event log</h2><span className="text-[13px] text-pencil">{live.length ? `${live.length} connected: ${live.map((c) => c.name).join(", ")}` : "No connector set up: events are recorded but not sent"}</span></div>
        <div className="card overflow-x-auto">
          {!data?.events.length ? <div className="px-5"><Empty>No events yet. Complete an action in a session (an order, a stock transfer, a follow-up, a handoff) and it appears here.</Empty></div> : (
            <table className="w-full text-[14px] min-w-[720px]">
              <thead><tr className="text-left text-[13px] text-pencil border-b border-rule"><th className="font-medium p-3 pl-5">When</th><th className="font-medium p-3">Event</th><th className="font-medium p-3">Delivery</th></tr></thead>
              <tbody>{data.events.map((e) => (
                <tr key={e.id} className="border-b border-rule last:border-0 align-top">
                  <td className="p-3 pl-5 text-pencil whitespace-nowrap">{fmtDateTime(e.ts)}</td>
                  <td className="p-3"><div className="font-semibold">{TITLES[e.event_type] ?? e.event_type}<span className="font-normal text-pencil"> · {e.asset_id}{e.ref ? ` · ${e.ref}` : ""}</span></div><div className="text-ink-2">{e.summary}</div></td>
                  <td className="p-3">
                    {e.deliveries.length ? <div className="grid gap-1.5">{e.deliveries.map((d) => (
                      <div key={d.id} className="flex flex-wrap items-center gap-2 text-[13px]">
                        <Stamp tone={d.status === "delivered" ? "ok" : d.status === "partial" ? "caution" : "alarm"} label={`${d.connector}: ${d.status}`} />
                        <span className="text-pencil">{d.detail}</span>
                        {d.status !== "delivered" && <button onClick={() => retry(e, d.connector)} disabled={busy === `${e.id}-${d.connector}`} className="inline-flex items-center gap-1 text-blue hover:underline"><RefreshCw size={13} />Retry</button>}
                      </div>))}</div> : <span className="text-[13px] text-pencil">recorded, not sent (no connector)</span>}
                  </td>
                </tr>))}</tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}

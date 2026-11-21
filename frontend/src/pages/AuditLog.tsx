import { Fragment, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { X } from "lucide-react";
import { fmtTime, type SessionRow, type ToolAction } from "../api";
import { useFetch, useLiveTick } from "../live";
import { Btn, Empty, Outcome, PageHead, Panel, RawCall, callerLabel, cx, describeTool, outcomeOf, WRITE_TOOLS } from "../ui";

const LIMIT = 300;
const dayOf = (ts: string) => {
  const d = new Date(ts); const today = new Date();
  if (d.toDateString() === today.toDateString()) return "Today";
  if (new Date(today.getTime() - 86400000).toDateString() === d.toDateString()) return "Yesterday";
  return d.toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
};

export default function AuditLog() {
  const tick = useLiveTick(["tool", "approval", "state"]);
  const [params, setParams] = useSearchParams();
  const session = params.get("session") ?? "";
  const { data: rows } = useFetch<ToolAction[]>(`/api/tool-actions?limit=${LIMIT}${session ? `&session_id=${encodeURIComponent(session)}` : ""}`, [tick]);
  const { data: sessions } = useFetch<SessionRow[]>("/api/sessions", [tick]);
  const [result, setResult] = useState("all");
  const [who, setWho] = useState("all");
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<number | null>(null);

  const list = useMemo(() => (rows ?? []).filter((t) => {
    const [tone] = outcomeOf(t);
    if (result === "verified" && tone !== "ok") return false;
    if (result === "failed" && tone !== "alarm") return false;
    if (result === "approval" && tone !== "caution") return false;
    if (result === "writes" && !WRITE_TOOLS.has(t.tool_name)) return false;
    if (who !== "all" && t.caller !== who) return false;
    if (q) {
      const d = describeTool(t);
      const hay = `${d.action} ${d.target} ${t.tool_name} ${t.session_id ?? ""} ${JSON.stringify(t.input)}`.toLowerCase();
      if (!hay.includes(q.toLowerCase())) return false;
    }
    return true;
  }), [rows, result, who, q]);
  const counts = useMemo(() => {
    const c = { failed: 0, approval: 0, verified: 0 };
    for (const t of rows ?? []) { const [tone] = outcomeOf(t); if (tone === "alarm") c.failed++; else if (tone === "caution") c.approval++; else if (tone === "ok") c.verified++; }
    return c;
  }, [rows]);
  const selected = list.find((t) => t.id === sel) ?? rows?.find((t) => t.id === sel) ?? null;
  const field = "h-9 px-2.5 rounded-[7px] bg-sheet border border-rule-strong text-[14px] outline-none focus:border-teal";

  let lastDay = "";
  return (
    <div className="px-4 py-6 grid gap-5 max-w-[1500px] mx-auto">
      <PageHead title="Audit log"
        sub={<>Every tool call made by the voice agent or the console, newest first. Changes show <b>Verified</b> only after the system re-read the database on a fresh connection. Conversations and evidence are on each session page.</>} />

      <div className="flex flex-wrap items-end gap-3">
        <label className="grid gap-1 text-[13px] text-pencil">Result
          <select value={result} onChange={(e) => setResult(e.target.value)} className={field}>
            <option value="all">All calls</option>
            <option value="writes">Changes only</option>
            <option value="verified">Verified changes ({counts.verified})</option>
            <option value="approval">Needs approval ({counts.approval})</option>
            <option value="failed">Failed ({counts.failed})</option>
          </select></label>
        <label className="grid gap-1 text-[13px] text-pencil">Made by
          <select value={who} onChange={(e) => setWho(e.target.value)} className={field}>
            <option value="all">Anyone</option><option value="agora_mcp">Voice agent</option><option value="console">Console</option>
          </select></label>
        <label className="grid gap-1 text-[13px] text-pencil">Session
          <select value={session} onChange={(e) => { const v = e.target.value; setParams(v ? { session: v } : {}); setSel(null); }} className={field}>
            <option value="">All sessions</option>
            {sessions?.map((s) => <option key={s.session_id} value={s.session_id}>{s.session_id}, {s.technician} on {s.asset_id}</option>)}
          </select></label>
        <label className="grid gap-1 text-[13px] text-pencil grow max-w-sm">Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Part, work order, query…" className={field} /></label>
        <span className="text-[14px] text-pencil pb-2">{list.length} of {rows?.length ?? 0}{rows?.length === LIMIT ? ` (latest ${LIMIT})` : ""}</span>
      </div>

      <div className={cx("grid gap-4 items-start", selected && "xl:grid-cols-[minmax(0,1fr)_440px]")}>
        <Panel flush className="overflow-hidden">
          {list.length === 0 ? <div className="px-4"><Empty>No calls match these filters.</Empty></div> : (
            <div className="overflow-x-auto">
              <table className="w-full text-[14px]">
                <thead><tr className="text-left text-[13px] text-pencil border-b border-rule">
                  <th className="font-medium px-4 py-2.5">Time</th>
                  <th className="font-medium px-3 py-2.5">Action</th>
                  <th className="font-medium px-3 py-2.5 hidden md:table-cell">Made by</th>
                  <th className="font-medium px-3 py-2.5 hidden md:table-cell">Session</th>
                  <th className="font-medium px-3 py-2.5">Result</th>
                </tr></thead>
                <tbody>
                  {list.map((t) => {
                    const d = describeTool(t); const day = dayOf(t.ts); const divider = day !== lastDay; lastDay = day;
                    return (
                      <Fragment key={t.id}>
                        {divider && <tr><td colSpan={5} className="px-4 pt-3 pb-1 text-[13px] font-semibold text-ink-2 bg-ink/[0.03]">{day}</td></tr>}
                        <tr onClick={() => setSel(t.id === sel ? null : t.id)} aria-selected={t.id === sel}
                          className={cx("border-b border-rule cursor-pointer align-top", t.id === sel ? "bg-ink/[0.04]" : "hover:bg-ink/[0.03]")}>
                          <td className="px-4 py-2.5 whitespace-nowrap text-ink-2">{fmtTime(t.ts)}</td>
                          <td className="px-3 py-2.5 min-w-0">
                            <button className="text-left" onClick={(e) => { e.stopPropagation(); setSel(t.id === sel ? null : t.id); }}>
                              <span>{d.action}</span>{d.target && <span className="block text-[13px] text-ink-2 max-w-[52ch] truncate">{d.target}</span>}
                            </button>
                          </td>
                          <td className="px-3 py-2.5 hidden md:table-cell whitespace-nowrap text-ink-2">{callerLabel(t.caller)}</td>
                          <td className="px-3 py-2.5 hidden md:table-cell whitespace-nowrap">{t.session_id ? <Link onClick={(e) => e.stopPropagation()} className="ref text-blue hover:underline" to={`/session/${t.session_id}`}>{t.session_id}</Link> : <span className="text-pencil">none</span>}</td>
                          <td className="px-3 py-2.5"><Outcome t={t} /></td>
                        </tr>
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        {selected && (
          <Panel className="xl:sticky xl:top-20" title={describeTool(selected).action} hint={describeTool(selected).target}
            right={<Btn kind="quiet" size="sm" title="Close details" onClick={() => setSel(null)}><X size={16} /></Btn>}>
            <dl className="grid grid-cols-[110px_1fr] gap-y-1.5 text-[14px] mb-3">
              <dt className="text-pencil">Result</dt><dd><Outcome t={selected} /></dd>
              <dt className="text-pencil">When</dt><dd>{new Date(selected.ts).toLocaleString()}</dd>
              <dt className="text-pencil">Made by</dt><dd>{callerLabel(selected.caller)}{selected.caller === "agora_mcp" ? " (through Agora's MCP connection)" : ""}</dd>
              <dt className="text-pencil">Session</dt><dd>{selected.session_id ? <Link className="ref text-blue hover:underline" to={`/session/${selected.session_id}`}>{selected.session_id}</Link> : "none"}</dd>
              <dt className="text-pencil">Took</dt><dd>{selected.duration_ms} ms</dd>
              {(selected.result as { message?: string } | null)?.message && <><dt className="text-pencil">Message</dt><dd>{(selected.result as { message?: string }).message}</dd></>}
            </dl>
            <RawCall t={selected} />
          </Panel>
        )}
      </div>
    </div>
  );
}

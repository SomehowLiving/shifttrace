// Running cost and the controls that keep it low (System page).
import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch, useLiveTick } from "../live";
import { Btn, Panel, cx } from "../ui";

interface Rate { key: string; label: string; value: number; unit: string; source: string }
interface Proj { settings: Record<string, string>; per_active_minute_usd: number; per_shift_usd: number; per_month_usd: number; always_on_8h_shift_usd: number; assumptions: string; rates: Rate[] }
interface Overview { projection: Proj; sessions: { session_id: string; asset_id: string; technician: string; started_at: string; status: string; cost: { total_usd: number; voice_minutes: number; camera_minutes: number } }[] }

export default function CostPanel() {
  const tick = useLiveTick(["flags", "session", "voice"]);
  const { data, reload } = useFetch<Overview>("/api/costs", [tick]);
  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (data) setForm(data.projection.settings); }, [data]);
  if (!data) return null;
  const p = data.projection;
  const save = async () => { setSaving(true); try { await api.post("/api/site-settings", form); reload(); } finally { setSaving(false); } };
  const field = "h-10 w-24 px-2.5 rounded-[7px] bg-paper border border-rule-strong text-[15px] outline-none focus:border-teal";
  const saved = JSON.stringify(form) === JSON.stringify(p.settings);
  return (
    <Panel title="Running cost and cost controls" hint="Nothing streams all day. An agent exists only while someone is in a session, pauses itself after silence, and the camera can be on demand. Estimates use public list prices; your contract decides the real bill.">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {[["Per active voice minute", `$${p.per_active_minute_usd.toFixed(3)}`], ["Per worker per shift", `$${p.per_shift_usd.toFixed(2)}`], ["Per worker per month", `$${p.per_month_usd.toFixed(2)}`],
          ["If streamed all 8 h shift", `$${p.always_on_8h_shift_usd.toFixed(2)}`]].map(([l, v], i) => (
          <div key={l} className={cx("rounded-xl border p-4", i === 3 ? "border-red/40" : "border-rule")}>
            <div className="label">{l}</div><div className="mt-2 text-[30px] font-semibold tracking-[-0.04em] nameplate" style={{ color: i === 3 ? "var(--red)" : undefined }}>{v}</div>
          </div>
        ))}
      </div>
      <p className="text-[13px] text-pencil -mt-2 mb-4">Assumes {p.assumptions}.</p>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="grid gap-3 text-[14px]">
          <h3 className="text-[15px] font-bold">Controls</h3>
          <label className="flex items-center justify-between gap-3">Pause the agent after this many minutes of silence (0 = never)<input type="number" min={0} max={30} step={1} value={form.idle_pause_min ?? ""} onChange={(e) => setForm({ ...form, idle_pause_min: e.target.value })} className={field} /></label>
          <div className="flex items-center justify-between gap-3"><span>Camera</span>
            <span className="flex gap-1">{[["always", "Always on"], ["on_demand", "On demand"]].map(([v, l]) => (
              <button key={v} onClick={() => setForm({ ...form, camera_mode: v })} aria-pressed={form.camera_mode === v} className={cx("h-10 px-3 rounded-[7px] border text-[14px]", form.camera_mode === v ? "border-teal text-teal bg-teal/10" : "border-rule-strong text-ink-2")}>{l}</button>))}</span></div>
          <p className="text-[13px] text-pencil -mt-1">On demand: the camera stays off (billed as audio) until the worker taps Show camera, then turns off after 60 s.</p>
          <label className="flex items-center justify-between gap-3">Active voice minutes per worker per shift (for the projection)<input type="number" min={1} max={480} value={form.active_min_per_shift ?? ""} onChange={(e) => setForm({ ...form, active_min_per_shift: e.target.value })} className={field} /></label>
          <label className="flex items-center justify-between gap-3">Share of those minutes with the camera on, when on demand<input type="number" min={0} max={1} step={0.05} value={form.camera_share ?? ""} onChange={(e) => setForm({ ...form, camera_share: e.target.value })} className={field} /></label>
          <div><Btn kind="primary" onClick={save} disabled={saving || saved}>{saving ? "Saving…" : saved ? "Saved" : "Save controls"}</Btn></div>
        </div>
        <div>
          <h3 className="text-[15px] font-bold mb-2">Rates used</h3>
          <table className="w-full text-[13px]"><tbody>{p.rates.map((r) => (
            <tr key={r.key} className="border-t border-rule align-top"><td className="py-1.5 pr-2">{r.label}<div className="text-pencil">{r.source}</div></td><td className="py-1.5 text-right whitespace-nowrap">${r.value} <span className="text-pencil">{r.unit}</span></td></tr>))}</tbody></table>
          <p className="text-[12px] text-pencil mt-2">Override any rate in backend/.env (for example COST_CONVOAI_PER_MIN) to match your contract.</p>
        </div>
      </div>

      {data.sessions.length > 0 && (
        <div className="mt-6">
          <h3 className="text-[15px] font-bold mb-2">Recent sessions (measured)</h3>
          <table className="w-full text-[14px]"><tbody>{data.sessions.map((s) => (
            <tr key={s.session_id} className="border-t border-rule"><td className="py-2">{s.session_id}</td><td className="py-2 text-ink-2">{s.technician} on {s.asset_id}</td><td className="py-2 text-pencil">{s.cost.voice_minutes} voice min, {s.cost.camera_minutes} camera</td><td className="py-2 text-right font-semibold">${s.cost.total_usd.toFixed(3)}</td></tr>))}</tbody></table>
        </div>
      )}
    </Panel>
  );
}

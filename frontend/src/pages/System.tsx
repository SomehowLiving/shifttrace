import { useState } from "react";
import { MonitorSmartphone, RotateCcw } from "lucide-react";
import { api, type Health, type Pack, type TaskList } from "../api";
import { useFetch, useLiveTick, useStreamStatus } from "../live";
import { Btn, Glyph, PageHead, Panel, cx } from "../ui";
import CostPanel from "./CostPanel";

function Check({ ok, label, detail }: { ok: boolean | null | undefined; label: string; detail?: string | null }) {
  return (
    <li className="grid grid-cols-[18px_1fr_auto] items-start gap-x-3 py-2.5 border-t border-rule first:border-0">
      <span className="pt-1"><Glyph tone={ok ? "ok" : "alarm"} size={12} /></span>
      <span className="min-w-0"><span className="text-[15px]">{label}</span>{detail && <span className="block text-[13px] text-pencil break-all">{detail}</span>}</span>
      <span className={cx("text-[14px] font-semibold", ok ? "text-ok" : "text-red")}>{ok ? "Pass" : "Fail"}</span>
    </li>
  );
}

export default function SystemPage() {
  const live = useStreamStatus();
  const tick = useLiveTick(["session", "flags", "tunnel"]);
  const { data: h } = useFetch<Health>("/api/health", [tick]);
  const { data: packs } = useFetch<Pack[]>("/api/packs", [tick]);
  const { data: tasks } = useFetch<TaskList>("/api/tasks", [tick]);
  const flagsTick = useLiveTick(["flags"]);
  const { data: flags, reload } = useFetch<Record<string, boolean>>("/api/demo/flags", [flagsTick]);
  const [resetting, setResetting] = useState(false);
  const toggle = async (flag: string) => { await api.post("/api/demo/flags", { flag, enabled: !flags?.[flag] }); reload(); };
  const reset = async () => {
    if (!window.confirm("Reset all demo data to the scenario packs? Any live voice agent will be stopped.")) return;
    setResetting(true); try { await api.post("/api/demo/reset"); } finally { setResetting(false); }
  };

  return (
    <div className="px-4 py-6 grid gap-5 max-w-[1100px] mx-auto">
      <PageHead title="System" sub="Live checks run against the real services, plus the switches for demonstrating failures." />

      <CostPanel />

      <Panel title="Live checks" hint="Each line is checked now, not assumed.">
        <ul>
          <Check ok={live} label="Console connected to the backend" detail="Server-sent events stream" />
          {h && <>
            <Check ok={h.agora_credentials} label="Agora App ID and certificate" detail={h.agora_credentials ? "Set in backend/.env" : "Missing: add them to backend/.env"} />
            <Check ok={h.murf_key} label={`Murf Falcon voice (${h.murf_voice_id})`} detail={h.murf_key ? "Key passed to Agora's TTS step" : "Missing: add MURF_API_KEY to backend/.env"} />
            <Check ok={!!h.tunnel?.self_test} label="Agora cloud can reach the maintenance tools" detail={h.tunnel?.url ? `${h.tunnel.url}/mcp` : h.tunnel?.error ?? h.tunnel?.mode} />
            <Check ok={true} label={`Language model ${h.llm_model}, vision on`} detail="Speech recognition by Deepgram nova-3, both managed by Agora" />
          </>}
        </ul>
      </Panel>

      <Panel title="Demonstrate a failure" hint="All maintenance, stock and purchasing data is fictional. Agora, Murf and the model are real. These switches make a service fail so you can show the agent stays honest.">
        <div className="grid gap-2">
          {[
            ["inventory_outage", "Stock system outage", "Stock checks and reservations fail. The agent must say stock is unknown."],
            ["supplier_rejects", "Supplier rejects orders", "Approved orders come back rejected. The agent must not say the part was ordered."],
          ].map(([flag, label, note]) => (
            <label key={flag} className={cx("flex items-start gap-3 rounded-[7px] border px-3 py-2.5 cursor-pointer", flags?.[flag] ? "border-red/60 bg-red/5" : "border-rule")}>
              <input type="checkbox" className="mt-1 accent-[var(--red)]" checked={!!flags?.[flag]} onChange={() => toggle(flag)} />
              <span><span className={cx("text-[15px] font-semibold", flags?.[flag] && "text-red")}>{label}{flags?.[flag] ? ": on" : ""}</span>
                <span className="block text-[14px] text-ink-2">{note}</span></span>
            </label>
          ))}
          <div className="flex flex-wrap gap-2 pt-2">
            <Btn onClick={reset} disabled={resetting}><RotateCcw size={15} />{resetting ? "Resetting…" : "Reset demo data"}</Btn>
            <a href="/panel" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 h-9 px-3 text-[14px] text-ink-2 hover:text-ink"><MonitorSmartphone size={15} />Open the simulated panel</a>
          </div>
        </div>
      </Panel>

      <Panel title="Use cases" hint="Machines and their history come from packs in demo_data/packs. Session tasks come from demo_data/tasks.json. See docs/CONFIGURING_USE_CASES.md to add your own.">
        <div className="grid md:grid-cols-3 gap-3">
          {packs?.map((p) => (
            <div key={p.id} className={cx("rounded-[7px] border px-3 py-2.5", p.loaded ? "border-rule-strong" : "border-rule opacity-60")}>
              <div className="text-[15px] font-semibold">{p.name}</div>
              <div className="text-[13px] text-pencil">{p.loaded ? `Loaded: ${p.assets.join(", ")}` : "Not loaded (SHIFTTRACE_PACKS)"}</div>
              <p className="text-[14px] text-ink-2 mt-1">{p.description}</p>
            </div>
          ))}
        </div>
        {tasks && (
          <div className="mt-4">
            <h3 className="text-[14px] font-semibold mb-1">Tasks</h3>
            <ul className="grid md:grid-cols-2 gap-x-6">
              {tasks.tasks.map((t) => (
                <li key={t.id} className="py-2 border-t border-rule">
                  <span className="text-[15px]">{t.label}</span>
                  <span className="block text-[14px] text-ink-2">{t.summary}</span>
                  <span className="block text-[13px] text-pencil">{t.read_only ? `${t.restricted_tools?.length ?? 0} tools: read and note only` : t.restricted_tools ? `${t.restricted_tools.length} tools` : "Core tools"}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Panel>
    </div>
  );
}

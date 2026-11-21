// Simulated controller panel (fictional equipment) for the camera to look at during a demo or test.
// Driven by the asset's metadata.panel in its data pack, so every machine gets its own panel:
//   /panel            -> first asset that defines a panel (C-204 in the default packs)
//   /panel/CV-310     -> that asset's panel
// Optional URL state: ?alarm=<index>&lamps=a,b&flash=c&<readingKey>=<value>  e.g. /panel?alarm=3&temp=96&vib=2.6&lamps=run,load
// Show it on a second screen / phone; tap lamps and values to change the scene.
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import QRCode from "qrcode";
import { api, type Asset } from "../api";

type Lamp = "off" | "on" | "flash";
interface Reading { key: string; label: string; unit: string; value: number; step: number; min: number; max: number; decimals: number }
interface PanelSpec { title: string; subtitle: string; lamps: { key: string; label: string; color: string }[]; lit: string[]; alarms: string[]; readings: Reading[] }

function initial(spec: PanelSpec) {
  const q = new URLSearchParams(window.location.search);
  const lit = q.get("lamps")?.split(",") ?? spec.lit;
  const flash = q.get("flash")?.split(",") ?? [];
  const lamps: Record<string, Lamp> = {};
  for (const l of spec.lamps) lamps[l.key] = flash.includes(l.key) ? "flash" : lit.includes(l.key) ? "on" : "off";
  const values: Record<string, number> = {};
  for (const r of spec.readings) values[r.key] = q.has(r.key) ? Number(q.get(r.key)) : r.value;
  return { lamps, alarm: Number(q.get("alarm") ?? 0) % spec.alarms.length, values };
}

export default function PanelSim() {
  const { assetId } = useParams();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    const load = assetId
      ? api.get<{ asset: Asset }>(`/api/assets/${encodeURIComponent(assetId)}`).then((h) => h.asset)
      : api.get<Asset[]>("/api/assets").then((all) => all.find((a) => a.asset_id === "C-204" && a.metadata?.panel) ?? all.find((a) => a.metadata?.panel) ?? null);
    load.then((a) => (a?.metadata?.panel ? setAsset(a) : setErr(`No simulated panel is defined for ${assetId ?? "any asset"} (metadata.panel in its pack).`)))
      .catch((e) => setErr(String(e?.message ?? e)));
  }, [assetId]);
  if (err) return <div className="min-h-screen bg-[#2b2f33] text-white p-6">{err}</div>;
  if (!asset) return <div className="min-h-screen bg-[#2b2f33]" />;
  return <Panel asset={asset} spec={asset.metadata.panel as unknown as PanelSpec} />;
}

function Panel({ asset, spec }: { asset: Asset; spec: PanelSpec }) {
  const init = useState(() => initial(spec))[0];
  const [lamps, setLamps] = useState<Record<string, Lamp>>(init.lamps);
  const [alarm, setAlarm] = useState(init.alarm);
  const [values, setValues] = useState<Record<string, number>>(init.values);
  const [blinkOn, setBlinkOn] = useState(true);
  const qr = useRef<HTMLCanvasElement>(null);
  const qrText = String(asset.metadata.qr ?? `SHIFTTRACE:${asset.asset_id}`);

  useEffect(() => { const t = setInterval(() => setBlinkOn((b) => !b), 550); return () => clearInterval(t); }, []);
  useEffect(() => { if (qr.current) QRCode.toCanvas(qr.current, qrText, { width: 132, margin: 1, color: { dark: "#000", light: "#fff" } }); }, [qrText]);

  const cycle = (k: string) => setLamps((l) => ({ ...l, [k]: l[k] === "off" ? "on" : l[k] === "on" ? "flash" : "off" }));
  const bump = (r: Reading) => setValues((v) => {
    const next = Math.round((v[r.key] + r.step) * 10 ** r.decimals) / 10 ** r.decimals;
    return { ...v, [r.key]: next > r.max ? r.min : next };
  });
  // Flashing alternates bright/dim, never fully dark: Agora samples camera frames, and a
  // frame caught in a dark phase would make the lamp look off to the model.
  const lit = (s: Lamp) => s !== "off";
  const dim = (s: Lamp) => s === "flash" && !blinkOn;

  return (
    <div className="min-h-screen bg-[#2b2f33] flex items-center justify-center p-4 select-none" style={{ fontFamily: "Arial, Helvetica, sans-serif" }}>
      <div className="w-full max-w-[1000px] rounded-lg p-6 shadow-2xl" style={{ background: "linear-gradient(#d9dcdf,#bfc4c8)", border: "6px solid #8e9499" }}>
        <div className="flex items-start justify-between gap-6">
          <div className="min-w-0">
            <div className="text-[#1d2a36] text-3xl font-black tracking-wide">{spec.title}</div>
            <div className="text-[#1d2a36] text-lg font-bold">{spec.subtitle}</div>
            <div className="text-[#4b5560] text-xs mt-1">SIMULATED PANEL FOR SHIFTTRACE DEMO · FICTIONAL EQUIPMENT</div>
          </div>
          <div className="bg-white p-2 rounded text-center shrink-0">
            <canvas ref={qr} />
            <div className="text-[11px] font-bold text-black">ASSET {asset.asset_id}</div>
          </div>
        </div>

        <div className="mt-5 rounded-md p-5" style={{ background: "#0d1a12", border: "4px solid #222" }}>
          <button onClick={() => setAlarm((a) => (a + 1) % spec.alarms.length)} className="block w-full text-left">
            <div className="text-[#7dff9b] text-[44px] leading-none font-mono font-bold tracking-wider" style={{ textShadow: "0 0 8px rgba(125,255,155,.5)" }}>
              {spec.alarms[alarm]}
            </div>
          </button>
          <div className={`mt-4 grid gap-4 font-mono text-[#7dff9b]`} style={{ gridTemplateColumns: `repeat(${Math.max(1, spec.readings.length)}, minmax(0, 1fr))` }}>
            {spec.readings.map((r) => (
              <button key={r.key} onClick={() => bump(r)} className="text-left min-w-0">
                <div className="text-sm opacity-80">{r.label}</div>
                <div className="text-[56px] leading-none font-bold whitespace-nowrap">{values[r.key].toFixed(r.decimals)} {r.unit}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 grid gap-4" style={{ gridTemplateColumns: `repeat(${spec.lamps.length}, minmax(0, 1fr))` }}>
          {spec.lamps.map((l) => (
            <button key={l.key} onClick={() => cycle(l.key)} className="flex flex-col items-center gap-2">
              <span className="w-20 h-20 rounded-full border-[5px] border-[#3c4146]" style={{
                background: lit(lamps[l.key]) ? l.color : "#3a3f44", opacity: dim(lamps[l.key]) ? 0.55 : 1,
                boxShadow: lit(lamps[l.key]) ? `0 0 28px 6px ${l.color}aa, inset 0 -6px 12px rgba(0,0,0,.25)` : "inset 0 4px 10px rgba(0,0,0,.5)",
              }} />
              <span className="text-[#1d2a36] font-black text-lg tracking-wide text-center">{l.label}</span>
            </button>
          ))}
        </div>
        <div className="mt-4 text-[11px] text-[#4b5560]">Tap a lamp to cycle off / on / flashing. Tap the alarm text or a reading to change it.</div>
      </div>
    </div>
  );
}

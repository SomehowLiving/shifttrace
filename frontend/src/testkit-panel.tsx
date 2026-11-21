// Test feed controls for the live session: what the camera shows (right column) and the next recorded line to say
// as the technician (bottom bar). Items come from demo_data/testkit.json for this machine and task.
import { useEffect, useRef, useState } from "react";
import { ChevronUp, Play, Volume2 } from "lucide-react";
import { useFetch } from "./live";
import { testFeed, type Line, type Scene, type TestKit } from "./testfeed";
import { cx } from "./ui";

const SETTLE_MS = 4500; // frames reach the model a few seconds late (measured in live runs): hold the scene before asking

export function useTestKit(assetId: string, taskId: string | null | undefined, enabled: boolean) {
  const { data: kit } = useFetch<TestKit>(enabled ? `/api/testkit?asset_id=${encodeURIComponent(assetId)}${taskId ? `&task_id=${encodeURIComponent(taskId)}` : ""}` : null, []);
  const [scene, setScene] = useState<string | null>(testFeed.scene);
  const [busy, setBusy] = useState<string | null>(null);
  const [said, setSaid] = useState<string[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const first = useRef(true);

  const show = async (s: Scene | null) => {
    setErr(null);
    try { await testFeed.show(s); setScene(s?.id ?? null); } catch (e) { setErr(`Could not show that scene: ${(e as Error).message}`); }
  };
  // Start on this machine's own panel so the camera is never just black.
  useEffect(() => {
    if (kit && first.current && !testFeed.scene && kit.scenes[0]) { first.current = false; void show(kit.scenes[0]); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kit]);

  const say = async (l: Line) => {
    setBusy(l.id); setErr(null);
    try {
      if (l.scene && testFeed.scene !== l.scene) {
        const s = kit?.scenes.find((x) => x.id === l.scene);
        if (s) { await show(s); setBusy(`${l.id}:hold`); await new Promise((r) => setTimeout(r, SETTLE_MS)); setBusy(l.id); }
      }
      await testFeed.say(l.url);
      setSaid((p) => [...p, l.id]);
    } catch (e) { setErr(`Could not play that line: ${(e as Error).message}`); }
    finally { setBusy(null); }
  };
  const next = kit?.lines.find((l) => !said.includes(l.id)) ?? null;
  return { kit, scene, show, say, busy, said, next, err };
}
export type TestKitState = ReturnType<typeof useTestKit>;

export function SceneStrip({ t }: { t: TestKitState }) {
  if (!t.kit) return null;
  return (
    <div className="grid gap-1.5">
      <div className="flex items-baseline justify-between"><span className="text-[13px] font-bold text-violet">Test feed: the camera shows</span></div>
      <div className="flex gap-1.5 overflow-x-auto pb-1" role="radiogroup" aria-label="Camera scene">
        {t.kit.scenes.map((s) => (
          <button key={s.id} role="radio" aria-checked={t.scene === s.id} onClick={() => t.show(s)} disabled={!!t.busy} title={s.label}
            className={cx("shrink-0 w-[92px] grid gap-1 text-left rounded-[7px] border p-1 text-[11px] leading-tight", t.scene === s.id ? "border-violet bg-violet/10 text-ink" : "border-rule text-pencil hover:border-rule-strong")}>
            {s.kind === "image" ? <img src={s.url} alt="" className="w-full aspect-[16/10] object-cover rounded-2xl" /> : <span className="w-full aspect-[16/10] rounded-2xl bg-black text-white text-[11px] flex items-center justify-center">video</span>}
            <span className="line-clamp-2">{s.label}</span>
          </button>
        ))}
        <button role="radio" aria-checked={t.scene === null} onClick={() => t.show(null)} disabled={!!t.busy}
          className={cx("shrink-0 w-[92px] rounded-[7px] border p-1 text-[11px]", t.scene === null ? "border-violet bg-violet/10 text-ink" : "border-rule text-pencil")}>
          <span className="w-full aspect-[16/10] rounded-2xl bg-black block mb-1" />Covered
        </button>
      </div>
    </div>
  );
}

/** Bottom-bar control: say the next scripted line, or pick any line from the list. */
export function NextLine({ t, ready }: { t: TestKitState; ready: boolean }) {
  const [open, setOpen] = useState(false);
  if (!t.kit) return null;
  const n = t.next;
  return (
    <div className="relative min-w-0 flex items-center gap-2">
      <button onClick={() => n && t.say(n)} disabled={!ready || !!t.busy || !n} data-line-next={n?.id}
        className="min-w-0 h-12 pl-3 pr-4 rounded-[7px] border border-violet/60 bg-violet/10 hover:bg-violet/15 text-left flex items-center gap-2.5">
        {t.busy ? <Volume2 size={18} className="text-violet shrink-0" /> : <Play size={18} className="text-violet shrink-0" />}
        <span className="min-w-0">
          <span className="block text-[12px] text-violet font-bold">{t.busy?.endsWith(":hold") ? "Holding the camera on the panel…" : t.busy ? "Saying…" : n ? `Test feed: say line ${t.kit.lines.indexOf(n) + 1} of ${t.kit.lines.length}` : "All lines said"}</span>
          <span className="block text-[14px] truncate max-w-[34ch]">{n ? `“${n.text}”` : "Pick any line again from the list"}</span>
        </span>
      </button>
      <button onClick={() => setOpen(!open)} aria-expanded={open} title="All test lines" className="h-12 w-10 rounded-[7px] border border-rule hover:border-rule-strong flex items-center justify-center text-pencil"><ChevronUp size={18} /></button>
      {open && (
        <div className="absolute bottom-14 right-0 z-50 w-[min(460px,92vw)] max-h-[60vh] overflow-y-auto bg-sheet border border-rule-strong rounded-[7px] shadow-2xl p-2">
          <p className="text-[13px] text-pencil px-2 py-1">Each line plays as your voice. Lines marked with a scene switch the camera first.</p>
          <ol>
            {t.kit.lines.map((l, i) => (
              <li key={l.id}>
                <button onClick={() => { setOpen(false); void t.say(l); }} disabled={!ready || !!t.busy} data-line={l.id}
                  className={cx("w-full grid grid-cols-[24px_1fr] gap-x-2 text-left rounded-[7px] px-2 py-1.5 hover:bg-ink/[0.05]", t.said.includes(l.id) && "opacity-60")}>
                  <span className="text-[13px] text-pencil pt-0.5">{i + 1}</span>
                  <span className="text-[14px]"><span className="text-blue">“{l.text}”</span>
                    {l.scene && <span className="block text-[12px] text-violet">shows {t.kit!.scenes.find((s) => s.id === l.scene)?.label}</span>}
                    {l.note && <span className="block text-[12px] text-pencil">{l.note}</span>}</span>
                </button>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

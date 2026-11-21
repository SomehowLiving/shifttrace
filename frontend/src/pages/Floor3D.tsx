// "Shifttrace on the floor": a 3D illustration of a worker using Shifttrace on a plant floor, for judges and first
// visitors. Procedural low-poly scene, one story loop, a caption bar and a guided camera the viewer can take over.
// Illustration only; every name and number in it is synthetic demo data.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Canvas } from "@react-three/fiber";
import { ArrowLeft, ChevronLeft, ChevronRight, Compass, Pause, Play, RotateCcw } from "lucide-react";
import type { Clock } from "../floor3d/models";
import { PALETTES, Scene, type SceneApi } from "../floor3d/Scene";
import { LOOP, STEPS } from "../floor3d/story";
import { cx } from "../ui";

function useReducedMotion() {
  const q = "(prefers-reduced-motion: reduce)";
  const [reduced, setReduced] = useState(() => typeof window !== "undefined" && window.matchMedia(q).matches);
  useEffect(() => {
    const m = window.matchMedia(q);
    const f = () => setReduced(m.matches);
    m.addEventListener("change", f);
    return () => m.removeEventListener("change", f);
  }, []);
  return reduced;
}

function usePageHidden() {
  const [hidden, setHidden] = useState(() => typeof document !== "undefined" && document.visibilityState === "hidden");
  useEffect(() => {
    const f = () => setHidden(document.visibilityState === "hidden");
    document.addEventListener("visibilitychange", f);
    return () => document.removeEventListener("visibilitychange", f);
  }, []);
  return hidden;
}

function useTheme(): "dark" | "light" {
  const read = (): "dark" | "light" => (typeof document !== "undefined" && document.documentElement.dataset.theme === "light" ? "light" : "dark");
  const [theme, setTheme] = useState(read);
  useEffect(() => {
    const o = new MutationObserver(() => setTheme(read()));
    o.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => o.disconnect();
  }, []);
  return theme;
}

export default function Floor3D({ className, backHref = "/" }: {
  /** Size of the view. Defaults to the full viewport height; pass e.g. "h-full" inside a sized container. */
  className?: string;
  /** Where the back link goes; null hides it (e.g. inside the console shell). */
  backHref?: string | null;
}) {
  const reduced = useReducedMotion();
  const hidden = usePageHidden();
  const theme = useTheme();
  const [accent, setAccent] = useState<string | undefined>(undefined);
  useEffect(() => { setAccent(getComputedStyle(document.documentElement).getPropertyValue("--teal").trim() || undefined); }, [theme]);
  const palette = useMemo(() => ({ ...PALETTES[theme], accent }), [theme, accent]);
  const clock = useRef<Clock>({ t: reduced ? STEPS[0].key : 0, playing: !reduced, tour: true, snap: reduced, jumpFrames: 4 });
  const api = useRef<SceneApi>({ invalidate: () => {} });
  const progress = useRef<HTMLDivElement>(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(!reduced);
  const [tour, setTour] = useState(true);

  // Reduced motion switched on mid-way: stop and show the current step's key moment.
  useEffect(() => {
    const c = clock.current;
    c.snap = reduced;
    if (reduced) { c.playing = false; setPlaying(false); c.t = STEPS[step].key; c.jumpFrames = 8; api.current.invalidate(); }
  }, [reduced]);

  const onStep = useCallback((i: number) => setStep(i), []);
  const onUserOrbit = useCallback(() => { clock.current.tour = false; setTour(false); }, []);

  const jump = (i: number) => {
    const c = clock.current;
    const n = (i + STEPS.length) % STEPS.length;
    c.t = c.playing ? STEPS[n].start + 0.01 : STEPS[n].key;
    c.jumpFrames = 8;
    setStep(n);
    api.current.invalidate();
  };
  const togglePlay = () => {
    const c = clock.current;
    c.playing = !c.playing;
    if (c.playing && c.t >= LOOP - 0.2) c.t = 0;
    setPlaying(c.playing);
    api.current.invalidate();
  };
  const restart = () => {
    const c = clock.current;
    c.t = c.playing ? 0 : STEPS[0].key;
    c.tour = true;
    c.jumpFrames = 8;
    setTour(true);
    setStep(0);
    api.current.invalidate();
  };
  const resumeTour = () => { clock.current.tour = true; clock.current.jumpFrames = 2; setTour(true); api.current.invalidate(); };

  const s = STEPS[step];
  const frameloop = hidden ? "never" : !playing && reduced ? "demand" : "always";

  return (
    <div className={cx("relative w-full overflow-hidden bg-paper text-ink isolate", className ?? "h-[100dvh]")}>
      <div className="absolute inset-0" aria-hidden>
        <Canvas
          frameloop={frameloop} dpr={[1, 1.5]} shadows
          camera={{ fov: 42, near: 0.1, far: 120, position: [6, 6, 10] }}
          gl={{ antialias: true, powerPreference: "high-performance" }}
        >
          <Scene clock={clock} api={api} palette={palette} progress={progress} onStep={onStep} onUserOrbit={onUserOrbit} damping={!reduced} />
        </Canvas>
      </div>

      {/* top bar */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-30 flex items-start justify-between gap-3 p-4 sm:p-5">
        <div className="pointer-events-auto min-w-0 -ml-2.5 -mt-1.5 rounded-lg bg-paper/55 px-2.5 py-1.5 backdrop-blur-sm">
          {backHref !== null && (
            <Link to={backHref} className="mb-1.5 inline-flex items-center gap-1 text-[12px] text-pencil hover:text-ink no-underline">
              <ArrowLeft size={13} aria-hidden />Shifttrace
            </Link>
          )}
          <h1 className="m-0 text-[17px] sm:text-[20px] font-semibold leading-tight tracking-tight">Shifttrace on the floor</h1>
          <p className="m-0 mt-0.5 text-[12px] text-pencil">Illustration. Synthetic data.</p>
        </div>
        {!tour && (
          <button type="button" onClick={resumeTour}
            className="pointer-events-auto inline-flex h-8 shrink-0 items-center gap-1.5 rounded-full border border-teal/60 bg-sheet/90 px-3 text-[12px] font-semibold text-teal backdrop-blur hover:bg-sheet">
            <Compass size={14} aria-hidden />Resume tour
          </button>
        )}
      </div>

      {/* caption bar */}
      <div className="absolute inset-x-0 bottom-0 z-30 p-3 sm:p-5 pointer-events-none">
        <div className="pointer-events-auto mx-auto max-w-[760px] rounded-xl border border-rule bg-sheet/92 px-3 py-2.5 sm:px-4 sm:py-3 shadow-[0_20px_50px_-20px_rgba(0,0,0,.7)] backdrop-blur">
          <div className="flex items-start gap-3">
            <div className="min-w-0 flex-1" aria-live="polite">
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-[11px] text-pencil">{step + 1}/{STEPS.length}</span>
                <span className="text-[14px] sm:text-[15px] font-semibold text-ink leading-tight">{s.title}</span>
              </div>
              <p className="m-0 mt-0.5 text-[12px] sm:text-[13px] leading-snug text-ink-2">{s.line}</p>
            </div>
            <div className="flex shrink-0 items-center gap-1">
              {reduced && (
                <button type="button" onClick={() => jump(step - 1)} aria-label="Previous step"
                  className="grid h-8 w-8 place-items-center rounded-full border border-rule text-ink-2 hover:text-ink hover:bg-ink/5"><ChevronLeft size={15} /></button>
              )}
              <button type="button" onClick={togglePlay} aria-label={playing ? "Pause" : "Play"} title={playing ? "Pause" : "Play"}
                className="grid h-8 w-8 place-items-center rounded-full bg-teal text-[var(--on-accent,var(--paper))] hover:opacity-90">
                {playing ? <Pause size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" className="translate-x-px" />}
              </button>
              {reduced ? (
                <button type="button" onClick={() => jump(step + 1)} aria-label="Next step"
                  className="grid h-8 w-8 place-items-center rounded-full border border-rule text-ink-2 hover:text-ink hover:bg-ink/5"><ChevronRight size={15} /></button>
              ) : (
                <button type="button" onClick={restart} aria-label="Restart" title="Restart"
                  className="grid h-8 w-8 place-items-center rounded-full border border-rule text-ink-2 hover:text-ink hover:bg-ink/5"><RotateCcw size={14} /></button>
              )}
            </div>
          </div>
          {/* step dots: one segment per step, sized by its share of the loop */}
          <div className="mt-2.5 flex gap-1" role="group" aria-label="Story steps">
            {STEPS.map((st, i) => (
              <button key={st.id} type="button" onClick={() => jump(i)} aria-label={`Step ${i + 1}: ${st.title}`} aria-current={i === step ? "step" : undefined}
                title={st.title} className="group relative h-4 min-w-0 flex-1 py-1.5" style={{ flexGrow: st.end - st.start }}>
                <span className="block h-1 w-full overflow-hidden rounded-full bg-rule-strong/60 group-hover:bg-rule-strong">
                  {i < step && <span className="block h-full w-full bg-teal/70" />}
                  {i === step && <span ref={progress} className="block h-full bg-teal" style={{ width: reduced && !playing ? "100%" : "0%" }} />}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

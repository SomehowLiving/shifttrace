// Everything inside the <Canvas>: lights, floor, machines, the worker, overlays, the story clock and the guided camera.
import { memo, useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Grid, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { ACCENT, AirHandler, Beams, Compressor, Conveyor, Rack, ScreenBody, Shell, Worker, type ClockRef } from "./models";
import { AgentSays, Chips, EvidenceCard, HandoffScreen, MachineTag, OrderCard, Pin, ScanCard, WorkerSays } from "./overlays";
import { cueKey, LOOP, PLACES, shotAt, stepAt, STEPS, type Shot } from "./story";

export type Palette = { bg: string; floor: string; wall: string; trim: string; cell: string; section: string; light: boolean; accent?: string };

export const PALETTES: Record<"dark" | "light", Palette> = {
  dark: { bg: "#0a0d10", floor: "#1a2128", wall: "#1f272e", trim: "#27353b", cell: "#26313a", section: "#3a4853", light: false },
  light: { bg: "#e7ecea", floor: "#d9dfdd", wall: "#c9d1cf", trim: "#f7fbfa", cell: "#bfc8c6", section: "#93a0a3", light: true },
};

export type SceneApi = { invalidate: () => void };

type Props = {
  clock: ClockRef;
  api: RefObject<SceneApi>;
  palette: Palette;
  progress: RefObject<HTMLDivElement | null>;
  onStep: (i: number) => void;
  onUserOrbit: () => void;
  damping: boolean;
};

export const Scene = memo(function Scene({ clock, api, palette, progress, onStep, onUserOrbit, damping }: Props) {
  const workerRoot = useRef<THREE.Group>(null);
  const lens = useRef<THREE.Object3D>(null);
  useEffect(() => { if (palette.accent) { ACCENT.set(palette.accent); api.current.invalidate(); } }, [palette.accent, api]);
  return (
    <>
      <Director clock={clock} api={api} progress={progress} onStep={onStep} />
      <color attach="background" args={[palette.bg]} />
      <fog attach="fog" args={[palette.bg, 26, 60]} />
      <hemisphereLight args={[palette.light ? "#ffffff" : "#cfe0f0", palette.light ? "#b9c2c0" : "#1a2026", palette.light ? 1.2 : 1.5]} />
      <directionalLight
        position={[9, 15, 8]} intensity={palette.light ? 1.8 : 2.2} castShadow
        shadow-mapSize={[1024, 1024]} shadow-camera-left={-17} shadow-camera-right={17} shadow-camera-top={13} shadow-camera-bottom={-13}
        shadow-camera-near={1} shadow-camera-far={50} shadow-bias={-0.0006}
      />
      <pointLight position={[-4.2, 2.6, -1.4]} color="#f26b61" intensity={2.2} distance={4.5} decay={2} />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -0.5]} receiveShadow>
        <planeGeometry args={[30, 15.4]} />
        <meshStandardMaterial color={palette.floor} roughness={0.95} />
      </mesh>
      <Grid
        position={[0, 0.004, -0.5]} args={[30, 15.4]} cellSize={1} cellThickness={0.6} sectionSize={4} sectionThickness={1}
        cellColor={palette.cell} sectionColor={palette.section} fadeDistance={48} fadeStrength={1.2} followCamera={false} infiniteGrid={false}
      />
      <Shell wall={palette.wall} trim={palette.trim} />
      <Compressor clock={clock} />
      <Conveyor />
      <Rack clock={clock} />
      <AirHandler />
      <ScreenBody clock={clock} />
      <Worker clock={clock} root={workerRoot} lens={lens} />
      <Beams clock={clock} lens={lens} />
      <Overlays clock={clock} workerRoot={workerRoot} />
      <CameraRig clock={clock} workerRoot={workerRoot} />
      <OrbitControls
        makeDefault enableDamping={damping} dampingFactor={0.08} minDistance={3} maxDistance={32} maxPolarAngle={Math.PI * 0.47}
        enablePan onStart={onUserOrbit}
      />
    </>
  );
});

/** Advances the story clock, reports step changes and drives the caption's progress fill without React re-renders. */
function Director({ clock, api, progress, onStep }: Pick<Props, "clock" | "api" | "progress" | "onStep">) {
  const invalidate = useThree((s) => s.invalidate);
  api.current.invalidate = invalidate;
  const last = useRef(-1);
  useFrame((_, dt) => {
    const c = clock.current;
    if (c.playing) {
      c.t += Math.min(dt, 0.1);
      if (c.t >= LOOP) { c.t -= LOOP; c.jumpFrames = Math.max(c.jumpFrames, 2); }
    }
    const i = stepAt(c.t);
    if (i !== last.current) { last.current = i; onStep(i); }
    const el = progress.current;
    if (el) {
      const { start, end } = STEPS[i];
      el.style.width = `${Math.min(100, ((c.t - start) / (end - start)) * 100).toFixed(1)}%`;
    }
    if (c.jumpFrames > 0) { c.jumpFrames--; invalidate(); }
  });
  return null;
}

const _p = new THREE.Vector3();
const _t = new THREE.Vector3();
const UP = new THREE.Vector3(0, 1, 0);

type Controls = { target: THREE.Vector3; update: () => void };

/** The guided tour: eases the camera towards the current step's shot until the viewer grabs the controls. */
function CameraRig({ clock, workerRoot }: { clock: ClockRef; workerRoot: RefObject<THREE.Group | null> }) {
  const controls = useThree((s) => s.controls) as unknown as Controls | null;
  const shot = useMemo<Shot>(() => ({ pos: [0, 0, 0], target: [0, 0, 0], lean: 0 }), []);
  const first = useRef(true);
  useFrame(({ camera, size }, dt) => {
    const c = clock.current;
    const w = workerRoot.current;
    if (!c.tour || !controls || !w) return;
    const aspect = size.width / Math.max(1, size.height);
    const stretch = aspect < 1.25 ? 1 + (1.25 - aspect) * 0.95 : 1;
    shotAt(c.t, w.position.x, w.position.z, stretch, shot);
    if (aspect < 1 && shot.lean !== 0) {
      // Slide camera and target sideways together (screen-left), so the worker sits right of centre.
      _t.set(...shot.target).sub(_p.set(...shot.pos)).cross(UP).normalize().multiplyScalar(-(1 - aspect) * 1.7 * shot.lean);
      for (let i = 0; i < 3; i++) { const d = _t.getComponent(i); shot.pos[i] += d; shot.target[i] += d; }
    }
    const k = c.snap || first.current || c.jumpFrames > 0 && !c.playing ? 1 : 1 - Math.exp(-Math.min(dt, 0.1) * 1.5);
    first.current = false;
    camera.position.lerp(_p.set(...shot.pos), k);
    controls.target.lerp(_t.set(...shot.target), k);
    controls.update();
  });
  return null;
}

/** Copies the worker's position each frame so screen-space overlays can ride along with them. */
function FollowWorker({ workerRoot, children }: { workerRoot: RefObject<THREE.Group | null>; children: ReactNode }) {
  const g = useRef<THREE.Group>(null);
  useFrame(() => { if (g.current && workerRoot.current) g.current.position.copy(workerRoot.current.position); });
  return <group ref={g}>{children}</group>;
}

function Overlays({ clock, workerRoot }: { clock: ClockRef; workerRoot: RefObject<THREE.Group | null> }) {
  const [key, setKey] = useState(() => cueKey(clock.current.t));
  const keyRef = useRef(key);
  // Html roots are mounted once, a few frames in (after R3F has connected its event target), and then only their content
  // changes. Mounting/unmounting drei <Html> while the scene renders races React 19's root unmount.
  const [ready, setReady] = useState(false);
  const size = useThree((s) => s.size);
  const frames = useRef(0);
  useFrame(() => {
    if (!ready && ++frames.current > 2) setReady(true);
    const k = cueKey(clock.current.t);
    if (k !== keyRef.current) { keyRef.current = k; setKey(k); }
  });
  if (!ready) return null;
  const set = new Set(key.split(","));
  const has = (id: string) => set.has(id);
  const received = Number([...set].find((s) => /^i\d$/.test(s))?.slice(1) ?? 0);
  const step = stepAt(clock.current.t);
  const narrow = size.width < 640;
  const head: [number, number, number] = [0, 1.95, 0];
  return (
    <>
      <FollowWorker workerRoot={workerRoot}>
        <Pin show={has("bubbleAsk")} position={head} side="tl"><WorkerSays text="C-204 is running hot again." /></Pin>
        <Pin show={has("bubbleYes")} position={head} side="tl"><WorkerSays text="Yes, order it." /></Pin>
        <Pin show={has("bubbleHandoff")} position={head} side="tl"><WorkerSays text="That's it for C-204. Hand over." /></Pin>
        <Pin show={has("bubbleAgent")} position={head} side="tl">
          <AgentSays text="Discharge is 108 °C, limit is 105. Last month the same alarm came from a clogged cooler." />
        </Pin>
        <Pin show={has("chipHistory") || has("chipManual") || has("chipStock")} position={[0, 1.1, 0]} side="l" className="pr-10">
          <Chips history={has("chipHistory")} historyOk={has("hv")} manual={has("chipManual")} manualOk={has("md")} stock={has("chipStock")} />
        </Pin>
        <Pin show={has("orderCard")} position={narrow ? [0, 0.5, 0] : [0, 0.95, 0]} side={narrow ? "l" : "r"} className={narrow ? "pr-6" : "pl-8"}><OrderCard stamped={has("st")} /></Pin>
      </FollowWorker>
      <Pin show={has("evidence")} position={[PLACES.gauge[0] - 0.3, PLACES.gauge[1] + 0.25, PLACES.gauge[2]]} side="tl"><EvidenceCard /></Pin>
      <Pin show={has("scanCard")} position={[PLACES.binLabel[0], PLACES.binLabel[1] + 0.35, PLACES.binLabel[2]]} side={narrow ? "tl" : "tr"}><ScanCard /></Pin>
      <HandoffScreen lit={has("screenOn")} received={has("screenOn") ? received : 0} />
      <MachineTag show={step === 0 || step >= 6} position={[-4.5, 2.35, -3]} id="C-204" name="Air compressor" state="hot" />
      <MachineTag position={[8.5, 2.0, -5]} id="CV-310" name="Packaging conveyor" />
      <MachineTag position={[-10, 5.0, -5.6]} id="AHU-3" name="Rooftop air handler" />
      <MachineTag show={!has("scanCard")} position={[7.5, 3.75, 3]} id="DC2" name="Warehouse racks" />
    </>
  );
}

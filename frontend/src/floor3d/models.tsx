// Procedural low-poly models for the floor view. Primitives only: no downloaded models, textures or brand assets.
import { useMemo, useRef, type ReactNode, type RefObject } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { MOMENTS, on, PLACES, workerPose } from "./story";

export type Clock = { t: number; playing: boolean; tour: boolean; snap: boolean; jumpFrames: number };
export type ClockRef = RefObject<Clock>;

/** The console's brand accent (read from the --teal token by the page), shared by every glowing part of the scene. */
export const ACCENT = new THREE.Color("#c8f135");
const _dim = new THREE.Color();
const GLASS_OFF = new THREE.Color("#0b1014");

/* ---------- shared materials (one instance each keeps draw state cheap) ---------- */

function useMats() {
  return useMemo(() => {
    const std = (color: string, extra: Partial<THREE.MeshStandardMaterialParameters> = {}) =>
      new THREE.MeshStandardMaterial({ color, roughness: 0.75, metalness: 0.1, flatShading: true, ...extra });
    return {
      steel: std("#5f6b75", { metalness: 0.45, roughness: 0.5 }),
      darkSteel: std("#2b333a", { metalness: 0.4, roughness: 0.6 }),
      tank: std("#3f6f86", { metalness: 0.3, roughness: 0.55 }),
      motor: std("#2f3d47"),
      copper: std("#b8743f", { metalness: 0.6, roughness: 0.4 }),
      white: std("#e8ecee", { roughness: 0.4 }),
      belt: std("#16191c", { roughness: 0.9 }),
      kraft: std("#b08a5a"),
      kraft2: std("#9c7748"),
      upright: std("#2d64a8"),
      beam: std("#d8742c"),
      binBlue: std("#3a7bd5"),
      binGrey: std("#7c8791"),
      binRed: std("#c0473b"),
      ahu: std("#a9b3ba", { metalness: 0.3 }),
      hiVis: std("#d6f23c", { roughness: 0.6 }),
      reflect: std("#e6ebef", { roughness: 0.2, metalness: 0.6, emissive: "#555b60" }),
      navy: std("#26324a"),
      shirt: std("#33435e"),
      skin: std("#b98058"),
      hat: std("#f2c230", { roughness: 0.45 }),
      black: std("#111417"),
      boot: std("#3a2a1e"),
    };
  }, []);
}
type Mats = ReturnType<typeof useMats>;

/* ---------- C-204 air compressor ---------- */

export function Compressor({ clock }: { clock: ClockRef }) {
  const m = useMats();
  const needle = useRef<THREE.Group>(null);
  const beacon = useRef<THREE.MeshBasicMaterial>(null);
  const flash = useRef<THREE.MeshBasicMaterial>(null);
  const [cx, cz] = PLACES.compressor;
  useFrame(({ clock: c }) => {
    const e = c.elapsedTime;
    // Needle sits in the red: 108 °C on a dial whose limit mark is 105.
    if (needle.current) needle.current.rotation.z = -1.62 + Math.sin(e * 3.1) * 0.03 + Math.sin(e * 7.3) * 0.015;
    if (beacon.current) beacon.current.color.set(Math.sin(e * 5) > 0 ? "#f26b61" : "#5a1f1b");
    if (flash.current) {
      const t = clock.current.t;
      const k = t >= 20 && t < 20.6 ? 1 - (t - 20) / 0.6 : 0;
      flash.current.opacity = k * 0.9;
    }
  });
  return (
    <group position={[cx, 0, cz]}>
      {/* skid */}
      <mesh material={m.darkSteel} position={[0, 0.08, 0]} castShadow receiveShadow><boxGeometry args={[3.2, 0.16, 1.5]} /></mesh>
      {/* receiver tank on saddles */}
      <mesh material={m.tank} position={[0, 0.78, -0.1]} rotation={[0, 0, Math.PI / 2]} castShadow><cylinderGeometry args={[0.52, 0.52, 2.5, 14]} /></mesh>
      {[-1.25, 1.25].map((x) => (
        <mesh key={x} material={m.tank} position={[x, 0.78, -0.1]} scale={[0.25, 1, 1]} castShadow><sphereGeometry args={[0.52, 12, 8]} /></mesh>
      ))}
      {[-0.8, 0.8].map((x) => (
        <mesh key={x} material={m.darkSteel} position={[x, 0.32, -0.1]}><boxGeometry args={[0.18, 0.34, 0.9]} /></mesh>
      ))}
      {/* motor + pump head on top */}
      <mesh material={m.motor} position={[-0.55, 1.5, -0.1]} rotation={[0, 0, Math.PI / 2]} castShadow><cylinderGeometry args={[0.28, 0.28, 0.8, 10]} /></mesh>
      {[-0.42, -0.62, -0.82].map((x) => (
        <mesh key={x} material={m.darkSteel} position={[x, 1.5, -0.1]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.3, 0.3, 0.03, 10]} /></mesh>
      ))}
      <mesh material={m.steel} position={[0.45, 1.52, -0.1]} castShadow><boxGeometry args={[0.6, 0.46, 0.5]} /></mesh>
      <mesh material={m.steel} position={[0.45, 1.85, -0.1]}><boxGeometry args={[0.5, 0.18, 0.4]} /></mesh>
      {/* belt guard */}
      <mesh material={m.beam} position={[0, 1.5, 0.27]}><boxGeometry args={[1.0, 0.5, 0.08]} /></mesh>
      {/* discharge pipe to the aftercooler (the part that clogs) */}
      <mesh material={m.copper} position={[0.75, 1.75, -0.1]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.05, 0.05, 0.5, 8]} /></mesh>
      <mesh material={m.copper} position={[1.0, 1.35, -0.1]}><cylinderGeometry args={[0.05, 0.05, 0.8, 8]} /></mesh>
      <group position={[1.35, 1.0, -0.1]}>
        <mesh material={m.darkSteel} castShadow><boxGeometry args={[0.4, 0.9, 0.7]} /></mesh>
        {[-0.3, -0.15, 0, 0.15, 0.3].map((y) => (
          <mesh key={y} material={m.steel} position={[0.21, y, 0]}><boxGeometry args={[0.02, 0.05, 0.6]} /></mesh>
        ))}
      </group>
      {/* control panel with the discharge-temperature gauge, facing the aisle */}
      <group position={[PLACES.gauge[0] - cx, 0, 0.55]}>
        <mesh material={m.darkSteel} position={[0, 0.75, 0]}><boxGeometry args={[0.08, 1.5, 0.08]} /></mesh>
        <mesh material={m.white} position={[0, 1.42, 0.04]} castShadow><boxGeometry args={[0.62, 0.5, 0.12]} /></mesh>
        <group position={[0, 1.42, PLACES.gauge[2] - cz - 0.55]}>
          <mesh material={m.darkSteel} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.17, 0.17, 0.04, 20]} /></mesh>
          <mesh position={[0, 0, 0.021]}><circleGeometry args={[0.15, 24]} /><meshBasicMaterial color="#f4f1e8" /></mesh>
          {/* red zone */}
          <mesh position={[0, 0, 0.022]}><ringGeometry args={[0.11, 0.145, 16, 1, -0.785, 1.135]} /><meshBasicMaterial color="#d23b2f" /></mesh>
          <mesh position={[0, 0, 0.022]}><ringGeometry args={[0.11, 0.145, 24, 1, 0.35, 3.58]} /><meshBasicMaterial color="#9aa3a7" /></mesh>
          <group ref={needle} position={[0, 0, 0.026]}>
            <mesh position={[0, 0.06, 0]}><boxGeometry args={[0.012, 0.13, 0.004]} /><meshBasicMaterial color="#111" /></mesh>
          </group>
          <mesh position={[0, 0, 0.03]}><circleGeometry args={[0.035, 24]} /><meshBasicMaterial ref={flash} color="#ffffff" transparent opacity={0} depthWrite={false} /></mesh>
        </group>
        <mesh position={[0.2, 1.6, 0.11]}><boxGeometry args={[0.06, 0.06, 0.02]} /><meshBasicMaterial ref={beacon} color="#f26b61" /></mesh>
      </group>
      {/* alarm beacon on top */}
      <mesh position={[0.45, 2.05, -0.1]}><cylinderGeometry args={[0.07, 0.07, 0.14, 8]} /><meshBasicMaterial color="#f2a93b" /></mesh>
      {/* floor hazard outline */}
      <HazardOutline w={4.2} d={2.6} y={0.012} />
    </group>
  );
}

function HazardOutline({ w, d, y }: { w: number; d: number; y: number }) {
  const t = 0.08;
  const c = "#c9a227";
  return (
    <group position={[0, y, 0]}>
      {[[0, -d / 2, w, t], [0, d / 2, w, t], [-w / 2, 0, t, d], [w / 2, 0, t, d]].map(([x, z, a, b], i) => (
        <mesh key={i} position={[x, 0, z]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[a, b]} /><meshBasicMaterial color={c} transparent opacity={0.6} /></mesh>
      ))}
    </group>
  );
}

/* ---------- CV-310 packaging conveyor ---------- */

export function Conveyor() {
  const m = useMats();
  const boxes = useRef<THREE.Group>(null);
  const len = 9;
  const [cx, cz] = PLACES.conveyor;
  useFrame((_, dt) => {
    const g = boxes.current;
    if (!g) return;
    for (const b of g.children) {
      b.position.x += Math.min(dt, 0.1) * 0.7;
      if (b.position.x > len / 2 - 0.3) b.position.x -= len - 0.6;
    }
  });
  const rollers = useMemo(() => Array.from({ length: 18 }, (_, i) => -len / 2 + 0.25 + i * (len - 0.5) / 17), []);
  return (
    <group position={[cx, 0, cz]}>
      {[-0.42, 0.42].map((z) => (
        <mesh key={z} material={m.steel} position={[0, 0.86, z]} castShadow><boxGeometry args={[len, 0.12, 0.06]} /></mesh>
      ))}
      <mesh material={m.belt} position={[0, 0.88, 0]} receiveShadow><boxGeometry args={[len - 0.1, 0.04, 0.8]} /></mesh>
      {rollers.filter((_, i) => i % 3 === 0).map((x) => (
        <group key={x} position={[x, 0, 0]}>
          {[-0.4, 0.4].map((z) => (<mesh key={z} material={m.darkSteel} position={[0, 0.42, z]}><boxGeometry args={[0.06, 0.84, 0.06]} /></mesh>))}
        </group>
      ))}
      {/* motor drive and guard at the head end */}
      <mesh material={m.motor} position={[len / 2 - 0.3, 0.6, 0.6]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.16, 0.16, 0.4, 10]} /></mesh>
      <mesh material={m.beam} position={[len / 2 - 0.3, 0.9, 0.5]}><boxGeometry args={[0.5, 0.3, 0.1]} /></mesh>
      {/* status stack light: green, running */}
      <mesh material={m.darkSteel} position={[-len / 2 + 0.3, 1.3, -0.5]}><cylinderGeometry args={[0.025, 0.025, 0.9, 6]} /></mesh>
      <mesh position={[-len / 2 + 0.3, 1.78, -0.5]}><cylinderGeometry args={[0.06, 0.06, 0.12, 8]} /><meshBasicMaterial color="#36d1b0" /></mesh>
      <group ref={boxes}>
        {Array.from({ length: 6 }, (_, i) => (
          <mesh key={i} material={i % 2 ? m.kraft : m.kraft2} position={[-len / 2 + 0.6 + i * 1.45, 1.08 + (i % 3) * 0.02, (i % 2) * 0.08 - 0.04]}
            rotation={[0, (i % 3) * 0.08, 0]} castShadow>
            <boxGeometry args={[0.5 + (i % 3) * 0.08, 0.36 + (i % 2) * 0.08, 0.45]} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

/* ---------- DC2 warehouse rack with bins ---------- */

export function Rack({ clock }: { clock: ClockRef }) {
  const m = useMats();
  const glow = useRef<THREE.MeshBasicMaterial>(null);
  const [rx, rz] = PLACES.rack;
  const depth = 1.0, length = 5.4, height = 3.2;
  useFrame(() => {
    if (!glow.current) return;
    const t = clock.current.t;
    glow.current.opacity = t >= 43.6 && t < 48 ? 0.5 : 0;
    glow.current.color.copy(ACCENT);
  });
  const levels = [0.15, 1.0, 1.85, 2.7];
  const bays = [-1.8, -0.6, 0.6, 1.8];
  const binMats = [m.binBlue, m.binGrey, m.binRed, m.binBlue];
  return (
    <group position={[rx, 0, rz]}>
      {[-length / 2, -length / 6, length / 6, length / 2].map((z) =>
        [-depth / 2, depth / 2].map((x) => (
          <mesh key={`${z}${x}`} material={m.upright} position={[x + depth / 2 - 0.0, height / 2, z]} castShadow><boxGeometry args={[0.08, height, 0.08]} /></mesh>
        )),
      )}
      {levels.map((y) => (
        <group key={y}>
          {[0, depth].map((x) => (<mesh key={x} material={m.beam} position={[x, y, 0]}><boxGeometry args={[0.07, 0.1, length]} /></mesh>))}
          <mesh material={m.darkSteel} position={[depth / 2, y + 0.06, 0]} receiveShadow><boxGeometry args={[depth, 0.02, length]} /></mesh>
        </group>
      ))}
      {levels.slice(0, 3).map((y, li) =>
        bays.map((z, bi) => (
          <group key={`${li}${bi}`} position={[0.35, y + 0.27, z]}>
            {[-0.3, 0.3].map((dz) => (
              <mesh key={dz} material={binMats[(li + bi + (dz > 0 ? 1 : 0)) % 4]} position={[0, 0, dz]} castShadow><boxGeometry args={[0.5, 0.38, 0.5]} /></mesh>
            ))}
          </group>
        )),
      )}
      {/* bin C-03 label (white) and the highlight when it is scanned */}
      <mesh position={[PLACES.binLabel[0] - rx, PLACES.binLabel[1], PLACES.binLabel[2] - rz]} rotation={[0, -Math.PI / 2, 0]}>
        <planeGeometry args={[0.3, 0.12]} /><meshBasicMaterial color="#f4f6f5" />
      </mesh>
      {[-0.06, -0.03, 0, 0.03, 0.06].map((dz, i) => (
        <mesh key={dz} position={[PLACES.binLabel[0] - rx - 0.002, PLACES.binLabel[1], PLACES.binLabel[2] - rz + dz]} rotation={[0, -Math.PI / 2, 0]}>
          <planeGeometry args={[i % 2 ? 0.008 : 0.016, 0.07]} /><meshBasicMaterial color="#111" />
        </mesh>
      ))}
      <mesh position={[PLACES.binLabel[0] - rx - 0.004, PLACES.binLabel[1], PLACES.binLabel[2] - rz]} rotation={[0, -Math.PI / 2, 0]}>
        <planeGeometry args={[0.62, 0.46]} /><meshBasicMaterial ref={glow} transparent opacity={0} depthWrite={false} />
      </mesh>
      {/* aisle sign */}
      <mesh position={[-0.05, height + 0.25, 0]} rotation={[0, -Math.PI / 2, 0]}><planeGeometry args={[0.9, 0.35]} /><meshBasicMaterial color="#2d64a8" /></mesh>
    </group>
  );
}

/* ---------- AHU-3 rooftop air handler, on a mezzanine ---------- */

export function AirHandler() {
  const m = useMats();
  const fans = useRef<THREE.Group>(null);
  const [ax, az] = PLACES.ahu;
  useFrame((_, dt) => { if (fans.current) for (const f of fans.current.children) f.rotation.y += Math.min(dt, 0.1) * 6; });
  const deck = 2.6;
  return (
    <group position={[ax, 0, az]}>
      {[[-2.2, -1.6], [2.2, -1.6], [-2.2, 1.6], [2.2, 1.6]].map(([x, z]) => (
        <mesh key={`${x}${z}`} material={m.darkSteel} position={[x, deck / 2, z]}><boxGeometry args={[0.14, deck, 0.14]} /></mesh>
      ))}
      <mesh material={m.steel} position={[0, deck, 0]} receiveShadow castShadow><boxGeometry args={[4.8, 0.14, 3.6]} /></mesh>
      {/* railing */}
      <mesh material={m.beam} position={[0, deck + 0.55, 1.78]}><boxGeometry args={[4.8, 0.05, 0.05]} /></mesh>
      {[-2.3, -0.8, 0.8, 2.3].map((x) => (<mesh key={x} material={m.beam} position={[x, deck + 0.28, 1.78]}><boxGeometry args={[0.05, 0.55, 0.05]} /></mesh>))}
      {/* ladder */}
      <group position={[2.6, 0, 1.0]}>
        {[-0.22, 0.22].map((z) => (<mesh key={z} material={m.beam} position={[0, deck / 2 + 0.3, z]}><boxGeometry args={[0.05, deck + 0.6, 0.05]} /></mesh>))}
        {Array.from({ length: 8 }, (_, i) => (<mesh key={i} material={m.beam} position={[0, 0.3 + i * 0.32, 0]}><boxGeometry args={[0.04, 0.04, 0.44]} /></mesh>))}
      </group>
      {/* the unit */}
      <group position={[0, deck + 0.07, -0.2]}>
        <mesh material={m.ahu} position={[0, 0.85, 0]} castShadow><boxGeometry args={[3.4, 1.7, 1.9]} /></mesh>
        {[-0.5, -0.25, 0, 0.25, 0.5].map((y) => (<mesh key={y} material={m.darkSteel} position={[-1.0, 0.85 + y, 0.96]}><boxGeometry args={[1.1, 0.06, 0.03]} /></mesh>))}
        <mesh material={m.darkSteel} position={[0.9, 0.85, 0.96]}><boxGeometry args={[0.9, 1.2, 0.03]} /></mesh>
        <group ref={fans}>
          {[-0.8, 0.8].map((x) => (
            <group key={x} position={[x, 1.75, 0]}>
              {[0, 1, 2].map((k) => (<mesh key={k} material={m.darkSteel} rotation={[0, (k * Math.PI) / 3, 0]}><boxGeometry args={[0.9, 0.03, 0.12]} /></mesh>))}
            </group>
          ))}
        </group>
        {[-0.8, 0.8].map((x) => (<mesh key={x} material={m.steel} position={[x, 1.72, 0]}><torusGeometry args={[0.5, 0.04, 6, 16]} /></mesh>))}
        {/* duct into the back wall */}
        <mesh material={m.steel} position={[0, 0.9, -1.6]}><boxGeometry args={[1.0, 0.7, 1.4]} /></mesh>
      </group>
    </group>
  );
}

/* ---------- building shell ---------- */

export function Shell({ wall, trim }: { wall: string; trim: string }) {
  const m = useMats();
  const wallMat = useMemo(() => new THREE.MeshStandardMaterial({ color: wall, roughness: 0.95, flatShading: true }), [wall]);
  return (
    <group>
      <mesh material={wallMat} position={[0, 3.2, -8.1]} receiveShadow><boxGeometry args={[30, 6.4, 0.2]} /></mesh>
      <mesh material={wallMat} position={[-15, 3.2, -0.5]} receiveShadow><boxGeometry args={[0.2, 6.4, 15.4]} /></mesh>
      {/* clerestory light strips */}
      {[-10, -4, 6, 12].map((x) => (
        <mesh key={x} position={[x, 5.5, -7.98]}><planeGeometry args={[4, 0.5]} /><meshBasicMaterial color={trim} /></mesh>
      ))}
      {/* steel columns */}
      {[-8, 4.2, 13].map((x) => (
        <group key={x} position={[x, 3.2, -7.7]}>
          <mesh material={m.darkSteel}><boxGeometry args={[0.35, 6.4, 0.12]} /></mesh>
          <mesh material={m.darkSteel} position={[0, 0, 0.15]}><boxGeometry args={[0.08, 6.4, 0.3]} /></mesh>
        </group>
      ))}
      {/* walkway lines: the aisle the worker uses */}
      <AisleLines />
    </group>
  );
}

function AisleLines() {
  const segs: [number, number, number, number][] = [
    [-1.8, 1.5, 0.08, 13], // x, z, w, d
    [1.8, 1.5, 0.08, 13],
    [3.8, 3, 1, 0.08],
  ];
  return (
    <group position={[0, 0.011, 0]}>
      {segs.map(([x, z, w, d], i) => (
        <mesh key={i} position={[x, 0, z]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[w, d]} /><meshBasicMaterial color="#c9a227" transparent opacity={0.45} /></mesh>
      ))}
    </group>
  );
}

/* ---------- handoff screen on the back wall (the 3D part; its content is an Html overlay) ---------- */

export function ScreenBody({ clock }: { clock: ClockRef }) {
  const glass = useRef<THREE.MeshBasicMaterial>(null);
  const rings = useRef<THREE.Group>(null);
  useFrame(() => {
    const t = clock.current.t;
    const lit = on("screenOn", t);
    if (glass.current) glass.current.color.copy(GLASS_OFF).lerp(ACCENT, lit ? 0.018 : 0); // linear space: a little goes a long way
    const g = rings.current;
    if (g) {
      g.children.forEach((r, i) => {
        const k = lit ? ((t - MOMENTS.integrationsFrom + 0.5 + i * 0.7) % 2.1) / 2.1 : -1;
        r.visible = k >= 0 && t > MOMENTS.integrationsFrom - 0.5;
        r.scale.setScalar(1 + Math.max(0, k) * 0.7);
        const mat = (r as THREE.Mesh).material as THREE.MeshBasicMaterial;
        mat.opacity = (1 - Math.max(0, k)) * 0.35;
        mat.color.copy(ACCENT);
      });
    }
  });
  const [sx, sy, sz] = PLACES.screen;
  return (
    <group position={[sx, sy, sz]}>
      <mesh position={[0, 0, -0.05]}><boxGeometry args={[3.5, 2.05, 0.1]} /><meshStandardMaterial color="#1b2228" roughness={0.6} /></mesh>
      <mesh position={[0, 0, 0.005]}><planeGeometry args={[3.3, 1.86]} /><meshBasicMaterial ref={glass} color="#0b1014" /></mesh>
      <group ref={rings} position={[0, 0, 0.02]} scale={[1.17, 0.66, 1]}>
        {[0, 1, 2].map((i) => (
          <mesh key={i} visible={false}>
            <ringGeometry args={[1.95, 2.0, 4, 1, Math.PI / 4]} />
            <meshBasicMaterial transparent opacity={0} depthWrite={false} />
          </mesh>
        ))}
      </group>
      {/* bracket */}
      <mesh position={[0, -1.2, -0.05]}><boxGeometry args={[0.2, 0.35, 0.1]} /><meshStandardMaterial color="#1b2228" /></mesh>
    </group>
  );
}

/* ---------- camera cone (device → gauge) and scan laser (device → label) ---------- */

const _a = new THREE.Vector3();
const _b = new THREE.Vector3();

export function Beams({ clock, lens }: { clock: ClockRef; lens: RefObject<THREE.Object3D | null> }) {
  const cone = useRef<THREE.Mesh>(null);
  const frame = useRef<THREE.Mesh>(null);
  const laser = useRef<THREE.Mesh>(null);
  const sweep = useRef<THREE.Mesh>(null);
  const coneGeo = useMemo(() => {
    const g = new THREE.ConeGeometry(0.32, 1, 4, 1, true);
    g.translate(0, -0.5, 0);
    g.rotateX(-Math.PI / 2); // apex at origin, base towards +z
    g.rotateZ(Math.PI / 4);
    return g;
  }, []);
  const laserGeo = useMemo(() => new THREE.BoxGeometry(0.012, 0.012, 1).translate(0, 0, 0.5), []);
  useFrame(({ clock: c }) => {
    const t = clock.current.t;
    const L = lens.current;
    if (!L) return;
    L.getWorldPosition(_a);
    const showCone = on("cone", t);
    if (cone.current) {
      cone.current.visible = showCone;
      if (showCone) {
        _b.set(...PLACES.gauge);
        cone.current.position.copy(_a);
        cone.current.lookAt(_b);
        const d = _a.distanceTo(_b);
        cone.current.scale.set(1, 1, d);
        const k = Math.min(1, (t - 19.2) / 0.5) * Math.min(1, (24.6 - t) / 0.4);
        (cone.current.material as THREE.MeshBasicMaterial).opacity = 0.16 * k;
      }
    }
    if (frame.current) {
      frame.current.visible = showCone;
      frame.current.rotation.z = Math.PI / 4 + (t < 20 ? (20 - t) * 1.2 : 0);
    }
    const showLaser = on("laser", t);
    if (laser.current) {
      laser.current.visible = showLaser;
      if (showLaser) {
        _b.set(PLACES.binLabel[0] - 0.01, PLACES.binLabel[1] + Math.sin(c.elapsedTime * 9) * 0.03, PLACES.binLabel[2]);
        laser.current.position.copy(_a);
        laser.current.lookAt(_b);
        laser.current.scale.set(1, 1, _a.distanceTo(_b));
      }
    }
    if (sweep.current) {
      sweep.current.visible = showLaser;
      sweep.current.position.y = PLACES.binLabel[1] + Math.sin(c.elapsedTime * 9) * 0.03;
    }
  });
  return (
    <group>
      <mesh ref={cone} geometry={coneGeo} visible={false}>
        <meshBasicMaterial color="#a693f5" transparent opacity={0.16} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {/* viewfinder diamond on the gauge: the violet "model reading" mark */}
      <mesh ref={frame} position={[PLACES.gauge[0], PLACES.gauge[1], PLACES.gauge[2] + 0.05]} visible={false}>
        <torusGeometry args={[0.27, 0.012, 4, 4]} />
        <meshBasicMaterial color="#a693f5" />
      </mesh>
      <mesh ref={laser} geometry={laserGeo} visible={false}><meshBasicMaterial color="#ff3b30" /></mesh>
      <mesh ref={sweep} position={[PLACES.binLabel[0] - 0.012, PLACES.binLabel[1], PLACES.binLabel[2]]} rotation={[0, -Math.PI / 2, 0]} visible={false}>
        <planeGeometry args={[0.34, 0.008]} /><meshBasicMaterial color="#ff3b30" />
      </mesh>
    </group>
  );
}

/* ---------- the worker ---------- */

const angleLerp = (a: number, b: number, k: number) => {
  let d = ((b - a + Math.PI) % (Math.PI * 2)) - Math.PI;
  if (d < -Math.PI) d += Math.PI * 2;
  return a + d * k;
};

export function Worker({ clock, root, lens, children }: {
  clock: ClockRef;
  root: RefObject<THREE.Group | null>;
  lens: RefObject<THREE.Object3D | null>;
  children?: ReactNode;
}) {
  const m = useMats();
  const body = useRef<THREE.Group>(null);
  const legL = useRef<THREE.Group>(null);
  const legR = useRef<THREE.Group>(null);
  const armL = useRef<THREE.Group>(null);
  const armR = useRef<THREE.Group>(null);
  const device = useRef<THREE.Group>(null);
  const mic = useRef<THREE.MeshBasicMaterial>(null);
  const led = useRef<THREE.MeshBasicMaterial>(null);
  const screen = useRef<THREE.MeshBasicMaterial>(null);
  const st = useRef({ heading: Math.PI, walk: 0, up: 0 });
  useFrame(({ clock: c }, dtRaw) => {
    const g = root.current;
    if (!g) return;
    const dt = Math.min(dtRaw, 0.1);
    const t = clock.current.t;
    const p = workerPose(t);
    const snap = clock.current.snap || clock.current.jumpFrames > 0;
    const s = st.current;
    const kTurn = snap ? 1 : 1 - Math.exp(-dt * 9);
    const kBlend = snap ? 1 : 1 - Math.exp(-dt * 6);
    s.heading = angleLerp(s.heading, p.heading, kTurn);
    s.walk += ((p.walking ? 1 : 0) - s.walk) * kBlend;
    s.up += ((p.deviceUp ? 1 : 0) - s.up) * kBlend;
    g.position.set(p.x, 0, p.z);
    g.rotation.y = s.heading;
    const phase = (p.dist / 1.25) * Math.PI * 2;
    const swing = Math.sin(phase) * 0.55 * s.walk;
    if (legL.current) legL.current.rotation.x = swing;
    if (legR.current) legR.current.rotation.x = -swing;
    if (armL.current) { armL.current.rotation.x = -swing * 0.8; armL.current.rotation.z = 0.08; }
    if (armR.current) {
      armR.current.rotation.x = swing * 0.8 * (1 - s.up) + -1.15 * s.up;
      armR.current.rotation.z = -0.08 * (1 - s.up) + 0.35 * s.up;
    }
    if (device.current) { device.current.rotation.x = 1.15 * s.up; device.current.rotation.z = -0.35 * s.up; }
    if (body.current) body.current.position.y = Math.abs(Math.sin(phase)) * 0.035 * s.walk + Math.sin(c.elapsedTime * 1.6) * 0.004;
    const talking = on("bubbleAsk", t) || on("bubbleYes", t) || on("bubbleHandoff", t);
    const agent = on("bubbleAgent", t) || (on("orderCard", t) && t < 30.4);
    if (mic.current) mic.current.color.set(talking ? (Math.sin(c.elapsedTime * 18) > 0 ? "#6aa6ff" : "#2c4d80") : "#1d2a33");
    if (led.current) led.current.color.copy(agent && Math.sin(c.elapsedTime * 12) < 0 ? _dim.copy(ACCENT).multiplyScalar(0.3) : ACCENT);
    if (screen.current) screen.current.color.copy(ACCENT);
  });
  return (
    <group ref={root}>
      <group ref={body}>
        {/* legs (pivot at the hip) */}
        {[[-0.1, legL], [0.1, legR]].map(([x, ref]) => (
          <group key={x as number} ref={ref as RefObject<THREE.Group | null>} position={[x as number, 0.9, 0]}>
            <mesh material={m.navy} position={[0, -0.42, 0]} castShadow><boxGeometry args={[0.16, 0.8, 0.18]} /></mesh>
            <mesh material={m.boot} position={[0, -0.85, 0.04]} castShadow><boxGeometry args={[0.18, 0.11, 0.28]} /></mesh>
          </group>
        ))}
        {/* torso, hi-vis vest with reflective bands */}
        <mesh material={m.shirt} position={[0, 1.18, 0]} castShadow><boxGeometry args={[0.42, 0.6, 0.23]} /></mesh>
        <mesh material={m.hiVis} position={[0, 1.2, 0]} castShadow><boxGeometry args={[0.45, 0.5, 0.26]} /></mesh>
        <mesh material={m.reflect} position={[0, 1.06, 0]}><boxGeometry args={[0.46, 0.045, 0.27]} /></mesh>
        <mesh material={m.reflect} position={[0, 1.3, 0]}><boxGeometry args={[0.46, 0.045, 0.27]} /></mesh>
        {/* head, hard hat, headset with boom mic */}
        <mesh material={m.skin} position={[0, 1.53, 0]}><boxGeometry args={[0.1, 0.08, 0.1]} /></mesh>
        <mesh material={m.skin} position={[0, 1.65, 0]} castShadow><sphereGeometry args={[0.13, 10, 8]} /></mesh>
        <mesh material={m.hat} position={[0, 1.7, 0]} castShadow><sphereGeometry args={[0.152, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2]} /></mesh>
        <mesh material={m.hat} position={[0, 1.7, 0.02]}><cylinderGeometry args={[0.19, 0.19, 0.02, 14]} /></mesh>
        <mesh material={m.black} position={[0, 1.66, -0.01]}><torusGeometry args={[0.145, 0.014, 4, 12, Math.PI]} /></mesh>
        {[-0.14, 0.14].map((x) => (
          <mesh key={x} material={m.black} position={[x, 1.64, 0]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.055, 0.055, 0.05, 10]} /></mesh>
        ))}
        <mesh position={[0.168, 1.64, 0]}><boxGeometry args={[0.01, 0.025, 0.025]} /><meshBasicMaterial ref={led} /></mesh>
        <mesh material={m.black} position={[-0.125, 1.585, 0.075]} rotation={[0.35, -0.5, 0]}><boxGeometry args={[0.014, 0.014, 0.16]} /></mesh>
        <mesh position={[-0.085, 1.555, 0.14]}><sphereGeometry args={[0.02, 6, 4]} /><meshBasicMaterial ref={mic} color="#1d2a33" /></mesh>
        {/* arms (pivot at the shoulder) */}
        <group ref={armL} position={[-0.28, 1.43, 0]}>
          <mesh material={m.hiVis} position={[0, -0.12, 0]}><boxGeometry args={[0.13, 0.22, 0.14]} /></mesh>
          <mesh material={m.shirt} position={[0, -0.38, 0]} castShadow><boxGeometry args={[0.11, 0.34, 0.12]} /></mesh>
          <mesh material={m.skin} position={[0, -0.6, 0]}><sphereGeometry args={[0.055, 6, 5]} /></mesh>
        </group>
        <group ref={armR} position={[0.28, 1.43, 0]}>
          <mesh material={m.hiVis} position={[0, -0.12, 0]}><boxGeometry args={[0.13, 0.22, 0.14]} /></mesh>
          <mesh material={m.shirt} position={[0, -0.38, 0]} castShadow><boxGeometry args={[0.11, 0.34, 0.12]} /></mesh>
          <mesh material={m.skin} position={[0, -0.6, 0]}><sphereGeometry args={[0.055, 6, 5]} /></mesh>
          {/* rugged handheld: screen faces the worker, camera lens faces the machine */}
          <group ref={device} position={[0, -0.64, 0.05]}>
            <mesh material={m.black} position={[0, 0.06, 0]} castShadow><boxGeometry args={[0.15, 0.22, 0.035]} /></mesh>
            <mesh position={[0, 0.07, -0.019]} rotation={[0, Math.PI, 0]}><planeGeometry args={[0.12, 0.16]} /><meshBasicMaterial ref={screen} /></mesh>
            <mesh material={m.beam} position={[0, -0.05, 0]}><boxGeometry args={[0.16, 0.03, 0.045]} /></mesh>
            <mesh material={m.darkSteel} position={[0.04, 0.14, 0.02]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.014, 0.014, 0.01, 8]} /></mesh>
            <object3D ref={lens} position={[0.04, 0.14, 0.03]} />
          </group>
        </group>
      </group>
      {children}
    </group>
  );
}

export type { Mats };

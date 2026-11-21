// The story loop for the 3D floor view: steps (for the caption bar), cues (what is on screen when) and the worker's
// path. Everything is a pure function of the loop time `t`, so jumping, pausing and reduced motion are all just "set t".
// All data is synthetic and mirrors the demo pack (C-204, PR-2001, FLT-OIL-75, H-0043).

export const LOOP = 57; // seconds

export type Step = { id: string; title: string; line: string; start: number; end: number; key: number };

export const STEPS: Step[] = [
  { id: "walk", title: "Walk to C-204", line: "A technician with a headset and a rugged handheld starts a voice session at the compressor.", start: 0, end: 6, key: 5.8 },
  { id: "ask", title: "Ask out loud", line: "No forms, no menus. The worker says what is wrong, hands still free for the machine.", start: 6, end: 10, key: 9.5 },
  { id: "tools", title: "Agent checks the record", line: "The voice agent (Agora Conversational AI, Murf Falcon voice) calls tools and answers from the machine's history.", start: 10, end: 18.5, key: 16.5 },
  { id: "camera", title: "Camera evidence", line: "The handheld's camera saves the gauge as evidence, labelled a model observation, never a diagnosis.", start: 18.5, end: 24, key: 22.5 },
  { id: "draft", title: "Draft, don't act", line: "No cooler kit on site, so the agent drafts PR-2001 and reads it back. Nothing is ordered yet.", start: 24, end: 30, key: 29 },
  { id: "yes", title: "Spoken yes", line: "Only the worker's own \"yes\" approves it. The write is re-read from the database before it is called verified.", start: 30, end: 37, key: 36 },
  { id: "scan", title: "Scan the part", line: "A barcode scan of the part label feeds the agent the SKU and bin, so the pick is logged against the job.", start: 37, end: 46.5, key: 45.5 },
  { id: "handoff", title: "Shift handoff", line: "The handoff is written for the next shift and lands in the team's chat, sheet and calendar.", start: 46.5, end: LOOP, key: 55.5 },
];

export function stepAt(t: number): number {
  for (let i = STEPS.length - 1; i >= 0; i--) if (t >= STEPS[i].start) return i;
  return 0;
}

/* ---------- cues: [from, to) windows in loop seconds ---------- */

export const CUES = {
  bubbleAsk: [6.3, 12.6],
  chipHistory: [10.2, 24],
  chipManual: [11.6, 24],
  bubbleAgent: [13, 19],
  cone: [19.2, 24.6],
  evidence: [20, 26],
  chipStock: [24.2, 30.4],
  orderCard: [25.4, 38],
  bubbleYes: [30.6, 34.6],
  laser: [43, 46.6],
  scanCard: [43.6, 48],
  bubbleHandoff: [47.2, 50.6],
  screenOn: [50.2, LOOP + 1],
} as const satisfies Record<string, readonly [number, number]>;

export type CueId = keyof typeof CUES;

/** Sub-moments inside a cue (a chip turning verified, the order being stamped, integrations receiving). */
export const MOMENTS = {
  historyVerified: 11.3,
  manualDone: 12.5,
  stamped: 33.8,
  integrationsFrom: 51.6,
  integrationsGap: 0.55,
} as const;

export const on = (id: CueId, t: number) => t >= CUES[id][0] && t < CUES[id][1];

/** Stable key of the cues visible at t (plus sub-moments) so React only re-renders when something actually changes. */
export function cueKey(t: number): string {
  const ids = (Object.keys(CUES) as CueId[]).filter((id) => on(id, t));
  const m = [
    t >= MOMENTS.historyVerified ? "hv" : "",
    t >= MOMENTS.manualDone ? "md" : "",
    t >= MOMENTS.stamped ? "st" : "",
    `i${Math.max(0, Math.min(5, Math.floor((t - MOMENTS.integrationsFrom) / MOMENTS.integrationsGap) + 1))}`,
  ];
  return [...ids, ...m].join(",");
}

/* ---------- the plant layout (metres, y up, the front of the floor faces +z) ---------- */

export const PLACES = {
  entrance: [1.5, 7.5] as V2,
  compressor: [-4.5, -3] as V2, // C-204 centre
  atCompressor: [-3.6, -0.8] as V2,
  gauge: [-3.95, 1.42, -2.33] as V3, // gauge face, world
  rack: [7, 3] as V2, // DC2 rack, front faces -x
  atRack: [5.6, 3.15] as V2,
  binLabel: [7.094, 1.24, 3.3] as V3, // label on bin C-03, world
  conveyor: [8.5, -5] as V2,
  ahu: [-10, -5.4] as V2,
  screen: [0.5, 3.1, -7.88] as V3,
  atScreen: [0.5, -5.6] as V2,
};

export type V2 = [number, number];
export type V3 = [number, number, number];

type Walk = { from: number; to: number; pts: V2[] };
type Stand = { from: number; to: number; at: V2; face: number; device: boolean };

const WALKS: Walk[] = [
  { from: 0, to: 6, pts: [PLACES.entrance, [-1, 3], PLACES.atCompressor] },
  { from: 37, to: 43, pts: [PLACES.atCompressor, [0.5, 1.2], PLACES.atRack] },
  { from: 46.8, to: 52.4, pts: [PLACES.atRack, [2.5, -1], PLACES.atScreen] },
];

// face: rotation about y, 0 = facing +z. Facing -z is PI, facing +x is PI/2.
const STANDS: Stand[] = [
  { from: 6, to: 37, at: PLACES.atCompressor, face: Math.PI, device: true },
  { from: 43, to: 46.8, at: PLACES.atRack, face: Math.PI / 2, device: true },
  { from: 52.4, to: LOOP + 1, at: PLACES.atScreen, face: Math.PI, device: true },
];

export type Pose = { x: number; z: number; heading: number; walking: boolean; dist: number; deviceUp: boolean };

const easeInOut = (u: number) => 0.5 - 0.5 * Math.cos(Math.PI * Math.min(1, Math.max(0, u)));

function polyLength(pts: V2[]) {
  let L = 0;
  for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return L;
}

/** Where the worker is at time t, which way they face and how far they have walked (drives the stride). */
export function workerPose(t: number): Pose {
  for (const w of WALKS) {
    if (t >= w.from && t < w.to) {
      const L = polyLength(w.pts);
      let s = easeInOut((t - w.from) / (w.to - w.from)) * L;
      const dist = s;
      for (let i = 1; i < w.pts.length; i++) {
        const [ax, az] = w.pts[i - 1];
        const [bx, bz] = w.pts[i];
        const seg = Math.hypot(bx - ax, bz - az);
        if (s <= seg || i === w.pts.length - 1) {
          const u = seg > 0 ? Math.min(1, s / seg) : 0;
          return { x: ax + (bx - ax) * u, z: az + (bz - az) * u, heading: Math.atan2(bx - ax, bz - az), walking: true, dist, deviceUp: false };
        }
        s -= seg;
      }
    }
  }
  for (const st of STANDS) {
    if (t >= st.from && t < st.to) return { x: st.at[0], z: st.at[1], heading: st.face, walking: false, dist: 0, deviceUp: st.device };
  }
  // Before the first walk starts (never, t starts at 0) or in a gap: stand at the entrance facing in.
  return { x: PLACES.entrance[0], z: PLACES.entrance[1], heading: Math.PI, walking: false, dist: 0, deviceUp: false };
}

/* ---------- guided camera ---------- */

export type Shot = { pos: V3; target: V3; lean: number };

/** The tour's camera for time t, given where the worker is. `stretch` pulls the camera back on portrait screens. */
export function shotAt(t: number, wx: number, wz: number, stretch: number, out: Shot): Shot {
  const step = STEPS[stepAt(t)].id;
  let tx: number, ty: number, tz: number, ox: number, oy: number, oz: number;
  const follow = () => { tx = wx; ty = 1.2; tz = wz; ox = 6.5; oy = 5; oz = 9; };
  out.lean = 1; // on narrow screens, push the worker right of centre so the overlays to their left stay on screen
  switch (step) {
    case "walk":
      if (t < 2.4) { tx = 2.5; ty = 0.5; tz = 0.2; ox = 8; oy = 11; oz = 15; out.lean = 0; } // establishing shot of the whole floor
      else follow();
      break;
    case "ask": case "tools": tx = -4.0; ty = 1.45; tz = -1.6; ox = 6.6; oy = 2.3; oz = 3.2; break;
    case "camera": tx = -3.85; ty = 1.4; tz = -1.6; ox = 5.6; oy = 1.7; oz = 2.6; break;
    case "draft": case "yes": tx = -4.0; ty = 1.35; tz = -1.6; ox = 6.4; oy = 2.1; oz = 3.6; break;
    case "scan":
      if (t < 42.4) follow();
      else { tx = 6.1; ty = 1.3; tz = 3; ox = -3.6; oy = 2.2; oz = 5.4; out.lean = -0.7; } // label is right of the worker
      break;
    default: // handoff
      if (t < 50.6) follow();
      else { tx = 0.5; ty = 2.4; tz = -7; ox = 4.2; oy = 1.6; oz = 9; out.lean = 0; }
  }
  out.target[0] = tx!; out.target[1] = ty!; out.target[2] = tz!;
  out.pos[0] = tx! + ox! * stretch; out.pos[1] = ty! + oy! * (0.6 + 0.4 * stretch); out.pos[2] = tz! + oz! * stretch;
  return out;
}

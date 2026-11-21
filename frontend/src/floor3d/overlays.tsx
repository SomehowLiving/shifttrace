// Html overlays for the floor view: speech, tool calls, evidence, the approval card, the scan and the handoff screen.
// Styled with the console's tokens (bg-sheet, border-rule, text-ink, teal = verified, violet = model, ochre = needs a person,
// blue = the technician) so the 3D view reads as the same product.
import type { CSSProperties, ReactNode } from "react";
import { Html } from "@react-three/drei";
import {
  AudioLines, BookOpen, Boxes, CalendarDays, Check, Database, FileSpreadsheet, MessageCircle, MessageSquare, Mic, ScanBarcode, Send, ShoppingCart,
} from "lucide-react";
import { cx } from "../ui";
import { PLACES, type V3 } from "./story";

type Side = "tl" | "tr" | "l" | "r" | "c" | "t";
const SHIFT: Record<Side, string> = {
  tl: "translate(-100%,-100%)", tr: "translate(0,-100%)", l: "translate(-100%,-50%)", r: "translate(0,-50%)", c: "translate(-50%,-50%)", t: "translate(-50%,-100%)",
};
const GAP: Record<Side, string> = { tl: "pr-2 pb-2", tr: "pl-2 pb-2", l: "pr-3", r: "pl-3", c: "", t: "pb-2" };

/** A screen-space overlay pinned to a 3D point. Never takes pointer events, so orbiting works through it. */
export function Pin({ position, side, children, className, show = true }: { position: V3; side: Side; children: ReactNode; className?: string; show?: boolean }) {
  return (
    <Html position={position} zIndexRange={[20, 0]} pointerEvents="none" wrapperClass="pointer-events-none select-none">
      {show && <div style={{ transform: SHIFT[side] }} className={cx("pointer-events-none", GAP[side], className)}>{children}</div>}
    </Html>
  );
}

const card = "rise rounded-lg border bg-sheet/95 shadow-[0_10px_30px_-10px_rgba(0,0,0,.6)] backdrop-blur-sm";
const width = "w-max max-w-[min(44vw,250px)]";

export function WorkerSays({ text }: { text: string }) {
  return (
    <div className={cx(card, width, "border-blue/60 rounded-br-sm px-2.5 py-1.5")}>
      <div className="flex items-center gap-1.5 text-[10px] font-semibold text-blue leading-tight"><Mic size={11} aria-hidden />Technician</div>
      <div className="text-[12px] sm:text-[13px] leading-snug text-ink">&ldquo;{text}&rdquo;</div>
    </div>
  );
}

export function AgentSays({ text }: { text: string }) {
  return (
    <div className={cx(card, "w-max max-w-[min(48vw,280px)] border-teal/50 rounded-br-sm px-2.5 py-1.5")}>
      <div className="flex items-center gap-1.5 text-[10px] font-semibold text-teal leading-tight">
        <AudioLines size={11} aria-hidden />Shifttrace<span className="font-normal text-pencil">· Murf Falcon voice</span>
      </div>
      <div className="text-[12px] sm:text-[13px] leading-snug text-ink">{text}</div>
    </div>
  );
}

export function ToolChip({ name, done, doneLabel, icon }: { name: string; done: boolean; doneLabel: string; icon: ReactNode }) {
  return (
    <div className={cx(card, "flex items-center gap-1.5 px-2 py-1 border-rule whitespace-nowrap")}>
      <span className="text-pencil">{icon}</span>
      <span className="font-mono text-[10.5px] sm:text-[11px] text-ink-2">{name}</span>
      {done
        ? <span className="inline-flex items-center gap-0.5 text-[10.5px] font-semibold text-green"><Check size={11} strokeWidth={3} aria-hidden />{doneLabel}</span>
        : <span className="think text-pencil text-[11px]"><span>.</span><span>.</span><span>.</span></span>}
    </div>
  );
}

export function Chips({ history, historyOk, manual, manualOk, stock }: { history: boolean; historyOk: boolean; manual: boolean; manualOk: boolean; stock: boolean }) {
  return (
    <div className="flex flex-col items-end gap-1">
      {history && <ToolChip name="get_asset_history" done={historyOk} doneLabel="verified" icon={<Database size={11} />} />}
      {manual && <ToolChip name="search_manual" done={manualOk} doneLabel="§4.2 cooler" icon={<BookOpen size={11} />} />}
      {stock && <ToolChip name="check_stock" done doneLabel="cooler kit: 0 on site" icon={<Boxes size={11} />} />}
    </div>
  );
}

export function EvidenceCard() {
  return (
    <div className={cx(card, "w-max max-w-[min(44vw,220px)] border-violet/60 px-2.5 py-1.5")}>
      <div className="flex items-center gap-1.5 text-[10px] font-semibold text-violet leading-tight">
        <svg width="10" height="10" viewBox="0 0 12 12" aria-hidden><path d="M6 1 11 6 6 11 1 6Z" fill="none" stroke="currentColor" strokeWidth="1.8" /></svg>
        Camera evidence saved
      </div>
      <div className="text-[12px] leading-snug text-ink">Gauge reads 108 °C</div>
      <div className="text-[10.5px] text-pencil leading-tight">model observation · not a diagnosis</div>
    </div>
  );
}

export function OrderCard({ stamped }: { stamped: boolean }) {
  return (
    <div className={cx(card, "w-[min(46vw,236px)] px-2.5 py-2", stamped ? "border-green/70" : "border-ochre/80 bg-ochre-wash/95")}>
      <div className={cx("flex items-center gap-1.5 text-[10px] font-semibold leading-tight", stamped ? "text-green" : "text-ochre")}>
        <ShoppingCart size={11} aria-hidden />{stamped ? "Purchase request" : "Draft · needs your yes"}
      </div>
      <div className="font-mono text-[12px] sm:text-[13px] text-ink mt-0.5">PR-2001</div>
      <div className="text-[12px] leading-snug text-ink">Cooler kit × 1 · for C-204</div>
      {stamped
        ? <div className="text-[10.5px] text-pencil leading-tight mt-0.5">re-read from the database</div>
        : <div className="flex items-center gap-1 text-[11px] text-ochre font-semibold mt-1"><Mic size={11} aria-hidden />Say yes to approve</div>}
      {stamped && (
        <div className="rise mt-1.5 inline-block rotate-[-4deg] rounded-[3px] border-2 border-green px-1.5 py-0.5 text-[10px] sm:text-[11px] font-bold tracking-wide text-green whitespace-nowrap">
          SUBMITTED · verified
        </div>
      )}
    </div>
  );
}

export function ScanCard() {
  return (
    <div className={cx(card, "w-max max-w-[min(46vw,230px)] border-blue/50 px-2.5 py-1.5")}>
      <div className="flex items-center gap-1.5 text-[10px] font-semibold text-blue leading-tight"><ScanBarcode size={11} aria-hidden />Label scanned · sent to agent</div>
      <div className="font-mono text-[12px] sm:text-[13px] text-ink">FLT-OIL-75 · bin C-03</div>
      <div className="text-[10.5px] text-pencil leading-tight">oil filter KS-75 · 1 picked for C-204</div>
    </div>
  );
}

export function MachineTag({ position, id, name, state, show }: { position: V3; id: string; name: string; state?: "hot" | "ok"; show?: boolean }) {
  return (
    <Pin position={position} side="t" show={show}>
      <div className="flex items-center gap-1.5 rounded-full border border-rule bg-paper/80 px-2 py-0.5 text-[10.5px] whitespace-nowrap backdrop-blur-sm">
        <span className={cx("w-1.5 h-1.5 rounded-full", state === "hot" ? "bg-red now-dot" : "bg-green")} aria-hidden />
        <span className="font-mono font-semibold text-ink">{id}</span>
        <span className="text-pencil">{name}</span>
      </div>
    </Pin>
  );
}

/* ---------- the handoff screen content: an Html transform on the wall-mounted display ---------- */

/** The wall display is a physical dark screen, so it keeps the dark palette whatever the page theme is. */
const SCREEN_VARS = {
  "--ink": "#eceff1", "--ink-2": "#a9b1b8", "--pencil": "#737c84", "--rule": "#2a3036", "--ochre": "#e8a53a", "--green": "#4cc39a",
  "--violet": "#a99af0", "--teal": "#c8f135", fontFamily: "var(--font-sans)",
} as CSSProperties;

const RECEIVERS: { name: string; icon: ReactNode }[] = [
  { name: "Slack", icon: <MessageSquare size={10} /> },
  { name: "Telegram", icon: <Send size={10} /> },
  { name: "WhatsApp", icon: <MessageCircle size={10} /> },
  { name: "Excel", icon: <FileSpreadsheet size={10} /> },
  { name: "Calendar", icon: <CalendarDays size={10} /> },
];

export function HandoffScreen({ lit, received }: { lit: boolean; received: number }) {
  const [x, y, z] = PLACES.screen;
  return (
    <Html transform position={[x, y, z + 0.02]} distanceFactor={3.67} zIndexRange={[10, 0]} pointerEvents="none" wrapperClass="pointer-events-none select-none">
      <div className="w-[360px] h-[203px] overflow-hidden p-3 text-ink [backface-visibility:hidden]" style={SCREEN_VARS}>
        {!lit ? (
          <div className="h-full flex flex-col justify-between opacity-60">
            <div className="flex items-center justify-between text-[11px] text-pencil"><span>Shift board · A shift</span><span className="font-mono">14:31</span></div>
            <div className="grid grid-cols-4 gap-1.5">
              {["C-204", "CV-310", "AHU-3", "DC2"].map((m, i) => (
                <div key={m} className="rounded border border-rule px-1.5 py-1 text-[10px]">
                  <div className="font-mono text-ink-2">{m}</div>
                  <div className={i === 0 ? "text-ochre" : "text-pencil"}>{i === 0 ? "◆ attention" : "ok"}</div>
                </div>
              ))}
            </div>
            <div className="text-[10px] text-pencil">Waiting for the handoff…</div>
          </div>
        ) : (
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-teal">Shift handoff H-0043 · C-204</span>
              <span className="text-[10px] text-pencil">A → B shift</span>
            </div>
            <div className="mt-1 flex items-baseline gap-3">
              <span className="text-[22px] font-semibold leading-none text-ochre">2 open</span>
              <span className="text-[22px] font-semibold leading-none text-green">3 done</span>
            </div>
            <div className="mt-1.5 grid grid-cols-2 gap-x-3 text-[10px] leading-snug">
              <ul className="space-y-0.5">
                <li className="text-ink-2"><span className="text-ochre">◆</span> Fit cooler kit when it arrives</li>
                <li className="text-ink-2"><span className="text-ochre">◆</span> Confirm discharge under 105 °C</li>
              </ul>
              <ul className="space-y-0.5">
                <li className="text-ink-2"><span className="text-green">✓</span> PR-2001 submitted, verified</li>
                <li className="text-ink-2"><span className="text-green">✓</span> Oil filter FLT-OIL-75 picked</li>
                <li className="text-ink-2"><span className="text-violet">◇</span> Gauge photo saved</li>
              </ul>
            </div>
            <div className="mt-auto grid grid-cols-5 gap-1">
              {RECEIVERS.map((r, i) => {
                const got = i < received;
                return (
                  <div key={r.name} className={cx("min-w-0 flex items-center justify-center gap-0.5 rounded border px-0.5 py-1 text-[8.5px] transition-colors duration-300",
                    got ? "border-green/70 text-green bg-green/10" : "border-rule text-pencil")}>
                    <span className="shrink-0">{r.icon}</span><span className="truncate">{r.name}</span>{got && <Check size={8} strokeWidth={3} className="shrink-0" aria-hidden />}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Html>
  );
}

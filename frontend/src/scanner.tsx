// Scanning without scanner hardware: the device camera reads barcodes and QR codes (ZXing, in the browser), or the
// worker types the code. Both go through the same handler as a Zebra / keyboard-wedge scan (see scan.ts).
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Keyboard, Printer, ScanBarcode, X } from "lucide-react";
import { Btn, cx } from "./ui";
import { emitScan } from "./scan";

const DEMO_CODES = ["SHIFTTRACE:C-204", "SKU-2231", "B-04-2", "SHP-4471", "BRG-6316-C3"];

type Controls = { stop: () => void };

export function ScanButton({ size = "md", label = "Scan", className }: { size?: "sm" | "md" | "lg"; label?: string; className?: string }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Btn size={size} className={className} title="Scan a barcode or QR code with the camera, or type a code" onClick={() => setOpen(true)}>
        <ScanBarcode size={size === "lg" ? 18 : 16} />{label && <span className={size === "lg" ? "hidden sm:inline" : ""}>{label}</span>}
      </Btn>
      {open && <ScanDialog onClose={() => setOpen(false)} />}
    </>
  );
}

export function ScanDialog({ onClose }: { onClose: () => void }) {
  const video = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState<"starting" | "scanning" | "nocam">("starting");
  const [err, setErr] = useState<string | null>(null);
  const [typed, setTyped] = useState("");
  const done = useRef(false);

  const finish = (code: string) => {
    if (done.current || !code.trim()) return;
    done.current = true;
    try { navigator.vibrate?.(60); } catch { /* no vibration */ }
    onClose();
    window.setTimeout(() => emitScan(code.trim()), 0);
  };

  useEffect(() => {
    let controls: Controls | null = null;
    let cancelled = false;
    (async () => {
      try {
        const { BrowserMultiFormatReader } = await import("@zxing/browser");
        if (cancelled || !video.current) return;
        const reader = new BrowserMultiFormatReader();
        controls = await reader.decodeFromConstraints({ video: { facingMode: { ideal: "environment" } }, audio: false }, video.current, (result) => {
          if (result) finish(result.getText());
        });
        if (cancelled) controls.stop(); else setStatus("scanning");
      } catch (e) {
        if (cancelled) return;
        setStatus("nocam");
        const name = (e as Error)?.name;
        setErr(name === "NotAllowedError" ? "Camera permission was refused." : name === "NotFoundError" ? "No camera found on this device." :
          name === "NotReadableError" ? "The camera is busy (another app or the live call is using it)." : `Camera unavailable (${(e as Error)?.message ?? e}).`);
      }
    })();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => { cancelled = true; controls?.stop(); window.removeEventListener("keydown", onKey); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div role="dialog" aria-modal="true" aria-label="Scan a code" className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4" onClick={onClose}>
      <div className="w-full sm:max-w-md bg-sheet border border-rule-strong rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-rule">
          <h2 className="text-[16px] font-bold inline-flex items-center gap-2"><ScanBarcode size={18} className="text-teal" />Scan a code</h2>
          <button onClick={onClose} aria-label="Close" className="h-9 w-9 inline-flex items-center justify-center rounded-lg hover:bg-ink/5 text-ink-2"><X size={18} /></button>
        </div>
        <div className="relative aspect-[4/3] bg-black">
          <video ref={video} muted playsInline className={cx("absolute inset-0 w-full h-full object-cover", status !== "scanning" && "opacity-0")} />
          {status === "scanning" && (
            <div aria-hidden className="absolute inset-[16%_12%] border-2 border-teal/80 rounded-xl shadow-[0_0_0_9999px_rgba(0,0,0,0.35)]">
              <div className="absolute left-2 right-2 top-1/2 h-0.5 bg-red/80 animate-pulse" />
            </div>
          )}
          <div className="absolute bottom-0 inset-x-0 p-3 text-center text-[13px] text-white/85 bg-gradient-to-t from-black/70 to-transparent">
            {status === "starting" ? "Starting the camera…" : status === "scanning" ? "Point at a barcode or QR code" : err}
          </div>
        </div>
        <div className="p-4 grid gap-3">
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); finish(typed); }}>
            <label className="sr-only" htmlFor="scan-typed">Type a code</label>
            <div className="relative flex-1">
              <Keyboard size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-pencil" />
              <input id="scan-typed" value={typed} onChange={(e) => setTyped(e.target.value)} autoFocus={status === "nocam"} placeholder="Or type a code (part, bin, shipment, machine)"
                className="w-full h-11 pl-9 pr-3 rounded-lg bg-paper border border-rule-strong text-[15px] outline-none focus:border-teal" />
            </div>
            <Btn kind="primary" type="submit" disabled={!typed.trim()}>Use</Btn>
          </form>
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[12px] text-pencil mr-1">Demo codes</span>
            {DEMO_CODES.map((c) => (
              <button key={c} onClick={() => finish(c)} data-scan-code={c} className="h-7 px-2 rounded-md border border-rule text-[12px] font-mono text-ink-2 hover:border-teal hover:text-ink">{c.replace("SHIFTTRACE:", "")}</button>
            ))}
          </div>
          <p className="text-[12px] text-pencil flex flex-wrap items-center gap-x-1">
            Zebra DataWedge and keyboard-wedge scanners work on any page without opening this.
            <Link to="/labels" onClick={onClose} className="inline-flex items-center gap-1 text-teal hover:underline"><Printer size={12} />Print test labels</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

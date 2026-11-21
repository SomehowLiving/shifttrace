// Barcode and QR input from rugged devices.
// Zebra mobile computers (DataWedge keystroke output), and any USB or Bluetooth "keyboard wedge" scanner, type the
// scanned code very fast and finish with Enter. This hook tells a scan apart from a person typing by the speed of the
// keystrokes, so it works on any page without a special field and without a native app.
import { useEffect, useRef } from "react";

const MAX_GAP_MS = 45;   // scanners type a character every few ms; people are far slower
const MIN_LEN = 4;

export function useScanner(onScan: (code: string) => void, enabled = true) {
  const cb = useRef(onScan);
  cb.current = onScan;
  useEffect(() => {
    if (!enabled) return;
    let buf = "", last = 0;
    const onKey = (e: KeyboardEvent) => {
      const now = performance.now();
      if (now - last > MAX_GAP_MS) buf = "";
      last = now;
      if (e.key === "Enter" || e.key === "Tab") {
        if (buf.length >= MIN_LEN) {
          const code = buf.trim();
          buf = "";
          const t = e.target as HTMLElement | null;
          if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) (t as HTMLInputElement).value = (t as HTMLInputElement).value.replace(code, "");
          e.preventDefault();
          cb.current(code);
        }
        buf = "";
        return;
      }
      if (e.key.length === 1) buf += e.key;
    };
    // The camera scanner and the printable labels page (no scanner hardware needed) feed the same handler.
    const onEmitted = (e: Event) => { const code = String((e as CustomEvent).detail ?? "").trim(); if (code) cb.current(code); };
    window.addEventListener("keydown", onKey, true);
    window.addEventListener(SCAN_EVENT, onEmitted);
    return () => { window.removeEventListener("keydown", onKey, true); window.removeEventListener(SCAN_EVENT, onEmitted); };
  }, [enabled]);
}

const SCAN_EVENT = "shifttrace-scan";

/** Deliver a code as if a hardware scanner had read it (camera scan, typed code, or a tap on a test label). */
export function emitScan(code: string) {
  window.dispatchEvent(new CustomEvent(SCAN_EVENT, { detail: code }));
}

/** What a scanned code refers to: an asset QR ("SHIFTTRACE:C-204" or "C-204"), or anything else (part, bin, shipment). */
export function parseScan(code: string, assetIds: string[]): { asset?: string; text: string } {
  const c = code.trim().replace(/^SHIFTTRACE:/i, "");
  const asset = assetIds.find((a) => a.toUpperCase() === c.toUpperCase());
  return asset ? { asset, text: c } : { text: c };
}

/** Camera QR scanning where the browser supports it (Chrome and Edge on Android, ChromeOS, macOS). */
export function cameraScanSupported(): boolean {
  return typeof (window as unknown as { BarcodeDetector?: unknown }).BarcodeDetector !== "undefined";
}

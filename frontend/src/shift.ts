// Who is on shift at this console. Set once, used to start sessions (no form per session).
// Kept in localStorage as a per-viewer convenience; falls back to the demo default if storage is blocked.
import { useEffect, useState } from "react";

export interface OnShift { technician: string; shift: string }
const KEY = "shifttrace:on-shift";
const DEFAULT: OnShift = { technician: "Kavya Rao", shift: "A shift" };
const listeners = new Set<(s: OnShift) => void>();

function read(): OnShift {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? "null") as OnShift | null;
    if (v?.technician && v?.shift) return v;
  } catch { /* storage unavailable */ }
  return DEFAULT;
}
let current = read();

export function setOnShift(next: OnShift) {
  current = { technician: next.technician.trim() || DEFAULT.technician, shift: next.shift.trim() || DEFAULT.shift };
  try { localStorage.setItem(KEY, JSON.stringify(current)); } catch { /* keep in memory only */ }
  listeners.forEach((l) => l(current));
}

export function useOnShift(): OnShift {
  const [s, setS] = useState(current);
  useEffect(() => { listeners.add(setS); return () => { listeners.delete(setS); }; }, []);
  return s;
}

export const firstName = (name: string) => name.trim().split(/\s+/)[0] ?? name;

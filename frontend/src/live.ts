// One shared EventSource for backend state changes; components refetch on relevant topics.
import { useCallback, useEffect, useRef, useState } from "react";

type Listener = (topic: string, data: unknown) => void;
const listeners = new Set<Listener>();
let source: EventSource | null = null;
let connected = false;
const statusListeners = new Set<(c: boolean) => void>();

function ensure() {
  if (source) return;
  source = new EventSource("/api/stream");
  source.onopen = () => { connected = true; statusListeners.forEach((l) => l(true)); };
  source.onerror = () => { connected = false; statusListeners.forEach((l) => l(false)); };
  source.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data) as { topic: string; data: unknown };
      listeners.forEach((l) => l(msg.topic, msg.data));
    } catch { /* ignore malformed */ }
  };
}

export function useLiveTick(topics: string[] | "all"): number {
  const [tick, setTick] = useState(0);
  const key = topics === "all" ? "all" : topics.join(",");
  useEffect(() => {
    ensure();
    const set = key === "all" ? null : new Set(key.split(","));
    let timer: number | undefined;
    const l: Listener = (topic) => {
      if (set && !set.has(topic) && topic !== "reset") return;
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setTick((t) => t + 1), 120); // coalesce bursts
    };
    listeners.add(l);
    return () => { listeners.delete(l); window.clearTimeout(timer); };
  }, [key]);
  return tick;
}

/** Subscribe to raw events of one topic (e.g. "voice") with their payload. */
export function useLiveEvent(topic: string, cb: (data: unknown) => void): void {
  const ref = useRef(cb);
  ref.current = cb;
  useEffect(() => {
    ensure();
    const l: Listener = (t, data) => { if (t === topic) ref.current(data); };
    listeners.add(l);
    return () => { listeners.delete(l); };
  }, [topic]);
}

export function useStreamStatus(): boolean {
  const [c, setC] = useState(connected);
  useEffect(() => { ensure(); statusListeners.add(setC); return () => { statusListeners.delete(setC); }; }, []);
  return c;
}

export function useFetch<T>(url: string | null, deps: unknown[] = []): { data: T | null; error: string | null; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [n, setN] = useState(0);
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    fetch(url)
      .then(async (r) => {
        const body = await r.json().catch(() => null);
        if (!r.ok) throw new Error(body?.detail?.message ?? body?.detail ?? `HTTP ${r.status}`);
        return body as T;
      })
      .then((d) => { if (!cancelled) { setData(d); setError(null); } })
      .catch((e: Error) => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, n, ...deps]);
  const reload = useCallback(() => setN((x) => x + 1), []);
  return { data, error, reload };
}

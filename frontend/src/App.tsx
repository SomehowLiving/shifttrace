import { NavLink, Outlet, Route, Routes, Link, useLocation, useNavigate } from "react-router-dom";
import { parseScan, useScanner } from "./scan";
import { lazy, Suspense, useEffect, useState } from "react";
import { Box, ClipboardCheck, FlaskConical, Globe, LayoutGrid, ListChecks, Menu, Package, Plug, QrCode, Settings2, SunMoon } from "lucide-react";
import { ScanButton } from "./scanner";
import { cx, Btn } from "./ui";
import { useFetch, useLiveTick, useStreamStatus } from "./live";
import { setOnShift, useOnShift } from "./shift";
import type { Health, SessionRow } from "./api";
import Dashboard from "./pages/Dashboard";
import Landing, { Wordmark } from "./pages/Landing";
import AssetMemory from "./pages/AssetMemory";
import ActionCentre from "./pages/ActionCentre";
import AuditLog from "./pages/AuditLog";
import SystemPage from "./pages/System";
import Integrations from "./pages/Integrations";
import Quality from "./pages/Quality";
import { HandoffList, HandoffView } from "./pages/Handoff";
import PanelSim from "./pages/PanelSim";
import Labels from "./pages/Labels";
// three.js scene: loaded only on the 3D floor view.
const Floor3D = lazy(() => import("./pages/Floor3D"));
// Agora RTC/RTM SDKs are ~3 MB: load them only on the live-session route.
const LiveSession = lazy(() => import("./pages/LiveSession").catch((e) => {
  // A tab opened before a rebuild asks for an old chunk name (seen live 21 Nov). Reload once to get the new build.
  if (!sessionStorage.getItem("chunk-reload")) { sessionStorage.setItem("chunk-reload", "1"); window.location.reload(); }
  throw e;
}).then((m) => { sessionStorage.removeItem("chunk-reload"); return m; }));

function useTheme(): () => void {
  const read = () => { try { return localStorage.getItem("theme") ?? ""; } catch { return ""; } };
  const [theme, setTheme] = useState<string>(read);
  useEffect(() => { if (theme) document.documentElement.dataset.theme = theme; else delete document.documentElement.dataset.theme; }, [theme]);
  return () => {
    const dark = theme ? theme === "dark" : true; // dark is the default
    const next = dark ? "light" : "dark";
    try { localStorage.setItem("theme", next); } catch { /* switch for this visit only */ }
    setTheme(next);
  };
}

function SystemStatus() {
  const live = useStreamStatus();
  const tick = useLiveTick(["session", "flags", "tunnel"]);
  const { data: h } = useFetch<Health>("/api/health", [tick]);
  const problems = !live ? ["Backend not connected"] : !h ? [] : [
    !h.agora_credentials && "Agora keys missing", !h.murf_key && "Murf key missing", h.tunnel?.self_test === false && "Agora cannot reach the tools",
  ].filter(Boolean) as string[];
  const ok = live && !!h && problems.length === 0;
  return (
    <NavLink to="/system" title={problems.join("; ") || "All live checks pass"}
      className={cx("inline-flex items-center gap-2 h-9 px-2.5 rounded-[7px] hover:bg-ink/5", ok ? "label !text-ink-2" : "text-[13px] text-red font-semibold")}>
      {ok ? <span className="w-1.5 h-1.5 rounded-full bg-green" /> : <svg width="11" height="11" viewBox="0 0 10 10" aria-hidden><path d="M5 .8 9.6 9.2H.4Z" fill="var(--red)" /></svg>}
      <span className={ok ? "hidden md:inline" : ""}>{!h && live ? "Checking" : ok ? "All systems nominal" : problems.length === 1 ? problems[0] : `${problems.length} problems`}</span>
    </NavLink>
  );
}

function LivePill() {
  const tick = useLiveTick(["session"]);
  const { data } = useFetch<SessionRow[]>("/api/sessions", [tick]);
  const a = data?.find((s) => s.status === "ACTIVE");
  if (!a) return null;
  return (
    <Link to={`/session/${a.session_id}`} className="inline-flex items-center gap-2 h-9 px-3 rounded-[7px] bg-red/10 text-red text-[13.5px] font-semibold whitespace-nowrap hover:bg-red/15 shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--red)_30%,transparent)]">
      <span className="w-2 h-2 rounded-full bg-red now-dot" />Live on {a.asset_id}
    </Link>
  );
}

/** Who is on shift at this console. Sessions start under this name; change it at shift change. */
function OnShiftControl() {
  const me = useOnShift();
  const [edit, setEdit] = useState(false);
  const [t, setT] = useState(me.technician);
  const [sh, setSh] = useState(me.shift);
  useEffect(() => { setT(me.technician); setSh(me.shift); }, [me]);
  const field = "h-9 px-2 rounded-[7px] bg-sheet border border-rule-strong text-[15px] outline-none focus:border-teal";
  return (
    <div className="relative">
      <button onClick={() => setEdit(!edit)} aria-expanded={edit} className="w-full flex items-center gap-2.5 h-11 px-2 rounded-lg hover:bg-ink/[0.05] text-left" title="Change who is on shift">
        <span className="w-8 h-8 rounded-full bg-accent text-on-accent text-[12px] font-bold flex items-center justify-center shrink-0">{me.technician.split(/\s+/).map((w) => w[0]).join("").slice(0, 2)}</span><span className="min-w-0"><span className="block text-[14px] font-semibold truncate">{me.technician}</span><span className="block text-[12px] text-pencil">On shift, {me.shift}</span></span>
      </button>
      {edit && (
        <form onSubmit={(e) => { e.preventDefault(); setOnShift({ technician: t, shift: sh }); setEdit(false); }}
          className="absolute left-0 bottom-11 z-50 w-72 bg-sheet border border-rule-strong rounded-lg shadow-2xl p-3 grid gap-2">
          <label className="grid gap-1 text-[14px]">Technician<input autoFocus value={t} onChange={(e) => setT(e.target.value)} className={field} /></label>
          <label className="grid gap-1 text-[14px]">Shift<input value={sh} onChange={(e) => setSh(e.target.value)} className={field} /></label>
          <div className="flex justify-end gap-2 pt-1"><Btn kind="quiet" size="sm" onClick={() => setEdit(false)}>Cancel</Btn><Btn kind="primary" size="sm" type="submit">Save</Btn></div>
        </form>
      )}
    </div>
  );
}

const CRUMB: [RegExp, string, string][] = [
  [/^\/board/, "Shift", "Shift board"], [/^\/machines\//, "Shift", "Machine"], [/^\/audit/, "Records", "Audit log"],
  [/^\/actions/, "Records", "Stock, orders, follow-ups"], [/^\/handoffs/, "Records", "Handoffs"], [/^\/integrations/, "Setup", "Connected systems"],
  [/^\/quality/, "Setup", "Agent quality"], [/^\/system/, "Setup", "System and demo"], [/^\/labels/, "Setup", "Scan and test labels"],
];

function TopBar({ path }: { path: string }) {
  const c = CRUMB.find(([re]) => re.test(path));
  return (
    <div className="hidden lg:flex sticky top-0 z-30 h-16 items-center gap-3 px-8 border-b border-rule bg-paper/80 backdrop-blur">
      {c && <div className="flex items-baseline gap-2.5 min-w-0"><span className="label !text-teal">{c[1]} /</span><span className="text-[15px] font-medium truncate">{c[2]}</span></div>}
      <div className="ml-auto flex items-center gap-2"><LivePill /><SystemStatus /></div>
    </div>
  );
}

function Shell() {
  const toggleTheme = useTheme();
  const loc = useLocation();
  const [menu, setMenu] = useState(false);
  useEffect(() => setMenu(false), [loc.pathname]);
  // Scan a machine's QR or asset tag (Zebra DataWedge / any keyboard-wedge scanner) from any page to open that machine.
  const navTo = useNavigate();
  const { data: assetList } = useFetch<{ asset_id: string }[]>("/api/assets", []);
  const [scanMsg, setScanMsg] = useState<string | null>(null);
  useScanner((code) => {
    const r = parseScan(code, (assetList ?? []).map((a) => a.asset_id));
    if (r.asset) navTo(`/machines/${r.asset}`);
    else { setScanMsg(`Scanned ${r.text}. That is not a machine tag: scan it during a live session and the agent looks it up (part, bin or shipment).`); window.setTimeout(() => setScanMsg(null), 6000); }
  }, !loc.pathname.startsWith("/session/"));
  // A live session is a focused workspace with its own bar (back to the board, finish); no site navigation.
  if (loc.pathname.startsWith("/session/")) return <main id="main" className="min-h-full"><Outlet /></main>;
  const item = (to: string, label: string, icon: React.ReactNode) => (
    <NavLink to={to} className={({ isActive }) => cx("flex items-center gap-3 h-10 px-3 rounded-[9px] text-[14.5px] transition-colors",
      isActive || (to === "/board" && loc.pathname.startsWith("/machines/")) ? "bg-accent/[0.09] text-teal font-medium shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--teal)_16%,transparent)]" : "text-ink-2 hover:text-ink hover:bg-ink/[0.04]")}>{icon}{label}</NavLink>
  );
  const nav = (
    <nav aria-label="Main" className="grid gap-6">
      <div className="grid gap-1">
        <div className="label px-3 pb-1.5">Shift</div>
        {item("/board", "Shift board", <LayoutGrid size={17} />)}</div>
      <div className="grid gap-1">
        <div className="label px-3 pb-1.5">Records</div>
        {item("/audit", "Audit log", <ListChecks size={17} />)}
        {item("/actions", "Stock, orders, follow-ups", <Package size={17} />)}
        {item("/handoffs", "Handoffs", <ClipboardCheck size={17} />)}
      </div>
      <div className="grid gap-1">
        <div className="label px-3 pb-1.5">Setup</div>
        {item("/integrations", "Connected systems", <Plug size={17} />)}
        {item("/quality", "Agent quality", <FlaskConical size={17} />)}
        {item("/system", "System and demo", <Settings2 size={17} />)}
        {item("/labels", "Scan and test labels", <QrCode size={17} />)}
        <Link to="/" className="flex items-center gap-3 h-10 px-3 rounded-[9px] text-[14.5px] text-ink-2 hover:text-ink hover:bg-ink/[0.04]"><Globe size={17} />Product page</Link>
        <Link to="/floor" className="flex items-center gap-3 h-10 px-3 rounded-[9px] text-[14.5px] text-ink-2 hover:text-ink hover:bg-ink/[0.04]"><Box size={17} />3D floor view</Link>
      </div>
    </nav>
  );
  return (
    <div className="min-h-full">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:p-2 focus:bg-sheet">Skip to content</a>
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 flex-col border-r border-rule bg-sheet px-4 py-5 gap-7 z-40">
        <Link to="/" className="flex items-center px-2 pt-1"><Wordmark size={28} sub /></Link>
        {nav}
        <div className="mt-auto grid gap-3 border-t border-rule pt-4">
          <ScanButton label="Scan a code" className="w-full justify-center" />
          <div className="flex items-center gap-1"><div className="flex-1 min-w-0"><OnShiftControl /></div>
            <button onClick={toggleTheme} title="Light or dark theme" aria-label="Switch light or dark theme" className="h-9 w-9 shrink-0 inline-flex items-center justify-center rounded-lg hover:bg-ink/[0.05] text-ink-2"><SunMoon size={17} /></button></div>
        </div>
      </aside>
      <header className="lg:hidden sticky top-0 z-40 border-b border-rule bg-paper/90 backdrop-blur">
        <div className="flex items-center gap-2 px-4 h-14">
          <Link to="/" className="flex items-center"><Wordmark size={24} /></Link>
          <div className="ml-auto flex items-center gap-1"><LivePill /><ScanButton size="sm" label="" /><button onClick={() => setMenu(!menu)} aria-expanded={menu} aria-label="Menu" className="h-10 w-10 inline-flex items-center justify-center rounded-lg hover:bg-ink/[0.05]"><Menu size={20} /></button></div>
        </div>
        {menu && <div className="px-3 pb-4 grid gap-4">{nav}<div className="grid gap-2 border-t border-rule pt-3"><OnShiftControl /><div className="flex items-center justify-between"><SystemStatus /><button onClick={toggleTheme} aria-label="Switch light or dark theme" className="h-9 w-9 inline-flex items-center justify-center rounded-lg text-ink-2"><SunMoon size={17} /></button></div></div></div>}
      </header>
      <main id="main" className="lg:pl-64 min-h-full"><TopBar path={loc.pathname} /><Outlet /></main>
      {scanMsg && <div role="status" className="fixed bottom-4 right-4 z-50 card px-4 py-3 text-[14px] shadow-2xl max-w-sm">{scanMsg}</div>}
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/panel" element={<PanelSim />} />
      <Route path="/panel/:assetId" element={<PanelSim />} />
      <Route path="/" element={<Landing />} />
      <Route path="/floor" element={<Suspense fallback={<div className="h-[100dvh] grid place-items-center text-pencil">Loading the 3D view…</div>}><Floor3D /></Suspense>} />
      <Route element={<Shell />}>
        <Route path="/board" element={<Dashboard />} />
        <Route path="/machines/:assetId" element={<AssetMemory />} />
        <Route path="/session/:sessionId" element={<Suspense fallback={<div className="p-6 text-pencil">Opening the session…</div>}><LiveSession /></Suspense>} />
        <Route path="/actions" element={<ActionCentre />} />
        <Route path="/audit" element={<AuditLog />} />
        <Route path="/system" element={<SystemPage />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/quality" element={<Quality />} />
        <Route path="/handoffs" element={<HandoffList />} />
        <Route path="/handoffs/:handoffId" element={<HandoffView />} />
        <Route path="/labels" element={<Labels />} />
      </Route>
    </Routes>
  );
}

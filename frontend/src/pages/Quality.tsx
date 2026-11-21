// Agent quality: the improvement loop, from the evidence on disk (live runs, failures found and fixed, dataset, tests).
import { useMemo, useState } from "react";
import { Bug, Database, FlaskConical, Hammer, Play, ShieldCheck } from "lucide-react";
import { useFetch } from "../live";
import { PageHead, cx } from "../ui";

interface Scen { scenario: string; steps: number; checks: number; passed: number; failed_checks: string[]; median_latency_ms: number | null }
interface Run { run: string; when: string | null; checks: number; passed: number; pass_rate: number; scenarios: Scen[] }
interface Lesson { n: string; symptom: string; cause: string; fix: string; found_live: boolean }
interface Source { file: string; title?: string; creator?: string; license?: string; source?: string; provider?: string; label?: string }
interface Q { runs: Run[]; lessons: Lesson[]; media: { sources: Source[]; generated: string[]; kinds: Record<string, number> }; tests: { total: number; files: { file: string; count: number }[] }; cases: { scenes: number; lines: number; scenarios: string[] } }

const md = (t: string) => t.replace(/\*\*/g, "").replace(/`/g, "");
const label = (run: string) => `${run.slice(6, 8)}/${run.slice(4, 6)} ${run.slice(9, 11)}:${run.slice(11, 13)}`;

/** Pass rate per live run: one series, so no legend; hover shows the value; a table follows for exact numbers. */
function PassRateChart({ runs }: { runs: Run[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 860, H = 220, P = { l: 40, r: 12, t: 12, b: 36 };
  const bw = (W - P.l - P.r) / Math.max(1, runs.length);
  const y = (v: number) => P.t + (H - P.t - P.b) * (1 - v / 100);
  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Live-run pass rate by run">
        {[0, 50, 80, 100].map((g) => (
          <g key={g}><line x1={P.l} x2={W - P.r} y1={y(g)} y2={y(g)} stroke="var(--rule)" strokeWidth={1} />
            <text x={P.l - 6} y={y(g) + 4} textAnchor="end" fontSize={11} fill="var(--pencil)">{g}%</text></g>
        ))}
        {runs.map((r, i) => {
          const x = P.l + i * bw + 2, h = Math.max(2, y(0) - y(r.pass_rate));
          return (
            <g key={r.run} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <rect x={P.l + i * bw} y={P.t} width={bw} height={H - P.t - P.b} fill="transparent" />
              <path d={`M${x},${y(0)} v${-h + 4} q0,-4 4,-4 h${bw - 12} q4,0 4,4 v${h - 4} z`} fill="var(--teal)" opacity={hover === null || hover === i ? 1 : 0.45} />
              {(i % Math.ceil(runs.length / 8) === 0 || i === runs.length - 1) && <text x={x + (bw - 4) / 2} y={H - P.b + 16} textAnchor="middle" fontSize={10} fill="var(--pencil)">{label(r.run)}</text>}
            </g>
          );
        })}
      </svg>
      {hover !== null && (
        <div className="absolute pointer-events-none card px-3 py-2 text-[13px] shadow-xl" style={{ left: `${Math.min(80, (100 * (P.l + hover * bw)) / W)}%`, top: 0 }}>
          <div className="font-semibold">{label(runs[hover].run)}</div>
          <div>{runs[hover].passed} of {runs[hover].checks} checks passed ({runs[hover].pass_rate}%)</div>
          <div className="text-pencil">{runs[hover].scenarios.length} scenarios</div>
        </div>
      )}
    </div>
  );
}

export default function Quality() {
  const { data } = useFetch<Q>("/api/quality", []);
  const [tab, setTab] = useState<"runs" | "lessons" | "dataset">("runs");
  const latest = data?.runs[data.runs.length - 1];
  const first = data?.runs[0];
  const live = useMemo(() => data?.lessons.filter((l) => l.found_live).length ?? 0, [data]);
  if (!data) return <div className="p-8 text-pencil">Loading quality data…</div>;
  const media: Source[] = [...data.media.sources.filter((s) => /\.(jpe?g|png)$/i.test(s.file)), ...data.media.generated.filter((g) => g.endsWith(".png")).map((g) => ({ file: g, title: g, label: "rendered simulated panel", license: "own work", provider: "generated" }))];
  const videos = [...data.media.sources.filter((s) => s.file.endsWith(".webm")), ...data.media.generated.filter((g) => g.endsWith(".webm") && !data.media.sources.some((s) => s.file === g)).map((g) => ({ file: g, title: g, label: "derived video" } as Source))];

  return (
    <div className="px-5 sm:px-8 py-8 max-w-[1320px] mx-auto grid gap-8">
      <PageHead title="Agent quality" sub="How the agent gets better: run real scenarios against the live Agora agent, score every step, log each failure with its root cause, fix it, pin the fix with a regression test, run again. Everything below is read from the run files and the failure log, not typed in." />

      <ol className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3" aria-label="The improvement loop">
        {[
          [<Play size={18} />, "Run", `${data.runs.length} live runs: real Agora voice, Murf, vision and MCP tools, driven by recorded speech and camera scenes`],
          [<FlaskConical size={18} />, "Score", `${latest?.checks ?? 0} checks in the latest run: tools called, evidence labelled, approvals gated, nothing invented`],
          [<Bug size={18} />, "Diagnose", `${data.lessons.length} failures logged with root cause; ${live} were found in live runs`],
          [<Hammer size={18} />, "Fix", "Code, prompt or tool change; never by loosening a check"],
          [<ShieldCheck size={18} />, "Pin", `${data.tests.total} test functions keep every fix fixed; then run again`],
        ].map(([icon, t, d], i) => (
          <li key={String(t)} className="card p-5 relative">
            <div className="flex items-center justify-between"><span className="w-9 h-9 rounded-[10px] bg-raised border border-rule text-ink-2 flex items-center justify-center">{icon}</span><span className="font-mono text-[12px] text-pencil">0{i + 1}</span></div>
            <div className="mt-3 text-[17px] font-semibold">{t}</div>
            <p className="mt-1 text-[13px] text-ink-2 leading-relaxed">{d}</p>
          </li>
        ))}
      </ol>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[["Latest live run", latest ? `${latest.pass_rate}%` : "–", latest ? `${latest.passed} of ${latest.checks} checks` : ""],
          ["First recorded run", first ? `${first.pass_rate}%` : "–", first ? `${first.passed} of ${first.checks} checks` : ""],
          ["Failures fixed", String(data.lessons.length), `${live} found live`],
          ["Dataset", `${data.media.kinds.image + data.media.kinds.video}`, `images and videos, ${data.cases.lines} spoken test lines`]].map(([l, v, n]) => (
          <div key={l} className="card px-5 pt-4 pb-5"><div className="label">{l}</div><div className="mt-4 text-[40px] font-semibold leading-none tracking-[-0.05em] nameplate">{v}</div><div className="mt-1.5 text-[13px] text-ink-2">{n}</div></div>
        ))}
      </div>

      <div role="tablist" className="flex gap-1 border-b border-rule">
        {([["runs", "Live runs"], ["lessons", "Failures and fixes"], ["dataset", "Dataset"]] as const).map(([id, l]) => (
          <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)} className={cx("h-10 px-3 -mb-px border-b-2 text-[14px]", tab === id ? "border-teal text-ink font-semibold" : "border-transparent text-pencil hover:text-ink")}>{l}</button>
        ))}
      </div>

      {tab === "runs" && (
        <div className="grid gap-6">
          <div className="card p-5"><div className="flex items-baseline justify-between mb-2"><h2 className="text-[15px] font-semibold">Pass rate by live run</h2><span className="text-[12px] text-pencil">share of scored checks passed; scenarios vary per run</span></div><PassRateChart runs={data.runs} /></div>
          {latest && (
            <div className="card overflow-x-auto">
              <div className="px-5 pt-4 pb-2 text-[15px] font-semibold">Latest run, {label(latest.run)}</div>
              <table className="w-full text-[14px] min-w-[640px]">
                <thead><tr className="text-left text-[13px] text-pencil border-b border-rule"><th className="font-medium p-3 pl-5">Scenario</th><th className="font-medium p-3">Steps</th><th className="font-medium p-3">Checks passed</th><th className="font-medium p-3">Median first audio</th><th className="font-medium p-3">Missed</th></tr></thead>
                <tbody>{latest.scenarios.map((s) => (
                  <tr key={s.scenario} className="border-b border-rule last:border-0 align-top">
                    <td className="p-3 pl-5 font-semibold">{s.scenario.replace(/_/g, " ")}</td><td className="p-3">{s.steps}</td>
                    <td className="p-3" style={{ color: s.passed === s.checks ? "var(--green)" : "var(--ochre)" }}>{s.passed}/{s.checks}</td>
                    <td className="p-3 text-ink-2">{s.median_latency_ms ? `${(s.median_latency_ms / 1000).toFixed(1)} s` : "–"}</td>
                    <td className="p-3 text-[13px] text-ink-2">{s.failed_checks.join("; ") || "–"}</td>
                  </tr>))}</tbody>
              </table>
            </div>
          )}
          <div className="card overflow-x-auto">
            <div className="px-5 pt-4 pb-2 text-[15px] font-semibold">All runs</div>
            <table className="w-full text-[14px] min-w-[560px]"><thead><tr className="text-left text-[13px] text-pencil border-b border-rule"><th className="font-medium p-3 pl-5">Run</th><th className="font-medium p-3">Scenarios</th><th className="font-medium p-3">Checks</th><th className="font-medium p-3">Pass rate</th></tr></thead>
              <tbody>{[...data.runs].reverse().map((r) => <tr key={r.run} className="border-b border-rule last:border-0"><td className="p-3 pl-5 font-mono text-[13px]">{r.run}</td><td className="p-3 text-ink-2">{r.scenarios.map((s) => s.scenario).join(", ")}</td><td className="p-3">{r.passed}/{r.checks}</td><td className="p-3">{r.pass_rate}%</td></tr>)}</tbody></table>
          </div>
        </div>
      )}

      {tab === "lessons" && (
        <div className="card overflow-x-auto">
          <table className="w-full text-[14px] min-w-[860px]">
            <thead><tr className="text-left text-[13px] text-pencil border-b border-rule"><th className="font-medium p-3 pl-5 w-12">#</th><th className="font-medium p-3">What went wrong</th><th className="font-medium p-3">Root cause</th><th className="font-medium p-3">Fix (pinned by a test)</th></tr></thead>
            <tbody>{[...data.lessons].reverse().map((l) => (
              <tr key={l.n} className="border-b border-rule last:border-0 align-top">
                <td className="p-3 pl-5 font-mono text-pencil">{l.n}</td>
                <td className="p-3">{l.found_live && <span className="mr-1.5 text-[11px] font-semibold px-1.5 py-0.5 rounded border border-red/50 text-red">live</span>}{md(l.symptom)}</td>
                <td className="p-3 text-ink-2">{md(l.cause)}</td><td className="p-3 text-ink-2">{md(l.fix)}</td>
              </tr>))}</tbody>
          </table>
        </div>
      )}

      {tab === "dataset" && (
        <div className="grid gap-6">
          <p className="text-[14px] text-ink-2 max-w-[80ch]"><Database size={15} className="inline mr-1.5 text-teal" />Creative Commons photos (Openverse: Flickr) and audio (Freesound), hand-held videos derived from them, rendered simulated panels and synthetic speech. Each file's licence and source are recorded in experiments/media/MEDIA_SOURCES.json; the label says what a camera model should be able to see, which is how vision answers are judged.</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {media.map((m) => (
              <figure key={m.file} className="card overflow-hidden">
                <img src={`/api/quality/media/${encodeURIComponent(m.file)}`} alt={m.title ?? m.file} loading="lazy" className="w-full aspect-[4/3] object-cover bg-black" />
                <figcaption className="p-2.5 text-[12px] grid gap-0.5">
                  <span className="text-ink line-clamp-2">{m.label ?? m.title}</span>
                  <span className="text-pencil truncate">{m.license}{m.creator ? `, ${m.creator}` : ""}</span>
                  {m.source?.startsWith("http") && <a href={m.source} target="_blank" rel="noreferrer" className="text-blue hover:underline truncate">source</a>}
                </figcaption>
              </figure>
            ))}
          </div>
          {videos.length > 0 && <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">{videos.map((v) => (
            <figure key={v.file} className="card overflow-hidden"><video src={`/api/quality/media/${encodeURIComponent(v.file)}`} muted loop autoPlay playsInline className="w-full aspect-video bg-black" /><figcaption className="p-2.5 text-[12px] text-ink-2">{v.label ?? v.file}</figcaption></figure>))}</div>}
          <div className="text-[13px] text-pencil">Scenarios exercised: {data.cases.scenarios.join(", ")}. Test feed: {data.cases.scenes} scenes and {data.cases.lines} spoken lines.</div>
        </div>
      )}
    </div>
  );
}

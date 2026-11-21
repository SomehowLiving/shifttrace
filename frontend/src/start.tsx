// Starting a session is part of the machine page, not a form in a modal: who is on shift is already known.
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Play } from "lucide-react";
import { api, type TaskList } from "./api";
import { setOnShift, useOnShift } from "./shift";
import { Btn, cx } from "./ui";
import { setTestFeedPreferred, testFeedPreferred } from "./testfeed";

export function useStartSession() {
  const nav = useNavigate();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const start = async (assetId: string, technician: string, shift: string, voice: boolean, task?: string, feed = testFeedPreferred()) => {
    setBusy(true); setErr(null);
    try {
      const r = await api.startSession(assetId, technician, shift, voice, task || undefined);
      sessionStorage.setItem(`voice:${r.session_id}`, JSON.stringify({ voice: r.voice, voice_error: r.voice_error }));
      sessionStorage.setItem(`testfeed:${r.session_id}`, voice && feed ? "on" : "off");
      nav(`/session/${r.session_id}`);
    } catch (e) { setErr((e as Error).message); setBusy(false); }
  };
  return { start, busy, err };
}

export function StartPanel({ assetId, assetName }: { assetId: string; assetName: string }) {
  const me = useOnShift();
  const [tasks, setTasks] = useState<TaskList | null>(null);
  const [task, setTask] = useState("");
  const [voice, setVoice] = useState(true);
  const [feed, setFeed] = useState(testFeedPreferred());
  const { start, busy, err } = useStartSession();
  useEffect(() => {
    api.get<TaskList>(`/api/tasks?asset_id=${encodeURIComponent(assetId)}`)
      .then((t) => { setTasks(t); setTask(t.default); })
      .catch(() => setTasks({ asset_id: assetId, default: "", tasks: [] }));
  }, [assetId]);
  const chosen = tasks?.tasks.find((t) => t.id === task);
  return (
    <section aria-label={`Start a session on ${assetId}`} className="surface p-5 grid gap-3">
      <div>
        <h2 className="text-[19px] font-bold leading-tight">Start a session</h2>
        <p className="text-[14px] text-pencil">As {me.technician}, {me.shift}, on {assetName}.</p>
      </div>
      <fieldset>
        <legend className="text-[14px] font-bold mb-1.5">What is this session for?</legend>
        <div className="grid gap-1" role="radiogroup">
          {tasks?.tasks.map((t) => (
            <label key={t.id} data-task={t.id} className={cx("flex items-center gap-2.5 rounded-[7px] px-2.5 py-2 cursor-pointer text-[15px] border",
              task === t.id ? "border-teal/60 bg-teal/[0.06] font-semibold" : "border-transparent hover:bg-ink/[0.03]")}>
              <input type="radio" name="task" value={t.id} checked={task === t.id} onChange={() => setTask(t.id)} className="accent-[var(--teal)] w-4 h-4" />
              <span>{t.label}{t.id === tasks.default && <span className="font-normal text-pencil"> (usual for this machine)</span>}</span>
            </label>
          ))}
        </div>
        {chosen && <p className="text-[14px] text-ink-2 mt-2">{chosen.summary}{chosen.read_only ? " The agent can read and take notes only." : ""}</p>}
      </fieldset>
      <label className="flex items-start gap-2.5 text-[14px]">
        <input type="checkbox" checked={voice} onChange={(e) => setVoice(e.target.checked)} className="mt-0.5 accent-[var(--teal)] w-4 h-4" />
        <span><b>Start the voice agent</b>. Mic and camera stream to Agora while live.</span>
      </label>
      {voice && (
        <label data-testid="test-feed-option" className={cx("flex items-start gap-2.5 text-[14px] rounded-[7px] px-2.5 py-2 border", feed ? "border-violet/60 bg-violet/5" : "border-rule")}>
          <input type="checkbox" checked={feed} onChange={(e) => { setFeed(e.target.checked); setTestFeedPreferred(e.target.checked); }} className="mt-0.5 accent-[var(--violet)] w-4 h-4" />
          <span><b>No machine here? Use the test feed</b>. The camera shows recorded panels and photos of this machine, and you can play recorded questions as your voice. Your own mic still works.</span>
        </label>
      )}
      {err && <p role="alert" className="text-[14px] text-red">Could not start: {err}</p>}
      <Btn kind="primary" size="lg" onClick={() => start(assetId, me.technician, me.shift, voice, task, feed)} disabled={busy || !tasks}>
        <Play size={17} />{busy ? "Starting the agent…" : "Start session"}
      </Btn>
    </section>
  );
}

/** At the end of a handoff: hand the machine to the next person and start their briefing in one step. */
export function HandOver({ assetId, from }: { assetId: string; from: string }) {
  const me = useOnShift();
  const suggested = me.technician !== from ? me : { technician: from === "Dev Malhotra" ? "Kavya Rao" : "Dev Malhotra", shift: "B shift" };
  const [technician, setTechnician] = useState(suggested.technician);
  const [shift, setShift] = useState(suggested.shift);
  const { start, busy, err } = useStartSession();
  const field = "h-10 px-2.5 rounded-[7px] bg-sheet border border-rule-strong text-[15px] outline-none focus:border-teal min-w-0";
  return (
    <div className="grid gap-2">
      <div className="flex flex-wrap items-end gap-2">
        <label className="grid gap-1 text-[14px] grow">Next technician<input value={technician} onChange={(e) => setTechnician(e.target.value)} className={field} /></label>
        <label className="grid gap-1 text-[14px] w-32">Shift<input value={shift} onChange={(e) => setShift(e.target.value)} className={field} /></label>
        <Btn kind="primary" disabled={busy || technician.trim().length < 2} onClick={() => { setOnShift({ technician, shift }); void start(assetId, technician, shift, true, "shift_briefing"); }}>
          <Play size={16} />{busy ? "Starting…" : "Start next-shift briefing"}
        </Btn>
      </div>
      <p className="text-[13px] text-pencil">Starts a voice briefing as the next technician. The agent reads this handoff aloud and answers questions; it cannot order or change anything.</p>
      {err && <p role="alert" className="text-[14px] text-red">Could not start: {err}</p>}
    </div>
  );
}

// Browser side of the Agora Conversational AI session.
//  - RTC: publish microphone + camera into the channel; play the agent's (Murf Falcon) audio.
//  - RTM + agent toolkit: live transcripts and agent state; typed messages to the agent.
// Agora's ConvoAI engine samples the published camera track and forwards frames to the LLM
// (input_modalities text+image); we additionally upload occasional JPEG snapshots so visual
// observations in the evidence timeline carry the frame they were made from.
import AgoraRTC, {
  type ICameraVideoTrack, type IAgoraRTCClient, type IMicrophoneAudioTrack, type IAgoraRTCRemoteUser,
} from "agora-rtc-sdk-ng";
import AgoraRTM from "agora-rtm";
import {
  AgoraVoiceAI, AgoraVoiceAIEvents, ChatMessagePriority, ChatMessageType, TranscriptHelperMode, TurnStatus,
  type AgentState, type TranscriptHelperItem,
} from "agora-agent-client-toolkit";
import type { VoiceCreds } from "./api";

AgoraRTC.setLogLevel(2);

export interface TurnItem { key: string; role: "user" | "agent" | "system"; turnId: number; text: string; final: boolean; time: number }

export interface VoiceHandlers {
  onState?: (s: { rtc: string; agentJoined: boolean; agentState: AgentState | null; rtm: string }) => void;
  onTurns?: (items: TurnItem[]) => void;
  onIssue?: (msg: string) => void;
}

type RTMClient = InstanceType<typeof AgoraRTM.RTM>;

export class VoiceLink {
  client: IAgoraRTCClient;
  mic: IMicrophoneAudioTrack | null = null;
  cam: ICameraVideoTrack | null = null;
  rtm: RTMClient | null = null;
  ai: AgoraVoiceAI | null = null;
  private creds: VoiceCreds;
  private h: VoiceHandlers;
  private st = { rtc: "DISCONNECTED", agentJoined: false, agentState: null as AgentState | null, rtm: "DISCONNECTED" };
  private snapshotTimer: number | undefined;
  private sessionId: string;
  private posted = new Map<string, string>();
  /** Diagnostics for tests and debugging: timestamps of state/transcript/media events. */
  log: { t: number; kind: string; data: unknown }[] = [];
  remoteAudioTrack: MediaStreamTrack | null = null;

  constructor(sessionId: string, creds: VoiceCreds, handlers: VoiceHandlers) {
    this.sessionId = sessionId;
    this.creds = creds;
    this.h = handlers;
    this.client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
    (window as unknown as { __shifttrace?: VoiceLink }).__shifttrace = this;
  }

  private note(kind: string, data: unknown) {
    this.log.push({ t: Date.now(), kind, data });
    if (this.log.length > 2000) this.log.shift();
  }

  private emit(patch: Partial<typeof this.st>) {
    this.st = { ...this.st, ...patch };
    this.note("state", this.st);
    this.h.onState?.(this.st);
  }

  async connect(opts: { camera: boolean; facingMode: "environment" | "user" }) {
    const { app_id, channel, token, user_uid, agent_uid } = this.creds;
    this.client.on("connection-state-change", (cur) => this.emit({ rtc: cur }));
    this.client.on("stream-message", (uid, payload) => this.note("rtc_stream_msg", { uid: String(uid), len: payload?.length }));
    this.client.on("user-published", async (user: IAgoraRTCRemoteUser, mediaType) => {
      await this.client.subscribe(user, mediaType);
      if (mediaType === "audio") {
        user.audioTrack?.play();
        this.remoteAudioTrack = user.audioTrack?.getMediaStreamTrack() ?? null;
        this.note("agent_audio", { uid: String(user.uid) });
      }
    });
    this.client.on("user-joined", (u) => { if (String(u.uid) === String(agent_uid)) this.emit({ agentJoined: true }); });
    this.client.on("user-left", (u) => { if (String(u.uid) === String(agent_uid)) this.emit({ agentJoined: false }); });
    AgoraRTC.onAutoplayFailed = () => this.h.onIssue?.("Browser blocked audio autoplay. Click anywhere on the page to hear the agent.");

    const rtmPromise = (async () => {
      const rtm = new AgoraRTM.RTM(app_id, String(user_uid));
      rtm.addEventListener("linkState", (e) => this.emit({ rtm: String(e.currentState) }));
      rtm.addEventListener("message", (e) => {
        const m = typeof e.message === "string" ? e.message : new TextDecoder().decode(e.message as Uint8Array);
        this.note("rtm_msg", { from: e.publisher, type: e.channelType, len: m.length, head: m.slice(0, 160) });
      });
      await rtm.login({ token });
      await rtm.subscribe(channel);
      this.rtm = rtm;
    })().catch((e) => this.h.onIssue?.(`Signaling (RTM) failed: ${e?.message ?? e}. Transcripts and spoken approvals will be unavailable; use the console buttons.`));

    await this.client.join(app_id, channel, token, user_uid);
    this.mic = await AgoraRTC.createMicrophoneAudioTrack({ AEC: true, ANS: true, AGC: true });
    const tracks: (IMicrophoneAudioTrack | ICameraVideoTrack)[] = [this.mic];
    if (opts.camera) {
      try {
        this.cam = await AgoraRTC.createCameraVideoTrack({ encoderConfig: "720p_1", facingMode: opts.facingMode, optimizationMode: "detail" });
        tracks.push(this.cam);
      } catch (e) {
        this.h.onIssue?.(`Camera unavailable (${(e as Error).message}). Voice continues without vision.`);
      }
    }
    await this.client.publish(tracks);
    await rtmPromise;
    if (this.rtm) await this.initToolkit(channel, String(agent_uid));
    this.startSnapshots();
  }

  private async initToolkit(channel: string, agentUid: string) {
    try {
      const ai = await AgoraVoiceAI.init({ rtcEngine: this.client, rtmConfig: { rtmEngine: this.rtm! }, renderMode: TranscriptHelperMode.TEXT, enableLog: false } as never);
      ai.on(AgoraVoiceAIEvents.TRANSCRIPT_UPDATED, (items: TranscriptHelperItem<unknown>[]) => this.handleTranscript(items, agentUid));
      ai.on(AgoraVoiceAIEvents.AGENT_STATE_CHANGED, (_: string, ev: { state: AgentState }) => this.emit({ agentState: ev.state }));
      ai.on(AgoraVoiceAIEvents.AGENT_ERROR, (_: string, err: { type: string; message: string }) => this.h.onIssue?.(`Agent error: ${err.type}: ${err.message}`));
      ai.on(AgoraVoiceAIEvents.MESSAGE_ERROR, (_: string, err: { code: number; message: string }) => this.h.onIssue?.(`Agent message error ${err.code}: ${err.message}`));
      ai.subscribeMessage(channel);
      this.ai = ai;
    } catch (e) {
      this.h.onIssue?.(`Transcript toolkit failed: ${(e as Error).message}`);
    }
  }

  private handleTranscript(items: TranscriptHelperItem<unknown>[], agentUid: string) {
    const turns: TurnItem[] = items.map((it) => {
      const text0 = (it.text ?? "").trim();
      // think() injections from our backend echo back as user transcripts: show them as system notes.
      const role: "user" | "agent" | "system" = String(it.uid) === agentUid ? "agent"
        : /^(SYSTEM CHECK|SYSTEM NOTICE|The technician (approved|declined))/.test(text0) ? "system" : "user";
      // The toolkit marks interim user ASR updates as non-IN_PROGRESS; Agora's raw message carries the
      // real `final` flag, which the approval gate depends on.
      const meta = (it.metadata ?? {}) as { final?: boolean; turn_status?: TurnStatus };
      const final = role === "agent" ? it.status !== TurnStatus.IN_PROGRESS : meta.final === true || role === "system";
      return { key: `${role}-${it.turn_id}`, role, turnId: it.turn_id, text: (it.text ?? "").trim(), final, time: it._time };
    });
    this.h.onTurns?.(turns);
    this.note("transcript", turns.slice(-2).map((t) => ({ role: t.role, turn: t.turnId, final: t.final, len: t.text.length })));
    for (const t of turns) {
      if (!t.text) continue;
      // Agent: post when first seen (marks the read-back start) and when final. User: post only final.
      const state = `${t.final ? "F" : "P"}`;
      const prev = this.posted.get(t.key);
      if (t.role === "system") continue; // the backend already knows what it injected
      const shouldPost = t.role === "agent" ? (!prev || (t.final && prev !== `F:${t.text}`)) : (t.final && prev !== `F:${t.text}`);
      if (!shouldPost) continue;
      this.posted.set(t.key, `${state}:${t.text}`);
      void fetch(`/api/sessions/${this.sessionId}/transcripts`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ role: t.role, turn_id: String(t.turnId), text: t.text, final: t.final }),
      }).catch(() => undefined);
    }
  }

  async sendText(text: string) {
    if (!this.ai) throw new Error("Text channel not available (RTM not connected)");
    await this.ai.sendText(String(this.creds.agent_uid), {
      messageType: ChatMessageType.TEXT, priority: ChatMessagePriority.INTERRUPTED, responseInterruptable: true, text,
    });
    await fetch(`/api/sessions/${this.sessionId}/transcripts`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ role: "user", turn_id: `typed-${Date.now()}`, text, final: true }),
    });
  }

  private startSnapshots() {
    const grab = async () => {
      if (!this.cam || !this.cam.enabled) return;
      try {
        const frame = this.cam.getCurrentFrameData();
        if (!frame.width) return;
        const scale = Math.min(1, 800 / frame.width);
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(frame.width * scale);
        canvas.height = Math.round(frame.height * scale);
        const tmp = document.createElement("canvas");
        tmp.width = frame.width; tmp.height = frame.height;
        tmp.getContext("2d")!.putImageData(frame, 0, 0);
        canvas.getContext("2d")!.drawImage(tmp, 0, 0, canvas.width, canvas.height);
        const blob: Blob | null = await new Promise((r) => canvas.toBlob(r, "image/jpeg", 0.72));
        if (blob) await fetch(`/api/sessions/${this.sessionId}/snapshot`, { method: "POST", body: blob, headers: { "content-type": "image/jpeg" } });
      } catch { /* frame not ready */ }
    };
    this.snapshotTimer = window.setInterval(grab, 4000);
  }

  async setMicMuted(muted: boolean) { await this.mic?.setMuted(muted); }
  async setCameraEnabled(on: boolean) { await this.cam?.setEnabled(on); }
  async flipCamera(): Promise<string | null> {
    if (!this.cam) return null;
    const cams = await AgoraRTC.getCameras();
    if (cams.length < 2) return null;
    const current = this.cam.getTrackLabel();
    const idx = cams.findIndex((c) => c.label === current);
    const next = cams[(idx + 1) % cams.length];
    await this.cam.setDevice(next.deviceId);
    return next.label;
  }

  async disconnect() {
    window.clearInterval(this.snapshotTimer);
    try { this.ai?.unsubscribe(); this.ai?.destroy(); } catch { /* noop */ }
    this.mic?.close(); this.cam?.close();
    this.mic = null; this.cam = null;
    await this.client.leave().catch(() => undefined);
    await this.rtm?.logout().catch(() => undefined);
    this.emit({ rtc: "DISCONNECTED", agentJoined: false, agentState: null, rtm: "DISCONNECTED" });
  }
}

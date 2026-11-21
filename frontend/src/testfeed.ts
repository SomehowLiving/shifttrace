// Test feed: try SHIFTTRACE without a machine.
// Replaces the camera with a canvas that shows a recorded panel image or video, and mixes recorded questions into
// the microphone (your real mic stays mixed in, so you can still talk). Agora receives these tracks exactly like a
// real camera and mic, so the agent, tools, approvals and audit log all behave as they would on the floor.
// Works by wrapping getUserMedia before the Agora tracks are created (the same method the test harness uses).

export interface Scene { id: string; label: string; file: string; kind: "image" | "video"; url: string }
export interface Line { id: string; text: string; file: string; url: string; scene: string | null; note?: string }
export interface TestKit { scenes: Scene[]; lines: Line[] }

const W = 1280, H = 720;

class Feed {
  private canvas = document.createElement("canvas");
  private g = this.canvas.getContext("2d")!;
  private cur: HTMLImageElement | HTMLVideoElement | null = null;
  private vid = Object.assign(document.createElement("video"), { muted: true, loop: true, playsInline: true });
  private actx: AudioContext | null = null;
  private dest: MediaStreamAudioDestinationNode | null = null;
  private stream: MediaStream | null = null;
  private realMic: MediaStream | null = null;
  private timer = 0;
  private cache = new Map<string, AudioBuffer>();
  private original: typeof navigator.mediaDevices.getUserMedia | null = null;
  scene: string | null = null;

  private draw = () => {
    const g = this.g;
    g.fillStyle = "#0a0a0a"; g.fillRect(0, 0, W, H);
    const c = this.cur;
    const sw = c ? ((c as HTMLVideoElement).videoWidth || (c as HTMLImageElement).naturalWidth || 0) : 0;
    const sh = c ? ((c as HTMLVideoElement).videoHeight || (c as HTMLImageElement).naturalHeight || 0) : 0;
    if (c && sw && sh) { const k = Math.min(W / sw, H / sh); g.drawImage(c, (W - sw * k) / 2, (H - sh * k) / 2, sw * k, sh * k); }
  };

  get installed() { return this.original !== null; }

  install() {
    if (this.original) return;
    this.canvas.width = W; this.canvas.height = H;
    this.timer = window.setInterval(this.draw, 66);
    this.stream = this.canvas.captureStream(15);
    this.actx = new AudioContext({ sampleRate: 48000 });
    this.dest = this.actx.createMediaStreamDestination();
    const md = navigator.mediaDevices;
    const original = md.getUserMedia.bind(md);
    this.original = original;
    md.getUserMedia = async (c?: MediaStreamConstraints) => {
      const out = new MediaStream();
      if (c?.audio && this.actx && this.dest) {
        await this.actx.resume();
        if (!this.realMic) {
          // Keep the technician's own voice in the mix; carry on with recorded lines only if the mic is unavailable.
          // Never block on the permission prompt: if it is not answered in a few seconds, start with recorded lines
          // only and add the mic if permission arrives later.
          const ask = original({ audio: { echoCancellation: true, noiseSuppression: true } });
          const attach = (m: MediaStream) => { if (this.actx && this.dest && !this.realMic) { this.realMic = m; this.actx.createMediaStreamSource(m).connect(this.dest); } else m.getTracks().forEach((t) => t.stop()); };
          const got = await Promise.race([ask.then((m) => m, () => null), new Promise<"wait">((r) => setTimeout(() => r("wait"), 6000))]);
          if (got && got !== "wait") attach(got);
          else if (got === "wait") ask.then(attach, () => undefined);
        }
        out.addTrack(this.dest.stream.getAudioTracks()[0].clone());
      }
      if (c?.video && this.stream) out.addTrack(this.stream.getVideoTracks()[0].clone());
      return out;
    };
  }

  uninstall() {
    if (!this.original) return;
    navigator.mediaDevices.getUserMedia = this.original;
    this.original = null;
    window.clearInterval(this.timer);
    this.realMic?.getTracks().forEach((t) => t.stop()); this.realMic = null;
    void this.actx?.close(); this.actx = null; this.dest = null;
    this.vid.pause(); this.cur = null; this.scene = null;
  }

  async show(s: Scene | null) {
    this.scene = s?.id ?? null;
    if (!s) { this.cur = null; this.vid.pause(); return; }
    if (s.kind === "image") { const im = new Image(); im.src = s.url; await im.decode(); this.cur = im; this.vid.pause(); return; }
    this.vid.src = s.url; await this.vid.play(); this.cur = this.vid;
  }

  /** Play a recorded line into the microphone. Resolves when it has finished. */
  async say(url: string) {
    if (!this.actx || !this.dest) throw new Error("Test feed is not running");
    await this.actx.resume();
    let b = this.cache.get(url);
    if (!b) { b = await this.actx.decodeAudioData(await (await fetch(url)).arrayBuffer()); this.cache.set(url, b); }
    const src = this.actx.createBufferSource(); src.buffer = b; src.connect(this.dest);
    await new Promise<void>((r) => { src.onended = () => r(); src.start(); });
  }
}

export const testFeed = new Feed();

const KEY = "shifttrace:test-feed";
export function testFeedPreferred(): boolean { try { return localStorage.getItem(KEY) !== "off"; } catch { return true; } }
export function setTestFeedPreferred(on: boolean) { try { localStorage.setItem(KEY, on ? "on" : "off"); } catch { /* per visit only */ } }

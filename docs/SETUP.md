# Setup

Tested on Windows 11, Python 3.12 (via uv 0.11), Node 24, Microsoft Edge.

## 1. Accounts and keys
1. **Agora Console**: create or open a project with an App Certificate. Conversational AI is enabled by default for new projects. Enable **Signaling (RTM)** for the project (needed for live transcripts and spoken approvals).
2. **Murf**: an API key with access to Falcon (`https://api.murf.ai/v1/speech/voices?model=falcon-2.1` must return voices).
3. Copy `backend/.env.example` to `backend/.env` (already created, with a random `MCP_TOKEN`) and fill `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, `MURF_API_KEY`. Optionally pick a voice with `MURF_VOICE_ID`.

No OpenAI, Deepgram or Google key is needed: ASR and LLM use Agora managed mode.

### Stable public endpoint (recommended): ngrok
Agora cloud must reach the MCP port. Free Cloudflare quick tunnels proved unreliable in live tests (Agora intermittently could not reach them; one died mid-run).
1. Sign up at https://dashboard.ngrok.com/signup (free).
2. Copy the token from https://dashboard.ngrok.com/get-started/your-authtoken into `NGROK_AUTHTOKEN`.
3. Claim the free static domain at https://dashboard.ngrok.com/domains and put it in `NGROK_DOMAIN` (e.g. `your-words.ngrok-free.app`).
4. `winget install Ngrok.Ngrok` then `ngrok update` (winget ships an old agent).
With a static domain the URL never changes, so the watchdog can restart ngrok without cutting a live agent off from its tools. If ngrok fails to start, the backend falls back to a Cloudflare quick tunnel.

## 2. Install
```powershell
winget install Cloudflare.cloudflared
cd backend;  uv sync
cd ..\frontend; npm install; npx vite build
```

## 3. Run
```powershell
.\start.ps1 -Reset
```
Wait for `tunnel MCP self-test: PASS` in the log. Then:
```powershell
cd backend; uv run python -m app.preflight
```
Expected: `[  OK]` for Agora ConvoAI REST, Murf key accepted, MURF_VOICE_ID, MCP tunnel.

## Notes
- Windows Application Control on this machine blocks uv's generated `.exe` launchers (`pytest.exe` and similar); use `uv run python -m <module>`.
- If the quick tunnel is blocked on venue Wi-Fi, use a phone hotspot, or set `MCP_PUBLIC_URL` to another tunnel (e.g. ngrok) pointing at port 8001; the backend self-tests it at startup.
- Camera and microphone need a secure context: use `http://localhost:8000` on the laptop. To use a phone as the camera, open the console on the phone via an HTTPS tunnel of port 8000 **only for the demo**, and keep it private.

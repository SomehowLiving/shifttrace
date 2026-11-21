# Murf Falcon integration

Sources (19 Nov 2026):
- Agora Murf page, Main: https://docs.agora.io/en/ai/models/tts/murf
- Murf stream-input WebSocket reference: https://murf.ai/api/docs/api-reference/text-to-speech/stream-input
- Murf list voices: https://murf.ai/api/docs/api-reference/voices/get-voices

## Facts verified from the docs
- Agora vendor `murf`. Main API: key inline at `tts.params.api_key`. (The Preview API instead requires BYOK through a secret set, `$secrets.<set>.<key>`; the earlier project brief described the Preview behaviour.)
- Endpoint `wss://global.api.murf.ai/v1/speech/stream-input`.
- `model: FALCON` is accepted; Murf maps `falcon`, `falcon2`, `falcon-2` case-insensitively to **Falcon 2.1**, the only model on that endpoint. Gen2 is not available there.
- Sample rates 8000 / 24000 / 44100 / 48000; we use 24000.
- Voice IDs: Murf's docs show `Gordon`, Agora's show `Matthew`, but on our account (verified by preflight, 19 Nov) Falcon IDs are locale-prefixed, e.g. `en-US-wayne`, `en-IN-isha`. `Matthew` does not exist. We use `en-IN-isha`. Falcon voices are listed by `GET https://api.murf.ai/v1/speech/voices?model=falcon-2.1` with header `api-key`.
- A rejected key does not return 401: the WebSocket upgrades and then closes with code 1008. A bad key would therefore surface as silence, not an error. That is why preflight validates the key with the voices API first.

## How we prove Murf is the voice
1. `app.preflight` validates the key and that `MURF_VOICE_ID` is a Falcon voice on the account.
2. The session's stored agent config (redacted) shows `tts.vendor=murf, params.model=FALCON, voiceId=…`; the timeline records "TTS vendor=murf model=FALCON voice=…" at session start; the Live session "Agent" panel renders it from the stored config.
3. Audible output in the session (requires the human check; recorded in `experiments/RESULTS.md` once done).

Status: key and voice verified by preflight (verified-hosted); audible output through Agora not yet tested.

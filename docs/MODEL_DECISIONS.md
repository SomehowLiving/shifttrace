# Model decisions

## Hardware (inspected 19 Nov 2026)
Intel Core Ultra 5 125H (18 threads), Intel Arc integrated GPU (~2 GB shared, no CUDA), 16 GB RAM, Windows 11.

## Decision table
| Function | Choice | Why | Alternatives rejected |
|---|---|---|---|
| Live voice transport, turn-taking | Agora ConvoAI | Hackathon requirement | — |
| Speech output | Murf FALCON via Agora | Hackathon requirement | MLLM native audio (would bypass Murf) |
| ASR | Deepgram nova-3, Agora-managed | No extra key; default in official recipes | BYOK ASR (more keys, no benefit) |
| Reasoning + tool calling | gpt-4o-mini, Agora-managed | Keyless, supports tools and image input; recipe-proven | Custom LLM endpoint (needs our own LLM key and an extra hop) |
| Camera understanding | Same managed LLM with `input_modalities: [text, image]`; Agora forwards camera frames | One path, no extra key, observation happens inside the conversation | Separate perception worker (Gemini/MiniCPM) adds a second model call per frame and a key |
| Audio events (machine sounds) | Not implemented | No validated model; DCASE-style anomaly detection does not diagnose faults | — |
| Manual retrieval | BM25 over manual sections (in-process) | Deterministic, testable, no embedding key; corpus is 6 sections | Embeddings (no benefit at this size) |
| Handoff writing | Deterministic composer from records | Grounding guarantee; the LLM only speaks it | LLM-written handoff (could invent facts) |

## Candidates from the research brief
| Model | Status | Notes |
|---|---|---|
| MiniCPM-o 4.5 (9B) | blocked (hardware) | Official demo is PyTorch + CUDA; no NVIDIA GPU here. Its own TTS would also not satisfy Murf |
| Realtime-Venus (9B) | blocked (hardware) | CUDA + Linux scripts per brief; not downloaded |
| Gemini Live | not-tested | Agora lists Gemini Live as an **MLLM** vendor; MLLM mode disables Agora's TTS module, so Murf could not speak. Could be used only as a side perception worker (future) |
| MOSS-Live, Qwen Audio Agent | code-reference-only | Architecture references (foreground voice + background tasks). Our equivalent: Agora voice in front, MCP tools as the background workers |

The brief's model claims (versions, release dates, benchmark numbers) were not independently re-verified, because hardware ruled out local inference within minutes and the Agora-managed vision path removed the need for a second model. They should be treated as unverified.

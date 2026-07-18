# Hapjes Avontuur

Dutch kids snack-encouragement game. Single-page static app for GitHub Pages.

Live (from `main`): https://beecave-orchestrator.github.io/hapjes-avontuur/

## What’s in this branch (`feat/xai-static-tts`)

This branch adds **v1 pre-generated Dutch speech assets** and wires them into the game. The 🔊 toggle now gates both the existing Web Audio SFX beeps and static speech playback. No runtime TTS, no API keys.

| Path | Purpose |
| --- | --- |
| `index.html` | Game UI + Web Audio SFX beeps + static speech playback (wired) |
| `audio/*.mp3` | 16 static Dutch voice clips |
| `audio/manifest.json` | Stable ID -> path + exact Dutch source text map |
| `scripts/generate_xai_dutch_v1.py` | Offline regenerator (Hermes xAI TTS) |
| `scripts/build_manifest.py` | Rebuilds `audio/manifest.json` from disk |
| `scripts/validate_audio_assets.py` | Non-destructive path/text/header checks |

## Architecture: static audio only

- **No runtime TTS** in the browser.
- **No API keys**, tokens, or provider calls from the page.
- Speech is generated **offline**, committed as MP3, hosted like any other static file on GitHub Pages.
- The 🔊 toggle gates both the oscillator SFX and the static speech: off = silent, on = plays the matching clip.
- A single shared `Audio` element is lazily created inside the first user gesture (toggleSound / hapGenomen / resetGame) so the browser autoplay policy unlocks playback. `stopSpeech()` runs before each new clip so rapid taps never overlap speech.

```
build-time (Hermes / xAI OAuth)     runtime (GitHub Pages)
──────────────────────────────      ──────────────────────
Dutch lines + language=nl    ->     audio/*.mp3 + manifest.json
                                    index.html plays by stable ID
```

## Frozen v1 line inventory

Stable IDs are frozen against `index.html` copy:

| ID | Category | Dutch source text |
| --- | --- | --- |
| `start` | start/reset | Klaar voor de eerste superhap? |
| `msg_01` … `msg_10` | random encouragements | `messages[]` in order |
| `reward_3` | reward @ 3 hapjes | title + body (see decision) |
| `reward_5` | reward @ 5 | title + body |
| `reward_10` | reward @ 10 | title + body |
| `reward_15` | reward @ 15 | title + body |
| `reward_20` | reward @ 20 | title + body |

**Reward title+body decision (v1):** each reward is **one** spoken clip combining `title` and `body` as `"{title} {body}"` for a single modal announcement. Separate title/body files were not generated.

Exact strings, byte sizes, and SHA-256 digests live in `audio/manifest.json`.

## Asset generation provenance

| Field | Value |
| --- | --- |
| Provider | xAI TTS (`POST /v1/tts`) |
| Voice | `ara` |
| Language | `nl` (per-call override) |
| Format | MP3, 24 kHz, 64 kbps, mono |
| Speech tags | off |
| Generated | 2026-07-18T20:11:37Z |
| Global Hermes TTS config | **not** modified (`tts.xai.language` left at profile default) |
| Credentials | Hermes xAI OAuth on the generator machine only — **never** committed |

Regenerate (requires working Hermes xAI OAuth; use the Hermes venv):

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes/profiles/investigator}"
"$HOME/.hermes/hermes-agent/venv/bin/python" scripts/generate_xai_dutch_v1.py
"$HOME/.hermes/hermes-agent/venv/bin/python" scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json` or smoke leftovers.

## Validation

```bash
python3 scripts/validate_audio_assets.py
```

Checks: every manifest key has a playable MP3 path, headers look like MPEG, bytes match, Dutch source text matches `index.html`, and the HTML has no network-TTS / API-key patterns.

## Out of scope here

- PR to `main` / GitHub Pages deploy of speech (handled separately)
- Changing Hermes global TTS defaults
- OpenAI / Edge alternate voice boards

## License / content

Game copy and voice lines are original project content for personal/family use.

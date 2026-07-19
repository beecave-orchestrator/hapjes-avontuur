# Hapjes Avontuur

Dutch kids snack-encouragement game. Single-page static app for GitHub Pages.

Live (from `main`): https://beecave-orchestrator.github.io/hapjes-avontuur/

## What’s in this branch (`feat/openai-static-tts-marin`)

Full quality replacement of the static speech pack. All 16 spoken lines are
pre-generated with **OpenAI `gpt-4o-mini-tts`** voice **`marin`**, committed as
MP3, and played locally. The 🔊 toggle gates both Web Audio SFX beeps and static
speech. No runtime TTS, no API keys in the browser.

| Path | Purpose |
| --- | --- |
| `index.html` | Game UI + Web Audio SFX + static speech playback + AI disclosure |
| `audio/*.mp3` | 16 static Dutch voice clips |
| `audio/manifest.json` | Stable ID -> path + exact Dutch source text + hashes |
| `scripts/speech_inventory.py` | Frozen IDs + source lines (single inventory) |
| `scripts/generate_openai_dutch_v1.py` | Offline regenerator (OpenAI Platform key) |
| `scripts/build_manifest.py` | Rebuilds `audio/manifest.json` from disk (+ ffprobe) |
| `scripts/validate_audio_assets.py` | Non-destructive path/text/header/checksum checks |

## Architecture: static audio only

- **No runtime TTS** in the browser.
- **No API keys**, tokens, or provider calls from the page.
- Speech is generated **offline**, committed as MP3, hosted like any other static file on GitHub Pages.
- The 🔊 toggle gates both the oscillator SFX and the static speech: off = silent, on = plays the matching clip.
- A single shared `Audio` element is lazily created inside the first user gesture (toggleSound / hapGenomen / resetGame) so the browser autoplay policy unlocks playback. `stopSpeech()` runs before each new clip so rapid taps never overlap speech.
- Visible disclosure: **“Stemgeluid is AI-gegenereerd.”** (OpenAI TTS usage policy).

```
build-time (OpenAI Platform key)     runtime (GitHub Pages)
────────────────────────────────      ──────────────────────
Dutch lines + gpt-4o-mini-tts/marin -> audio/*.mp3 + manifest.json
                                      index.html plays by stable ID
```

## Frozen line inventory

Stable IDs are frozen against `index.html` copy:

| ID | Category | Dutch source text |
| --- | --- | --- |
| `start` | start/reset | Klaar voor de eerste superhap? |
| `msg_01` … `msg_10` | random encouragements | `messages[]` in order (`msg_03` = **Super goed bezig!**) |
| `reward_3` | reward @ 3 hapjes | title + body (see decision) |
| `reward_5` | reward @ 5 | title + body |
| `reward_10` | reward @ 10 | title + body |
| `reward_15` | reward @ 15 | title + body |
| `reward_20` | reward @ 20 | title + body |

**Reward title+body decision:** each reward is **one** spoken clip combining
`title` and `body` as `"{title} {body}"` for a single modal announcement.

Exact strings, byte sizes, SHA-256 digests, and measured codec parameters live
in `audio/manifest.json`.

## Asset generation provenance

| Field | Value |
| --- | --- |
| Provider | OpenAI TTS (`POST /v1/audio/speech`) |
| Model | `gpt-4o-mini-tts` |
| Voice | `marin` |
| Locale / language | Dutch input (`nl-NL` product copy) |
| Format | MP3 (measured on disk via ffprobe after generation) |
| Instructions | Warm, clear, encouraging, child-friendly moderate pace |
| Credentials | `OPENAI_API_KEY` on the generator machine only (BWS-backed) — **never** committed |
| Supersedes | Prior xAI `ara` Dutch static pack |

Regenerate (requires `OPENAI_API_KEY`, or `BWS_ACCESS_TOKEN` that can read it):

```bash
export OPENAI_API_KEY  # or rely on BWS_ACCESS_TOKEN + scripts/generate_openai_dutch_v1.py
"$HOME/.hermes/hermes-agent/venv/bin/python" scripts/generate_openai_dutch_v1.py
"$HOME/.hermes/hermes-agent/venv/bin/python" scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json` or smoke leftovers.

## Validation

```bash
python3 scripts/validate_audio_assets.py
```

Checks: every manifest key has a playable MP3 path, headers look like MPEG,
bytes and SHA-256 match, Dutch source text matches `index.html` (including
`Super goed bezig!`), AI disclosure is present, generation provenance is OpenAI,
and the HTML has no network-TTS / API-key patterns.

## Out of scope here

- Merge to `main` / GitHub Pages deploy without review + human ear QA
- Changing Hermes global TTS defaults
- Runtime browser TTS or network speech calls

## License / content

Game copy and voice lines are original project content for personal/family use.
Spoken audio is AI-generated with OpenAI TTS and disclosed in the UI.

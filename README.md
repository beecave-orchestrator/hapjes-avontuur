# Hapjes Avontuur

Dutch kids snack-encouragement game. Single-page static app for GitHub Pages.

Live (from `main`): https://beecave-orchestrator.github.io/hapjes-avontuur/

## What’s in this branch (`fix/issue-7-positive-end-state`)

This branch adds a **positive, pressure-free end state** (issue #7). The main
adventure now has a safe end boundary: after 20 hapjes the game opens a
"Avontuur klaar!" dialog with a clear **Klaar met eten** primary exit and an
optional **Bonusavontuur** that explicitly says eating more is not required.
Pressure copy ("Je bord wordt al leger!", "Nog eentje voor de power?", "Je
vliegt door dit avondeten heen.") is replaced with neutral, positive lines.

| Path | Purpose |
| --- | --- |
| `index.html` | Game UI + Web Audio SFX beeps + static speech playback (wired) |
| `audio/*.mp3` | 19 static Dutch voice clips (incl. 3 end-state clips) |
| `audio/manifest.json` | Stable ID -> path + exact Dutch source text map |
| `scripts/generate_xai_dutch_v1.py` | Original xAI regenerator (kept for provenance) |
| `scripts/regenerate_edge_tts.py` | Current regenerator (edge-tts, no API key) |
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

## Frozen line inventory

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
| `end` | end state | Avontuur klaar! Verder eten is niet nodig. Je mag stoppen wanneer je wilt. |
| `end_done` | end state | Avontuur klaar! Je mag stoppen wanneer je wilt. |
| `bonus` | end state | Bonusavontuur! Verder eten is niet nodig, maar mag wel. |

**Reward title+body decision (v1):** each reward is **one** spoken clip combining `title` and `body` as `"{title} {body}"` for a single modal announcement. Separate title/body files were not generated.

Exact strings, byte sizes, and SHA-256 digests live in `audio/manifest.json`.

## Asset generation provenance

| Field | Value |
| --- | --- |
| Provider | edge-tts (Microsoft Edge neural TTS) |
| Voice | `nl-NL-FennaNeural` (warm, clear Dutch female) |
| Language | `nl` |
| Format | MP3, 24 kHz, 48 kbps, mono |
| Speech tags | off |
| Generated | 2026-08-14 (issue #7 regeneration) |
| Credentials | none — edge-tts needs no API key |

> **Voice change note:** the original v1 clips used the xAI `ara` voice. Issue
> #7 changed the copy and added end-state clips; xAI OAuth was unavailable in
> the regeneration environment, so all clips were regenerated with edge-tts
> `nl-NL-FennaNeural` for consistency. If the xAI voice is preferred, rerun the
> original `scripts/generate_xai_dutch_v1.py` (requires Hermes xAI OAuth) and
> rebuild the manifest.

Regenerate (requires `pip install edge-tts`):

```bash
python3 scripts/regenerate_edge_tts.py
python3 scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json` or smoke leftovers.

## Validation

```bash
python3 scripts/validate_audio_assets.py
```

Checks: every manifest key has a playable MP3 path, headers look like MPEG, bytes match, Dutch source text matches `index.html`, the end-state lines are present, no pressure copy remains, and the HTML has no network-TTS / API-key patterns.

## Out of scope here

- PR to `main` / GitHub Pages deploy (handled separately, requires explicit approval)
- Changing Hermes global TTS defaults
- Reverting the voice to xAI `ara` (see voice change note above)

## License / content

Game copy and voice lines are original project content for personal/family use.

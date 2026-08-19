# Hapjes Avontuur

Dutch kids snack-encouragement game. Single-page static app for GitHub Pages.

Live (from `main`): https://beecave-orchestrator.github.io/hapjes-avontuur/

## What’s in this branch (`feat/issue-5-schatkist`)

This branch adds a **quiet, cosmetic reward loop** (issue #5): hap nemen →
muntje verdienen → doel kiezen → zichtbaar ontgrendelen.

- Every registered hap gives **exactly one muntje**. The old escalating
  combo multiplier is gone.
- One savings goal at a time with visible progress, e.g.
  `🪙 4 van 8 — nog 4 muntjes tot de panda`.
- The **Schatkist** holds five strictly cosmetic items (Feestconfetti,
  Feestbord, Dierenvriendje, Regenbooglucht, Feeststrik). Prices act as
  thresholds on one shared spaarpot: unlocking never deducts muntjes, so
  the balance can never go negative.
- Unlocked cosmetics apply immediately and permanently: confetti button,
  plate rim, panda friend, rainbow sky, bow.
- **Reset is child-friendly and explicit.** "Opnieuw" starts a new
  adventure and never touches the spaarpot or unlocked items. The pot only
  clears through "Opnieuw sparen" inside the Schatkist, which asks for
  confirmation and always keeps unlocked items.
- No timers, streaks, quotas, rankings, munt deduction, or food rewards.

| Path | Purpose |
| --- | --- |
| `index.html` | Game UI + Web Audio SFX beeps + static speech playback (wired) |
| `audio/*.mp3` | 19 static Dutch voice clips (incl. 3 end-state clips) |
| `audio/manifest.json` | Stable ID -> path + exact Dutch source text map |
| `scripts/regenerate_edge_tts.py` | Regenerates the current edge-tts clips (no API key) |
| `scripts/build_manifest.py` | Rebuilds `audio/manifest.json` from disk |
| `scripts/validate_audio_assets.py` | Non-destructive path/text/header checks |
| `tests/verify_schatkist.js` | Issue #5 reward-loop and reset behavior checks |

## Architecture: static audio only

- **No runtime TTS** in the browser.
- **No API keys**, tokens, or provider calls from the page.
- Speech is generated **offline**, committed as MP3, hosted like any other static file on GitHub Pages.
- The 🔊 toggle gates both the oscillator SFX and the static speech: off = silent, on = plays the matching clip.
- A single shared `Audio` element is lazily created inside the first user gesture (toggleSound / hapGenomen / resetGame) so the browser autoplay policy unlocks playback. `stopSpeech()` runs before each new clip so rapid taps never overlap speech.

```
build-time (edge-tts)               runtime (GitHub Pages)
────────────────────               ──────────────────────
Dutch lines + voice=nl-NL-FennaNeural -> audio/*.mp3 + manifest.json
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

> **Speech disclosure:** the UI visibly states that the spoken texts are
> AI-generated. Current clips are generated with edge-tts
> `nl-NL-FennaNeural`.

Regenerate (requires `pip install edge-tts`):

```bash
python3 scripts/regenerate_edge_tts.py
python3 scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json` or smoke leftovers.

## Validation

```bash
node tests/verify_schatkist.js
node tests/verify_end_state.js
node tests/verify_document_links.js
python3 scripts/validate_audio_assets.py
```

Checks: every manifest key has a playable MP3 path, headers look like MPEG, bytes match, Dutch source text matches `index.html`, the end-state lines and AI-speech disclosure are present, no pressure copy remains, and the HTML has no network-TTS / API-key patterns.

## Out of scope here

- PR to `main` / GitHub Pages deploy (handled separately, requires explicit approval)
- Changing Hermes global TTS defaults
- Changing the edge-tts voice or regenerating audio without reviewing it

## License / content

Game copy and voice lines are original project content for personal/family use.

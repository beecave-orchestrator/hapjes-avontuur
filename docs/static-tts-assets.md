# Static speech assets

## Purpose

This document describes the committed, static Dutch speech pack. The browser never performs runtime TTS or sends audio/text to a speech API.

## Asset inventory

Stable IDs are frozen against `index.html` copy:

| ID | Category | Dutch source text |
| --- | --- | --- |
| `start` | start/reset | Klaar voor de eerste superhap? |
| `msg_01` … `msg_10` | encouragements | `messages[]` in order |
| `reward_3` … `reward_20` | reward | title + body |
| `end` | end state | Avontuur klaar! Verder eten is niet nodig. Je mag stoppen wanneer je wilt. |
| `end_done` | end state | Avontuur klaar! Je mag stoppen wanneer je wilt. |
| `bonus` | end state | Bonusavontuur! Verder eten is niet nodig, maar mag wel. |

Each reward is one spoken clip combining `{title} {body}`. The three end-state clips support the pressure-free completion dialog.

## Current pack provenance

| Field | Value |
| --- | --- |
| Provider | edge-tts (Microsoft Edge neural TTS) |
| Voice | `nl-NL-FennaNeural` |
| Locale | Dutch (`nl`) |
| Format | MP3, measured 24 kHz / 48 kbps / mono |
| Generation | 2026-08-14 issue #7 regeneration |
| Credentials | none required by edge-tts |

The UI accurately discloses that speech is AI-generated. `scripts/generate_openai_dutch_v1.py` remains available as the prior OpenAI-pack generator, but is not the generator or provenance for this 19-clip end-state pack.

## Regeneration and validation

```bash
python3 scripts/regenerate_edge_tts.py
python3 scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json`.

Validation checks the manifest paths, sizes, MP3 headers, source-text alignment, positive end-state copy, absence of pressure copy, and that `index.html` has no runtime-TTS or API-key patterns.

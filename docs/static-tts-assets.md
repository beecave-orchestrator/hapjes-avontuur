# Static speech assets

## Purpose

This document describes the committed, static Dutch speech pack. The browser never performs runtime TTS or sends audio/text to a speech API.

## Asset inventory

Stable IDs are frozen against `index.html` copy. `scripts/speech_inventory.py` is the single source of truth for IDs, categories, and texts; the generator, manifest builder, and validator all import from it:

| ID group | Category | Dutch source text |
| --- | --- | --- |
| `start`, `msg_01` … `msg_10` | start/reset, encouragements | start line and `messages[]` in order |
| `reward_3` … `reward_20` | reward | title + body |
| `end`, `end_done`, `bonus` | end state | completion-dialog lines |
| `picker_title_1`, `picker_title_2` | picker | "Wat eet je vandaag?" / "Wil je nog wat kiezen?" (title + note per step) |
| `meal_<key>`, `extra_<key>` | names | meal and extra names as shown on chips |
| `chip_kies`, `chip_eat_<key>` | chip status | "Kies je eten" / "Je eet nu: X" |
| `schatkist_intro`, `schatkist_actief`, `schatkist_vrij` | schatkist | title/standing question, "Hier spaar je voor", "Van jou!" |
| `spaar_reset_vraag`, `spaar_reset_nieuw` | spaar reset | reset question and confirmation |
| `unlock_<item>`, `unlock_einde_<item>` | unlock | "Gefeliciteerd! X is nu van jou!" (goal and end-of-adventure variants) |

Each reward is one spoken clip combining `{title} {body}`. The three end-state clips support the pressure-free completion dialog.

Spoken text matches the visible line exactly (issue #15 rule). Numeric status lines (pot counts, "nog 4 muntjes", "3 van 8") are deliberately not frozen or spoken: there are 39+ numeric combinations, and re-speaking counts on every change works against the pressure-free design. Buttons stay silent: action labels such as "Hiervoor sparen" are not progress or status lines, so no `schatkist_kies` clip exists.

## Current pack provenance

| Field | Value |
| --- | --- |
| Provider | OpenAI TTS (`POST /v1/audio/speech`) |
| Model | `gpt-4o-mini-tts` |
| Voice | `marin` |
| Locale | Dutch (`nl-NL`) |
| Format | MP3 |
| Credentials | `OPENAI_API_KEY` or `VOICE_TOOLS_OPENAI_KEY` in the process environment only — never committed |

Do not ship edge-tts. If the key is missing, stop.

The UI discloses that speech is AI-generated in the parent/info menu (issue #8).

## Regeneration and validation

Tooling requirements: `python3` and `ffmpeg` (`ffprobe` must be on `PATH`;
`build_manifest.py` and `validate_audio_assets.py` shell out to it for codec
facts and bitrate checks; both fail closed with a clear message if it is
missing).

```bash
test -n "${OPENAI_API_KEY:-${VOICE_TOOLS_OPENAI_KEY:-}}" || { echo "OpenAI key missing"; exit 1; }
python3 scripts/generate_openai_dutch_v1.py --only-missing
python3 scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json`.

Validation checks the manifest paths, sizes, MP3 headers, source-text alignment, positive end-state copy, absence of pressure copy, issue #15 child-facing coverage (every visible child line category has a clip and a `playSpeech` hook), and that `index.html` has no runtime-TTS or API-key patterns.

## Tests

`tests/child_tts.test.mjs` covers the issue #15 playback hooks with the same hand-rolled DOM shims as `tests/meal_picker.test.mjs` (no jsdom, zero dependencies): picker titles, meal/extra name clips, chip clips and their timing (chip clip only after the picker closes, guarded `start` clip on first confirmed meal), schatkist lines, spaar-reset lines, unlock announcements, silent buttons and parent menu, and a non-destructive validator failure test.

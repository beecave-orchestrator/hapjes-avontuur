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

This branch also keeps the merged **meal picker** (issue #6):

- "Eten kiezen" opens a dialog with labelled Dutch meals: Aardappels en
  groente, Pasta, Rijst, Noedels, Soep, and the permanent neutral choice
  **Mijn eigen eten**. Emoji are supplementary (`aria-hidden`); the text
  labels carry the meaning.
- The chosen meal stays visible all session in a chip under the counter
  ("Je eet nu: …") and can be changed deliberately by reopening the picker.
- An optional, explicitly skippable second step (Groente, Vlees of vis,
  Vegetarisch, Saus, Weet ik niet) never pressures the child: "Deze stap
  overslaan" and Escape both pass without answering, and skipping never
  changes the chosen meal.
- Keyboard and screen-reader support: `role="dialog"` + `aria-modal`,
  radiogroup semantics with `aria-checked` and roving `tabindex`, arrow-key
  selection, visible `:focus-visible` outlines, a Tab focus trap, and focus
  restoration to the opener button on close.
- No automatic emoji rotation anywhere in the meal-selection experience.

| Path | Purpose |
| --- | --- |
| `index.html` | Game UI + Web Audio SFX beeps + static speech playback (wired) |
| `audio/*.mp3` | 54 static Dutch voice clips (child-facing pack) |
| `audio/manifest.json` | Stable ID -> path + exact Dutch source text map |
| `scripts/generate_openai_dutch_v1.py` | Regenerates clips via OpenAI gpt-4o-mini-tts / marin |
| `scripts/build_manifest.py` | Rebuilds `audio/manifest.json` from disk |
| `scripts/validate_audio_assets.py` | Non-destructive path/text/header checks |
| `tests/verify_schatkist.js` | Issue #5 reward-loop and reset behavior checks |
| `tests/meal_picker.test.mjs` | Zero-dep Node tests: picker behaviour + a11y |
| `tests/parent_menu.test.mjs` | Zero-dep Node tests: issue #8 oudermenu + a11y |

## Architecture: static audio only

- **No runtime TTS** in the browser.
- **No API keys**, tokens, or provider calls from the page.
- Speech is generated **offline**, committed as MP3, hosted like any other static file on GitHub Pages.
- The 🔊 toggle gates both the oscillator SFX and the static speech: off = silent, on = plays the matching clip.
- A single shared `Audio` element is lazily created inside the first user gesture (toggleSound / hapGenomen / resetGame) so the browser autoplay policy unlocks playback. `stopSpeech()` runs before each new clip so rapid taps never overlap speech.

```
build-time (OpenAI gpt-4o-mini-tts / marin)   runtime (GitHub Pages)
──────────────────────────────────────────   ──────────────────────
Dutch lines + voice=marin -> audio/*.mp3 + manifest.json
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
| Provider | OpenAI TTS (`POST /v1/audio/speech`) |
| Model | `gpt-4o-mini-tts` |
| Voice | `marin` |
| Language | `nl` |
| Format | MP3 |
| Credentials | `OPENAI_API_KEY` or `VOICE_TOOLS_OPENAI_KEY` in the environment only |

> **Speech disclosure:** the parent/info menu (ℹ️ next to the sound button)
> states that the spoken texts are AI-generated. Current clips use
> OpenAI `gpt-4o-mini-tts` / `marin`. Do not fall back to edge-tts.

Regenerate (fails closed without a key):

```bash
python3 scripts/generate_openai_dutch_v1.py --only-missing
python3 scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json` or smoke leftovers.

## Validation

```bash
node tests/verify_schatkist.js
node tests/verify_end_state.js
node tests/verify_document_links.js
node --test tests/*.test.mjs
python3 scripts/validate_audio_assets.py
```

The `node --test` glob covers `tests/meal_picker.test.mjs` and `tests/parent_menu.test.mjs` (issue #8).

The Node tests are zero-dependency: they run the real inline `<script>` from
`index.html` inside a minimal DOM shim, so no jsdom install is needed.

Checks: every manifest key has a playable MP3 path, headers look like MPEG, bytes match, Dutch source text matches `index.html`, the end-state lines are present, the AI-speech disclosure lives inside the parent/info menu (`oudermenu`), no pressure copy remains, and the HTML has no network-TTS / API-key patterns.

## Out of scope here

- PR to `main` / GitHub Pages deploy (handled separately, requires explicit approval)
- Changing Hermes global TTS defaults
- Changing the OpenAI voice or regenerating audio without reviewing it

## License / content

Game copy and voice lines are original project content for personal/family use.

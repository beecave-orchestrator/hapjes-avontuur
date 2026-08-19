# AGENTS.md — Hapjes Avontuur

This file is the operating manual for agents working in this repository.
Read it before changing `index.html`, `audio/`, or opening a PR.

The product is a Dutch, child-facing snack game. A child sees it. A parent
trusts it. Agents are guests.

## What this is

- Single-page static app. The game is `index.html`. There is no build, no
  bundler, no backend, no accounts.
- Hosted from `main` on GitHub Pages:
  https://beecave-orchestrator.github.io/hapjes-avontuur/
- Host clone: `/home/elvee/projects/hapjes-avontuur`
- Feature work lives in git worktrees under `.worktrees/`. Do not commit
  `.worktrees/`.
- Kanban board slug: `hapjes-avontuur`. Do not park this work on
  `agent-output`.

## Product rules (non-negotiable)

These are the reasons PRs were sent back. Treat them as merge gates.

### 1. Child-facing text is spoken

Every line a child can see must have a frozen local MP3 and a `playSpeech`
hook **in the same change**. That is a standing merge rule, not a follow-up.

- Spoken text must match the visible line.
- Inventory lives in `scripts/speech_inventory.py`. Manifest:
  `audio/manifest.json`.
- Numeric pot counters (`nog X muntjes`, `X van Y`) stay silent on purpose.
- The oudermenu / parent-info dialog stays silent. It is for adults.
- Do not play `start` (`Klaar voor de eerste superhap?`) while that line is
  hidden.

If you add or change child copy and skip audio, the change is not done.

### 2. Voice is OpenAI marin. Stop if the key is missing

Required generator: `scripts/generate_openai_dutch_v1.py`

- Model: `gpt-4o-mini-tts`
- Voice: `marin`
- Key: `OPENAI_API_KEY` in the process environment (local alias
  `VOICE_TOOLS_OPENAI_KEY` is accepted by the generator). Never print it.
  Never put BWS IDs or secret lookup in this repo.

**Fail closed.** If the key is missing or rejected, stop. Do not generate
edge-tts / `nl-NL-FennaNeural`. Do not ship a mixed pack. Do not claim
`provider: openai` while files are still Fenna.

`scripts/regenerate_edge_tts.py` is leftover tooling. Do not use it for
new clips.

A marin pack in this repo is 128 kbps CBR. 48 kbps is the Fenna signature.
`scripts/validate_audio_assets.py` must fail a 48 kbps file under a marin
label. After regeneration: `python3 scripts/build_manifest.py` (it probes
bitrate; do not hardcode 48000).

Keep `audio/_generation_run.json` untracked.

### 3. No eetdruk

Copy stays warm, optional, and proud. Never pressure a child to eat more.

Forbidden patterns: must / moet, finish your plate, one more bite as duty,
shame, comparison, “almost there, keep eating”.

End-state lines already say stopping is allowed. Keep that.

### 4. Meal first

Until a meal is chosen, hide the play chrome: message, level, hap-button,
Schatkist, badges, hap-counter. The first action is **Kies je eten**.

`#playArea` starts `hidden`. `hapGenomen()` must refuse and open the picker
when no meal is selected. `resetGame()` may keep the chosen meal; that is
different from first-choice hide.

### 5. Overlays shade everything except the popup

Dialogs (ouder, picker, Schatkist, end, reward):

- Dimmer: `rgba(45, 42, 74, 0.72)` over the **full viewport**.
- Popup card: solid white, opacity 1. Game text must not show through.
- Preferred stack: confetti `z-index: 30`, dialogs `40`, end-state `45`,
  oudermenu `46` with a separate `.oudermenu-scrim` behind the card.
- Look at a **full-page** screenshot yourself. A cropped dialog hid the
  “shade stops halfway” bug more than once.

### 6. Look at the pixels

If the change is visual, you must inspect a full-page shot before claiming
it is fine. Do not invent diffs for images you did not open.

On GitHub, relative `![x](docs/…)` in a PR **body** usually does not
render. After push, comment with:

`https://github.com/beecave-orchestrator/hapjes-avontuur/blob/<branch>/<path>?raw=true`

## Layout

```
index.html                 Game: CSS + markup + one inline script
audio/*.mp3                Frozen speech pack
audio/manifest.json        IDs, exact Dutch text, hashes, probed codec
scripts/speech_inventory.py Single source of spoken lines
scripts/generate_openai_dutch_v1.py  Only allowed clip generator
scripts/build_manifest.py
scripts/validate_audio_assets.py
tests/*.test.mjs           Zero-dep Node tests (DOM shim, no jsdom)
tests/verify_*.js          End-state, Schatkist, doc-link checks
docs/static-tts-assets.md  TTS provenance and regenerate steps
assets/                    Icons / PWA bits
```

State lives in the page script. No framework, no npm app.

## Commands

No install. Open `index.html`, or serve the folder statically.

```bash
python3 scripts/validate_audio_assets.py
node --test tests/*.test.mjs
node tests/verify_end_state.js
node tests/verify_schatkist.js
node tests/verify_document_links.js
```

After meal-first: end-state / Schatkist stubs must `selectMeal("pasta")`
before hap / end / chest flows.

After speech work:

```bash
test -n "${OPENAI_API_KEY:-${VOICE_TOOLS_OPENAI_KEY:-}}" || exit 1
python3 scripts/generate_openai_dutch_v1.py --only-missing   # or full run
python3 scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Need `ffprobe` for manifest bitrate probes.

## Git and PRs

- Branch from current `origin/main`. Work in a worktree.
- Commits: `<type> <emoji>: <imperative>` (`feat ✨`, `fix 🐛`, `docs 📝`, …).
- One concern per commit. Do not mix speech files with unrelated CSS.
- Label GitHub issues/PRs with `agent:<profile>` (and `enhancement` /
  `bug` as needed).
- Merge PRs that both touch `index.html` **one at a time**. Rebase the
  other after the first lands.
- Reviews one at a time. Independent APPROVE is local readiness. Do not
  merge on a self-report.
- Pages only updates when `main` updates. A commit is not live until
  merged.

## Boundaries

### Always

- Keep the app static: no runtime TTS, no API keys in the browser, no
  network speech.
- Match Dutch child copy exactly between HTML, inventory, manifest, and
  MP3 text.
- Hide play UI until a meal exists.
- Put overlay shade behind an opaque card, full viewport.
- Inspect full-page visuals yourself.
- Stop when `OPENAI_API_KEY` is missing.
- English or Dutch in agent output. Never Chinese.

### Ask first

- New child-facing features that change the loop (map, new rewards, new
  meals).
- Regenerating the **entire** existing 54-clip pack (cost + review).
- Merging to `main` / treating Pages as updated.
- Using edge-tts or any non-marin voice “just this once”.
- Deleting `scripts/regenerate_edge_tts.py`.

### Never

- Fall back to edge-tts / Fenna when OpenAI is unavailable.
- Commit secrets, BWS IDs, or `_generation_run.json`.
- Add runtime `speechSynthesis` or provider fetches from `index.html`.
- Claim a screenshot is good without opening it.
- Ship a mixed-voice pack with a lying marin manifest.
- Pressure copy, dark patterns, tracking, ads, accounts.
- Start parked work (for example issue #9) while a merge-blocking speech
  or overlay defect is open.

## Common tasks

### Change child-visible copy

1. Edit the string in `index.html`.
2. Update `scripts/speech_inventory.py` with the same words.
3. Generate the clip with the OpenAI script (stop if no key).
4. Rebuild the manifest and run the validator + Node suites.
5. Wire `playSpeech("<id>")` at the moment the line appears.

### Add a modal / overlay

1. Reuse the dimmer recipe: full-viewport scrim, solid card, z-index
   above confetti (30).
2. Lock page scroll while open if the page can grow past one screen.
3. Full-page Playwright or browser shot of the **open** dialog, not a
   crop. Comment it on the PR with `?raw=true`.

### Fix a visual bug Elvee circled

1. Open the attached image with vision. Do not guess.
2. Patch, then take a new full-page shot of the same state.
3. Compare. If the leak is still there, do not push “fixed”.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Game text shows through a dialog | Card is inside a translucent overlay. Split scrim + opaque box. |
| Shade stops halfway down the page | Overlay is `100vh` / `fixed` while the page scrolls. Cover the document, keep the card in the viewport. |
| Confetti on top of copy | Confetti z-index 30 above the dialog. Raise the dialog. |
| Validator green, voice still Fenna | Manifest claimed openai; files were 48 kbps. Probe bitrate. |
| Worker “finished” TTS without a key | It used edge-tts. Reject the pack. Block the card. |
| End / Schatkist tests fail after meal-first | Stub never called `selectMeal`. |
| PR image missing on GitHub | Body used a relative path. Post a comment with blob `?raw=true`. |
| Two `index.html` PRs conflict | Merge one, rebase the other. |

## Language

Product copy is Dutch. Agent discussion may be Dutch or English. Do not
output Chinese. Do not “improve” child lines into adult phrasing.

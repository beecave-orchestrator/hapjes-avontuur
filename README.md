# Hapjes Avontuur

Dutch kids snack-encouragement game. Single-page static app for GitHub Pages.

🔊 **Live (from `main`):** [https://beecave-orchestrator.github.io/hapjes-avontuur/](https://beecave-orchestrator.github.io/hapjes-avontuur/)

## What is this?

A cheerful browser game that celebrates every snack ("hapje") a child takes.

- **No accounts, no tracking, no ads** — just a fun counter and encouraging voice.
- **Privacy by design:** all audio is pre-generated and played locally. No runtime TTS, no network calls.
- **AI disclosure:** the voice is AI-generated (OpenAI TTS) and clearly labeled in the UI.

## How to play

1. Open the [live page](https://beecave-orchestrator.github.io/hapjes-avontuur/).
2. Tap the 🔊 toggle to enable sound.
3. Tap the big snack button for every "hapje" — the game cheers you on!

## How to run locally

Clone the repo, open `index.html` in any browser. No build step, no server.

## Technical details

- **Static audio architecture:** all speech is pre-generated, committed as MP3, and played by stable ID.
- **Frozen line inventory:** 16 Dutch lines (start, 10 encouragements, 5 rewards).
- **Provider/model/voice:** OpenAI `gpt-4o-mini-tts` / `marin` (warm, clear, child-friendly).
- **Regeneration:** documented in [docs/static-tts-assets.md](docs/static-tts-assets.md) (requires `OPENAI_API_KEY` in the environment).

## License & content

- Game copy and voice lines: original project content for personal/family use.
- Spoken audio: AI-generated with OpenAI TTS, disclosed in the UI.

# Static TTS Assets

## Purpose

Durable technical documentation for the static speech pack: asset IDs, inventory rules, provider/model/voice provenance, exact generation instructions, manifest structure, validation procedure, and regeneration constraints.

## Asset inventory

Stable IDs are frozen against `index.html` copy:

| ID | Category | Dutch source text |
|---------------|------------------|--------------------------------------------|
| `start` | start/reset | Klaar voor de eerste superhap? |
| `msg_01` … `msg_10` | encouragements | `messages[]` in order (`msg_03` = **Super goed bezig!**) |
| `reward_3` | reward @ 3 | title + body (see decision) |
| `reward_5` | reward @ 5 | title + body |
| `reward_10` | reward @ 10 | title + body |
| `reward_15` | reward @ 15 | title + body |
| `reward_20` | reward @ 20 | title + body |

**Reward decision:** each reward is **one** spoken clip combining `title` and `body` as `"{title} {body}"` for a single modal announcement.

## Generation provenance

| Field | Value |
|---------------|--------------------------------------------|
| Provider | OpenAI TTS (`POST /v1/audio/speech`) |
| Model | `gpt-4o-mini-tts` |
| Voice | `marin` |
| Locale | Dutch input (`nl-NL` product copy) |
| Format | MP3 (measured on disk via ffprobe) |
| Instructions | Warm, clear, encouraging, child-friendly |
| Credentials | `OPENAI_API_KEY` in the process environment only — **never** committed or looked up from the repo |

## Regeneration instructions

Requires `OPENAI_API_KEY` already present in the environment:

```bash
# The generator reads OPENAI_API_KEY from the environment only.
test -n "$OPENAI_API_KEY" || { echo "OPENAI_API_KEY is not set"; exit 1; }

python3 scripts/generate_openai_dutch_v1.py
python3 scripts/build_manifest.py
python3 scripts/validate_audio_assets.py
```

Do not commit temporary files such as `audio/_generation_run.json`.

## Manifest structure

`audio/manifest.json` maps stable IDs to:

- `path`: relative MP3 path
- `text`: exact Dutch source text
- `bytes`: file size in bytes
- `sha256`: SHA-256 digest of the MP3 file
- `codec`: measured codec parameters (bitrate, channels, sample rate)

## Validation procedure

```bash
python3 scripts/validate_audio_assets.py
```

Checks:

- Every manifest key has a playable MP3 path.
- Headers look like MPEG.
- Bytes and SHA-256 match.
- Dutch source text matches `index.html` (including `Super goed bezig!`).
- AI disclosure is present in the UI.
- Generation provenance is OpenAI.
- HTML has no network-TTS / API-key patterns.

## Constraints

- **Do not alter** game logic, audio assets, generated manifest values, or runtime behaviour.
- **Do not mention** BWS, BWS secret IDs, or repository-side credential management.
- **Keep** the OpenAI AI-voice disclosure accurate and visible in the product.

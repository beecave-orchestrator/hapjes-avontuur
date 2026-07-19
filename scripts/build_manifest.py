#!/usr/bin/env python3
"""Build audio/manifest.json from frozen IDs + on-disk MP3 sizes/hashes.

Also records measured codec parameters via ffprobe when available.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
SCRIPTS = Path(__file__).resolve().parent

import sys

sys.path.insert(0, str(SCRIPTS))
from speech_inventory import (  # noqa: E402
    ENTRIES,
    INSTRUCTIONS,
    LOCALE,
    MODEL,
    PROVIDER,
    RESPONSE_FORMAT,
    VOICE,
)


def ffprobe_file(path: Path) -> dict:
    if not shutil.which("ffprobe"):
        return {}
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=codec_name,sample_rate,channels,bit_rate",
        "-show_entries",
        "format=format_name,duration,bit_rate",
        "-of",
        "json",
        str(path),
    ]
    try:
        raw = subprocess.check_output(cmd, text=True)
        data = json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return {}
    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    stream = streams[0] if streams else {}
    out = {}
    if stream.get("codec_name"):
        out["codec"] = stream["codec_name"]
    if stream.get("sample_rate"):
        out["sample_rate_hz"] = int(stream["sample_rate"])
    if stream.get("channels") is not None:
        ch = int(stream["channels"])
        out["channels"] = ch
        out["channels_label"] = "mono" if ch == 1 else ("stereo" if ch == 2 else str(ch))
    br = stream.get("bit_rate") or fmt.get("bit_rate")
    if br:
        out["bit_rate_bps"] = int(br)
    if fmt.get("duration"):
        out["duration_s"] = round(float(fmt["duration"]), 3)
    if fmt.get("format_name"):
        out["container"] = fmt["format_name"]
    return out


def majority(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def main() -> None:
    clips = {}
    total = 0
    probes = []
    for entry in ENTRIES:
        path = AUDIO / entry["file"]
        if not path.is_file():
            raise SystemExit(f"missing asset for {entry['id']}: {path}")
        data = path.read_bytes()
        size = len(data)
        if size < 500:
            raise SystemExit(f"asset too small for {entry['id']}: {size}")
        if not (data[:3] == b"ID3" or data[0] == 0xFF):
            raise SystemExit(f"not an MP3 header for {entry['id']}")
        sha = hashlib.sha256(data).hexdigest()
        total += size
        probe = ffprobe_file(path)
        probes.append(probe)
        item = {
            "id": entry["id"],
            "category": entry["category"],
            "text": entry["text"],
            "file": entry["file"],
            "path": f"audio/{entry['file']}",
            "source": entry["source"],
            "bytes": size,
            "sha256": sha,
            "format": "mp3",
        }
        if probe:
            item["probe"] = probe
        if entry["category"] == "reward":
            item["hapjes"] = entry["hapjes"]
            item["title"] = entry["title"]
            item["body"] = entry["body"]
            item["spoken_as"] = "title_plus_body"
        clips[entry["id"]] = item

    gen_probe = {
        "codec": majority(p.get("codec") for p in probes),
        "sample_rate_hz": majority(p.get("sample_rate_hz") for p in probes),
        "bit_rate_bps": majority(p.get("bit_rate_bps") for p in probes),
        "channels": majority(p.get("channels_label") for p in probes),
        "container": majority(p.get("container") for p in probes),
    }

    # Prefer generation-run timestamp when present.
    generated_at = None
    run_log = AUDIO / "_generation_run.json"
    if run_log.is_file():
        try:
            generated_at = json.loads(run_log.read_text(encoding="utf-8")).get(
                "generated_at_utc"
            )
        except (json.JSONDecodeError, OSError):
            generated_at = None
    if not generated_at:
        generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    manifest = {
        "version": "2.0.0",
        "game": "hapjes-avontuur",
        "locale": LOCALE,
        "architecture": "static-pregenerated",
        "runtime_tts": False,
        "browser_api_keys": False,
        "ai_generated_speech": True,
        "generation": {
            "provider": PROVIDER,
            "endpoint": "POST /v1/audio/speech",
            "model": MODEL,
            "voice": VOICE,
            "locale": LOCALE,
            "response_format": RESPONSE_FORMAT,
            "instructions": INSTRUCTIONS,
            "codec": gen_probe.get("codec") or "mp3",
            "sample_rate_hz": gen_probe.get("sample_rate_hz"),
            "bit_rate_bps": gen_probe.get("bit_rate_bps"),
            "channels": gen_probe.get("channels"),
            "container": gen_probe.get("container"),
            "probe_note": (
                "Codec parameters measured with ffprobe on the committed MP3s; "
                "not copied from a prior xAI pack."
            ),
            "generated_at_utc": generated_at,
            "tooling": (
                "scripts/generate_openai_dutch_v1.py via OpenAI audio.speech "
                f"({MODEL}, voice={VOICE}); credentials via OPENAI_API_KEY / BWS only"
            ),
            "supersedes": "xAI ara Dutch v1 static pack (main prior to this revision)",
        },
        "decisions": {
            "reward_title_body": (
                "Each reward is ONE clip combining title + body "
                '("{title} {body}") for a single modal announcement. '
                "Separate title/body files were not generated."
            ),
            "stable_ids": (
                "start; msg_01..msg_10 match messages[] order; "
                "reward_{3,5,10,15,20} match rewards keys / badge thresholds."
            ),
            "msg_03_wording": (
                'User-approved split wording "Super goed bezig!" '
                "(not the single-token Supergoed form)."
            ),
            "provider_choice": (
                "Full replacement with OpenAI gpt-4o-mini-tts voice marin after "
                "unsatisfactory Dutch quality from the prior xAI set."
            ),
            "disclosure": (
                "Visible in-game note that speech is AI-generated "
                "(OpenAI TTS usage policy)."
            ),
        },
        "counts": {
            "clips": len(clips),
            "start_reset": 1,
            "encouragement": 10,
            "reward": 5,
            "total_bytes": total,
        },
        "clips": clips,
        "lookup_helpers": {
            "encouragement_by_messages_index": {
                str(i): f"msg_{i+1:02d}" for i in range(10)
            },
            "reward_by_hapjes": {
                "3": "reward_3",
                "5": "reward_5",
                "10": "reward_10",
                "15": "reward_15",
                "20": "reward_20",
            },
            "start_reset_id": "start",
        },
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    out = AUDIO / "manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} clips={len(clips)} total_bytes={total} probe={gen_probe}")


if __name__ == "__main__":
    main()

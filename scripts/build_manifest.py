#!/usr/bin/env python3
"""Build audio/manifest.json from the frozen inventory + on-disk MP3s.

The inventory (stable IDs, exact Dutch text) lives in
scripts/speech_inventory.py — the single source of truth shared with the
generators. This script only measures what is on disk.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from speech_inventory import CHILD_FACING_CATEGORIES, ENTRIES  # noqa: E402


def main() -> None:
    clips = {}
    total = 0
    counts: dict[str, int] = {}
    for entry in ENTRIES:
        path = AUDIO / entry["file"]
        if not path.is_file():
            raise SystemExit(f"missing asset for {entry['id']}: {path}")
        data = path.read_bytes()
        size = len(data)
        if size < 500:
            raise SystemExit(f"asset too small for {entry['id']}: {size}")
        # MPEG ADTS or ID3
        if not (data[:3] == b"ID3" or data[0] == 0xFF):
            raise SystemExit(f"not an MP3 header for {entry['id']}")
        sha = hashlib.sha256(data).hexdigest()
        total += size
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
        if entry["category"] == "reward":
            item["hapjes"] = entry["hapjes"]
            item["title"] = entry["title"]
            item["body"] = entry["body"]
            item["spoken_as"] = "title_plus_body"
        clips[entry["id"]] = item
        counts[entry["category"]] = counts.get(entry["category"], 0) + 1

    manifest = {
        "version": "1.1.0",
        "game": "hapjes-avontuur",
        "locale": "nl-NL",
        "architecture": "static-pregenerated",
        "runtime_tts": False,
        "browser_api_keys": False,
        "generation": {
            "provider": "openai",
            "endpoint": "POST /v1/audio/speech",
            "model": "gpt-4o-mini-tts",
            "voice": "marin",
            "language": "nl",
            "language_note": (
                "Issue #15 child-facing clips and the existing pack use "
                "OpenAI gpt-4o-mini-tts voice marin. edge-tts is not an "
                "accepted fallback."
            ),
            "sample_rate_hz": 24000,
            "bit_rate_bps": 48000,
            "codec": "mp3",
            "channels": "mono",
            "auto_speech_tags": False,
            "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tooling": "scripts/generate_openai_dutch_v1.py",
        },
        "decisions": {
            "reward_title_body": (
                "Each reward is ONE clip combining title + body "
                "(\"{title} {body}\") for a single modal announcement. "
                "Separate title/body files were not generated for v1."
            ),
            "picker_title_note": (
                "Each picker step is ONE clip combining the visible title + "
                "note (issue #15), mirroring the reward title+body pattern."
            ),
            "stable_ids": (
                "start; msg_01..msg_10 match messages[] order; "
                "reward_{3,5,10,15,20} match rewards keys / badge thresholds; "
                "picker_title_{1,2}; meal_<key>/extra_<key> match picker "
                "options; chip_kies + chip_eat_<key> match meal chip lines; "
                "schatkist_* match dialog copy; unlock_<key> and "
                "unlock_einde_<key> match unlock announcements."
            ),
            "numeric_lines_not_frozen": (
                "Issue #15: goal-card counters (\"X van Y\", \"nog X "
                "muntjes\", pot counts, progress \"0 / 5\") are deliberately "
                "not frozen as clips. They change every hap; re-speaking "
                "running numbers each bite would add counting pressure the "
                "game explicitly avoids (issue #5/#7 pressure-free rule)."
            ),
            "oudermenu_silent": (
                "The parent/info menu (issue #8) is not child-facing and "
                "stays silent by standing merge rule."
            ),
        },
        "counts": {
            "clips": len(clips),
            **{k: v for k, v in sorted(counts.items())},
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
            "meal_by_key": {
                e["id"].removeprefix("meal_"): e["id"]
                for e in ENTRIES
                if e["category"] == "picker_name" and e["id"].startswith("meal_")
            },
            "extra_by_key": {
                e["id"].removeprefix("extra_"): e["id"]
                for e in ENTRIES
                if e["category"] == "picker_name" and e["id"].startswith("extra_")
            },
            "chip_eat_by_meal_key": {
                e["id"].removeprefix("chip_eat_"): e["id"]
                for e in ENTRIES
                if e["id"].startswith("chip_eat_")
            },
            "unlock_by_item": {
                e["id"].removeprefix("unlock_"): e["id"]
                for e in ENTRIES
                if e["category"] == "unlock" and not e["id"].startswith("unlock_einde_")
            },
            "unlock_einde_by_item": {
                e["id"].removeprefix("unlock_einde_"): e["id"]
                for e in ENTRIES
                if e["id"].startswith("unlock_einde_")
            },
            "start_reset_id": "start",
        },
        "child_facing_categories": CHILD_FACING_CATEGORIES,
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    out = AUDIO / "manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} clips={len(clips)} total_bytes={total}")


if __name__ == "__main__":
    main()

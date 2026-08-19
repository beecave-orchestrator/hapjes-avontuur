#!/usr/bin/env python3
"""Regenerate Hapjes Avontuur Dutch static TTS assets with edge-tts.

Canonical route for the committed pack (provenance since issue #7): one warm
Dutch neural voice (nl-NL-FennaNeural), no secrets, no runtime TTS.

Usage:
  python3 scripts/regenerate_edge_tts.py                 # regenerate all
  python3 scripts/regenerate_edge_tts.py --only-missing  # generate only
                                                         # absent clips

The inventory lives in scripts/speech_inventory.py (single source of truth
shared with build_manifest.py and generate_openai_dutch_v1.py).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audio"
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from speech_inventory import ENTRIES  # noqa: E402

# Voice: warm, clear Dutch female voice (kid-friendly).
VOICE = "nl-NL-FennaNeural"
RATE = "+0%"
PITCH = "+0Hz"


async def generate_one(entry: dict) -> None:
    path = OUT / entry["file"]
    tts = edge_tts.Communicate(entry["text"], VOICE, rate=RATE, pitch=PITCH)
    await tts.save(str(path))
    size = path.stat().st_size
    if size < 500:
        raise RuntimeError(f"audio too small ({size} bytes) for {entry['id']}")
    print(f"  ok {entry['id']} -> {entry['file']} ({size} bytes)", flush=True)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="generate only clips whose MP3 is not on disk yet",
    )
    args = parser.parse_args()

    entries = ENTRIES
    if args.only_missing:
        entries = [e for e in ENTRIES if not (OUT / e["file"]).is_file()]
        if not entries:
            print("nothing missing; all clips present")
            return 0

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"BATCH voice={VOICE} n={len(entries)}", flush=True)
    errors = []
    for i, entry in enumerate(entries, 1):
        print(f"[{i}/{len(entries)}] {entry['id']}", flush=True)
        try:
            await generate_one(entry)
        except Exception as exc:
            print(f"  FAIL {entry['id']}: {type(exc).__name__}: {exc}", flush=True)
            errors.append({"id": entry["id"], "error": str(exc)})
    if errors:
        print(json.dumps({"ok": len(entries) - len(errors), "fail": len(errors), "errors": errors}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": len(entries), "fail": 0, "voice": VOICE}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

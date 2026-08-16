#!/usr/bin/env python3
"""Regenerate Hapjes Avontuur Dutch static TTS assets with edge-tts.

Issue #7 changed the copy (neutral, pressure-free) and added three end-state
clips. Regenerate all clips with a warm Dutch edge-tts voice for consistency.

No secrets in repo. Requires: pip install edge-tts
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audio"

# Voice: warm, clear Dutch female voice (kid-friendly).
VOICE = "nl-NL-FennaNeural"
RATE = "+0%"
PITCH = "+0Hz"

# Frozen inventory from index.html (post-start spoken lines).
# Must stay in sync with scripts/build_manifest.py ENTRIES.
ENTRIES = [
    {"id": "start", "text": "Klaar voor de eerste superhap?", "file": "start.mp3"},
    {"id": "msg_01", "text": "Wat een lekkere hap!", "file": "msg_01.mp3"},
    {"id": "msg_02", "text": "Wat fijn dat je eet!", "file": "msg_02.mp3"},
    {"id": "msg_03", "text": "Supergoed bezig!", "file": "msg_03.mp3"},
    {"id": "msg_04", "text": "Hapjesheld gespot!", "file": "msg_04.mp3"},
    {"id": "msg_05", "text": "Lekker dat je proeft!", "file": "msg_05.mp3"},
    {"id": "msg_06", "text": "Jij bent echt goed in dit spel!", "file": "msg_06.mp3"},
    {"id": "msg_07", "text": "Wat een gezellige hap!", "file": "msg_07.mp3"},
    {"id": "msg_08", "text": "Mega trots op jou!", "file": "msg_08.mp3"},
    {"id": "msg_09", "text": "Dat was een dappere hap!", "file": "msg_09.mp3"},
    {"id": "msg_10", "text": "Je smaakpapillen gaan op avontuur!", "file": "msg_10.mp3"},
    {"id": "reward_3", "text": "Ster verdiend! Je hebt 3 hapjes gehaald. Superknap!", "file": "reward_3.mp3"},
    {"id": "reward_5", "text": "Level omhoog! 5 hapjes! De eenhoorn is trots op jou.", "file": "reward_5.mp3"},
    {"id": "reward_10", "text": "Beker gewonnen! 10 hapjes! Wat een avontuur.", "file": "reward_10.mp3"},
    {"id": "reward_15", "text": "Raketboost! 15 hapjes! Wat een leuke ontdekkingstocht.", "file": "reward_15.mp3"},
    {"id": "reward_20", "text": "Kroon verdiend! 20 hapjes! Wat een mooie reis.", "file": "reward_20.mp3"},
    {"id": "end", "text": "Avontuur klaar! Verder eten is niet nodig. Je mag stoppen wanneer je wilt.", "file": "end.mp3"},
    {"id": "end_done", "text": "Avontuur klaar! Je mag stoppen wanneer je wilt.", "file": "end_done.mp3"},
    {"id": "bonus", "text": "Bonusavontuur! Verder eten is niet nodig, maar mag wel.", "file": "bonus.mp3"},
]


async def generate_one(entry: dict) -> None:
    path = OUT / entry["file"]
    tts = edge_tts.Communicate(entry["text"], VOICE, rate=RATE, pitch=PITCH)
    await tts.save(str(path))
    size = path.stat().st_size
    if size < 500:
        raise RuntimeError(f"audio too small ({size} bytes) for {entry['id']}")
    print(f"  ok {entry['id']} -> {entry['file']} ({size} bytes)", flush=True)


async def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"BATCH voice={VOICE} n={len(ENTRIES)}", flush=True)
    errors = []
    for i, entry in enumerate(ENTRIES, 1):
        print(f"[{i}/{len(ENTRIES)}] {entry['id']}", flush=True)
        try:
            await generate_one(entry)
        except Exception as exc:
            print(f"  FAIL {entry['id']}: {type(exc).__name__}: {exc}", flush=True)
            errors.append({"id": entry["id"], "error": str(exc)})
    if errors:
        print(json.dumps({"ok": len(ENTRIES) - len(errors), "fail": len(errors), "errors": errors}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": len(ENTRIES), "fail": 0, "voice": VOICE}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

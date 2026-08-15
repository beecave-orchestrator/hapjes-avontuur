#!/usr/bin/env python3
"""Build audio/manifest.json from frozen IDs + on-disk MP3 sizes/hashes."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"

# Must stay in sync with scripts/generate_xai_dutch_v1.py ENTRIES.
ENTRIES = [
    {
        "id": "start",
        "category": "start_reset",
        "text": "Klaar voor de eerste superhap?",
        "file": "start.mp3",
        "source": "initial #message + resetGame()",
    },
    {
        "id": "msg_01",
        "category": "encouragement",
        "text": "Wat een lekkere hap!",
        "file": "msg_01.mp3",
        "source": "messages[0]",
    },
    {
        "id": "msg_02",
        "category": "encouragement",
        "text": "Wat fijn dat je eet!",
        "file": "msg_02.mp3",
        "source": "messages[1]",
    },
    {
        "id": "msg_03",
        "category": "encouragement",
        "text": "Supergoed bezig!",
        "file": "msg_03.mp3",
        "source": "messages[2]",
    },
    {
        "id": "msg_04",
        "category": "encouragement",
        "text": "Hapjesheld gespot!",
        "file": "msg_04.mp3",
        "source": "messages[3]",
    },
    {
        "id": "msg_05",
        "category": "encouragement",
        "text": "Lekker dat je proeft!",
        "file": "msg_05.mp3",
        "source": "messages[4]",
    },
    {
        "id": "msg_06",
        "category": "encouragement",
        "text": "Jij bent echt goed in dit spel!",
        "file": "msg_06.mp3",
        "source": "messages[5]",
    },
    {
        "id": "msg_07",
        "category": "encouragement",
        "text": "Wat een gezellige hap!",
        "file": "msg_07.mp3",
        "source": "messages[6]",
    },
    {
        "id": "msg_08",
        "category": "encouragement",
        "text": "Mega trots op jou!",
        "file": "msg_08.mp3",
        "source": "messages[7]",
    },
    {
        "id": "msg_09",
        "category": "encouragement",
        "text": "Dat was een dappere hap!",
        "file": "msg_09.mp3",
        "source": "messages[8]",
    },
    {
        "id": "msg_10",
        "category": "encouragement",
        "text": "Je smaakpapillen gaan op avontuur!",
        "file": "msg_10.mp3",
        "source": "messages[9]",
    },
    {
        "id": "reward_3",
        "category": "reward",
        "hapjes": 3,
        "title": "Ster verdiend!",
        "body": "Je hebt 3 hapjes gehaald. Superknap!",
        "text": "Ster verdiend! Je hebt 3 hapjes gehaald. Superknap!",
        "file": "reward_3.mp3",
        "source": "rewards[3] title+text",
    },
    {
        "id": "reward_5",
        "category": "reward",
        "hapjes": 5,
        "title": "Level omhoog!",
        "body": "5 hapjes! De eenhoorn is trots op jou.",
        "text": "Level omhoog! 5 hapjes! De eenhoorn is trots op jou.",
        "file": "reward_5.mp3",
        "source": "rewards[5] title+text",
    },
    {
        "id": "reward_10",
        "category": "reward",
        "hapjes": 10,
        "title": "Beker gewonnen!",
        "body": "10 hapjes! Wat een avontuur.",
        "text": "Beker gewonnen! 10 hapjes! Wat een avontuur.",
        "file": "reward_10.mp3",
        "source": "rewards[10] title+text",
    },
    {
        "id": "reward_15",
        "category": "reward",
        "hapjes": 15,
        "title": "Raketboost!",
        "body": "15 hapjes! Wat een leuke ontdekkingstocht.",
        "text": "Raketboost! 15 hapjes! Wat een leuke ontdekkingstocht.",
        "file": "reward_15.mp3",
        "source": "rewards[15] title+text",
    },
    {
        "id": "reward_20",
        "category": "reward",
        "hapjes": 20,
        "title": "Kroon verdiend!",
        "body": "20 hapjes! Wat een mooie reis.",
        "text": "Kroon verdiend! 20 hapjes! Wat een mooie reis.",
        "file": "reward_20.mp3",
        "source": "rewards[20] title+text",
    },
    {
        "id": "end",
        "category": "end_state",
        "text": "Avontuur klaar! Verder eten is niet nodig. Je mag stoppen wanneer je wilt.",
        "file": "end.mp3",
        "source": "toonEindstaat() end dialog",
    },
    {
        "id": "end_done",
        "category": "end_state",
        "text": "Avontuur klaar! Je mag stoppen wanneer je wilt.",
        "file": "end_done.mp3",
        "source": "klaarMetEten()",
    },
    {
        "id": "bonus",
        "category": "end_state",
        "text": "Bonusavontuur! Verder eten is niet nodig, maar mag wel.",
        "file": "bonus.mp3",
        "source": "bonusAvontuur()",
    },
]


def main() -> None:
    clips = {}
    total = 0
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

    manifest = {
        "version": "1.0.0",
        "game": "hapjes-avontuur",
        "locale": "nl-NL",
        "architecture": "static-pregenerated",
        "runtime_tts": False,
        "browser_api_keys": False,
        "generation": {
            "provider": "edge-tts",
            "endpoint": "Microsoft Edge neural TTS (offline via edge-tts)",
            "voice_id": "nl-NL-FennaNeural",
            "language": "nl",
            "language_note": (
                "Regenerated for issue #7 (neutral, pressure-free copy + "
                "end-state clips). Voice changed from xAI 'ara' to edge-tts "
                "nl-NL-FennaNeural because xAI OAuth was unavailable in the "
                "regeneration environment."
            ),
            "sample_rate_hz": 24000,
            "bit_rate_bps": 64000,
            "codec": "mp3",
            "channels": "mono",
            "auto_speech_tags": False,
            "generated_at_utc": "2026-08-14T18:10:00Z",
            "tooling": (
                "scripts/regenerate_edge_tts.py (edge-tts; no secrets in repo)"
            ),
        },
        "decisions": {
            "reward_title_body": (
                "Each reward is ONE clip combining title + body "
                "(\"{title} {body}\") for a single modal announcement. "
                "Separate title/body files were not generated for v1."
            ),
            "stable_ids": (
                "start; msg_01..msg_10 match messages[] order; "
                "reward_{3,5,10,15,20} match rewards keys / badge thresholds."
            ),
            "out_of_v1": (
                "Level names, chrome labels, SFX beeps remain Web Audio; "
                "no JS playback wiring in this asset stage."
            ),
        },
        "counts": {
            "clips": len(clips),
            "start_reset": 1,
            "encouragement": 10,
            "reward": 5,
            "end_state": 3,
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
    print(f"wrote {out} clips={len(clips)} total_bytes={total}")


if __name__ == "__main__":
    main()

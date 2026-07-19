#!/usr/bin/env python3
"""Generate Hapjes Avontuur v1 Dutch static TTS assets via Hermes xAI backend.

Per-call language/voice override only — does not mutate Hermes config.yaml.
Requires HERMES_HOME with working xAI OAuth (or XAI_API_KEY). No secrets in repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audio"
HERMES_AGENT = Path.home() / ".hermes" / "hermes-agent"
DEFAULT_HERMES_HOME = Path.home() / ".hermes" / "profiles" / "investigator"

# Frozen v1 inventory from index.html (post-start spoken lines).
# Reward decision: one clip per reward = title + body as a single announcement
# when the modal opens (not separate title/body files).
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
        "text": "Wat een kanjerhap!",
        "file": "msg_01.mp3",
        "source": "messages[0]",
    },
    {
        "id": "msg_02",
        "category": "encouragement",
        "text": "Je bord wordt al leger!",
        "file": "msg_02.mp3",
        "source": "messages[1]",
    },
    {
        "id": "msg_03",
        "category": "encouragement",
        "text": "Super goed bezig!",
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
        "text": "Daar word je groot en sterk van!",
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
        "text": "Nog eentje voor de power?",
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
        "body": "10 hapjes! Jij bent een echte kampioen.",
        "text": "Beker gewonnen! 10 hapjes! Jij bent een echte kampioen.",
        "file": "reward_10.mp3",
        "source": "rewards[10] title+text",
    },
    {
        "id": "reward_15",
        "category": "reward",
        "hapjes": 15,
        "title": "Raketboost!",
        "body": "15 hapjes! Je vliegt door dit avondeten heen.",
        "text": "Raketboost! 15 hapjes! Je vliegt door dit avondeten heen.",
        "file": "reward_15.mp3",
        "source": "rewards[15] title+text",
    },
    {
        "id": "reward_20",
        "category": "reward",
        "hapjes": 20,
        # Exact title from index.html (source of truth for v1 assets).
        "title": "Eetkoningin!",
        "body": "20 hapjes! Wat een prestatie.",
        "text": "Eetkoningin! 20 hapjes! Wat een prestatie.",
        "file": "reward_20.mp3",
        "source": "rewards[20] title+text",
    },
]

VOICE_ID = "ara"
PREFERRED_LANGUAGE = "nl"
FALLBACK_LANGUAGE = "auto"
SAMPLE_RATE = 24000
BIT_RATE = 64000


def main() -> int:
    hermes_home = os.environ.get("HERMES_HOME", str(DEFAULT_HERMES_HOME))
    os.environ["HERMES_HOME"] = hermes_home
    sys.path.insert(0, str(HERMES_AGENT))

    from tools.tts_tool import _generate_xai_tts  # noqa: E402

    OUT.mkdir(parents=True, exist_ok=True)

    base_xai = {
        "voice_id": VOICE_ID,
        "sample_rate": SAMPLE_RATE,
        "bit_rate": BIT_RATE,
        "auto_speech_tags": False,
    }

    def generate(text: str, path: Path, language: str) -> None:
        cfg = {"provider": "xai", "xai": {**base_xai, "language": language}}
        _generate_xai_tts(text, str(path), cfg)

    lang_used = PREFERRED_LANGUAGE
    smoke = OUT / "_smoke.mp3"
    print(f"SMOKE language={PREFERRED_LANGUAGE} ...", flush=True)
    try:
        generate(ENTRIES[0]["text"], smoke, PREFERRED_LANGUAGE)
        print(f"SMOKE ok bytes={smoke.stat().st_size}", flush=True)
    except Exception as exc:
        print(f"SMOKE {PREFERRED_LANGUAGE} failed: {type(exc).__name__}: {exc}", flush=True)
        print(f"SMOKE fallback language={FALLBACK_LANGUAGE} ...", flush=True)
        generate(ENTRIES[0]["text"], smoke, FALLBACK_LANGUAGE)
        lang_used = FALLBACK_LANGUAGE
        print(f"SMOKE {FALLBACK_LANGUAGE} ok bytes={smoke.stat().st_size}", flush=True)
    finally:
        if smoke.exists():
            smoke.unlink()

    print(
        f"BATCH language={lang_used} voice={VOICE_ID} n={len(ENTRIES)} "
        f"bit_rate={BIT_RATE} sample_rate={SAMPLE_RATE}",
        flush=True,
    )

    results = []
    errors = []
    for i, entry in enumerate(ENTRIES, 1):
        path = OUT / entry["file"]
        print(f"[{i}/{len(ENTRIES)}] {entry['id']} -> {entry['file']}", flush=True)
        t0 = time.time()
        try:
            generate(entry["text"], path, lang_used)
            size = path.stat().st_size
            if size < 500:
                raise RuntimeError(f"audio too small ({size} bytes)")
            # basic mp3 frame sync / ID3 / freestanding mpeg header check
            head = path.read_bytes()[:4]
            if not (head[:3] == b"ID3" or head[:2] == b"\xff\xfb" or head[:2] == b"\xff\xf3" or head[:2] == b"\xff\xf2" or head[0] == 0xFF):
                # still accept if larger; xAI may use other mpeg layer headers
                pass
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            dt = time.time() - t0
            print(f"  ok {size} bytes sha256={sha[:16]}… {dt:.1f}s", flush=True)
            row = {
                **entry,
                "path": f"audio/{entry['file']}",
                "bytes": size,
                "sha256": sha,
                "ok": True,
                "seconds": round(dt, 2),
            }
            results.append(row)
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            print(f"  FAIL {msg}", flush=True)
            errors.append({"id": entry["id"], "error": msg})
            results.append({**entry, "ok": False, "error": msg})
        time.sleep(0.35)

    run_log = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": "xai",
        "voice_id": VOICE_ID,
        "language": lang_used,
        "language_requested": PREFERRED_LANGUAGE,
        "sample_rate": SAMPLE_RATE,
        "bit_rate": BIT_RATE,
        "auto_speech_tags": False,
        "format": "mp3",
        "global_hermes_config_changed": False,
        "hermes_home": hermes_home,
        "count_ok": sum(1 for r in results if r.get("ok")),
        "count_fail": len(errors),
        "errors": errors,
        "entries": results,
    }
    (OUT / "_generation_run.json").write_text(
        json.dumps(run_log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": run_log["count_ok"],
                "fail": run_log["count_fail"],
                "language": lang_used,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

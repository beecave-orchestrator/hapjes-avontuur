#!/usr/bin/env python3
"""Generate Hapjes Avontuur Dutch static TTS assets via OpenAI gpt-4o-mini-tts.

Canonical offline route for committed MP3s. Requires OPENAI_API_KEY in the
process environment (injected by Hermes/BWS outside this repo). Never prints or
writes the API key. Does not look up secrets and does not mutate Hermes
config.yaml.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audio"
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from speech_inventory import (  # noqa: E402
    ENTRIES,
    INSTRUCTIONS,
    MODEL,
    PROVIDER,
    RESPONSE_FORMAT,
    VOICE,
)

HERMES_PY = Path.home() / ".hermes" / "hermes-agent" / "venv" / "bin" / "python"


def parse_args(argv):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="generate only clips whose MP3 is not on disk yet",
    )
    parser.add_argument(
        "--ids",
        nargs="*",
        default=[],
        help="generate only these stable IDs (space separated)",
    )
    return parser.parse_args(argv)


def _strip_wrapping_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return value.strip()


def resolve_openai_api_key() -> str:
    """Return OPENAI_API_KEY from the process environment only."""
    key = _strip_wrapping_quotes(os.environ.get("OPENAI_API_KEY", "") or "")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set")
    return key


def generate_one(client, text: str, path: Path) -> None:
    response = client.audio.speech.create(
        model=MODEL,
        voice=VOICE,
        input=text,
        response_format=RESPONSE_FORMAT,
        instructions=INSTRUCTIONS,
    )
    # openai SDK may warn about stream_to_file; it still writes the full body.
    response.stream_to_file(str(path))


def main() -> int:
    args = parse_args(sys.argv[1:])

    # Selection happens before the venv re-exec so it survives the exec.
    entries = ENTRIES
    if args.ids:
        wanted = set(args.ids)
        unknown = wanted - {e["id"] for e in ENTRIES}
        if unknown:
            raise SystemExit(f"unknown ids: {sorted(unknown)}")
        entries = [e for e in ENTRIES if e["id"] in wanted]
    elif args.only_missing:
        entries = [e for e in ENTRIES if not (OUT / e["file"]).is_file()]
        if not entries:
            print("nothing missing; all clips present")
            return 0

    # Prefer Hermes venv (has openai package) when available.
    if HERMES_PY.is_file() and Path(sys.executable).resolve() != HERMES_PY.resolve():
        # Fail fast if the key is missing before re-exec; child inherits env.
        resolve_openai_api_key()
        env = os.environ.copy()
        forward = ["--only-missing"] if args.only_missing else []
        if args.ids:
            forward += ["--ids", *args.ids]
        return subprocess.call(
            [str(HERMES_PY), str(Path(__file__).resolve()), *forward],
            env=env,
        )

    from openai import OpenAI  # type: ignore

    key = resolve_openai_api_key()
    print(
        f"BATCH provider={PROVIDER} model={MODEL} voice={VOICE} "
        f"format={RESPONSE_FORMAT} n={len(entries)} openai_api_key=yes",
        flush=True,
    )

    client = OpenAI(api_key=key)
    OUT.mkdir(parents=True, exist_ok=True)

    smoke = OUT / "_smoke.mp3"
    print("SMOKE ...", flush=True)
    try:
        generate_one(client, entries[0]["text"], smoke)
        print(f"SMOKE ok bytes={smoke.stat().st_size}", flush=True)
    finally:
        if smoke.exists():
            smoke.unlink()

    results = []
    errors = []
    for i, entry in enumerate(entries, 1):
        path = OUT / entry["file"]
        print(f"[{i}/{len(entries)}] {entry['id']} -> {entry['file']}", flush=True)
        t0 = time.time()
        try:
            generate_one(client, entry["text"], path)
            data = path.read_bytes()
            size = len(data)
            if size < 500:
                raise RuntimeError(f"audio too small ({size} bytes)")
            if not (data[:3] == b"ID3" or data[0] == 0xFF):
                raise RuntimeError(f"bad mp3 header {data[:4]!r}")
            sha = hashlib.sha256(data).hexdigest()
            dt = time.time() - t0
            print(f"  ok {size} bytes sha256={sha[:16]}… {dt:.1f}s", flush=True)
            results.append(
                {
                    **entry,
                    "path": f"audio/{entry['file']}",
                    "bytes": size,
                    "sha256": sha,
                    "ok": True,
                    "seconds": round(dt, 2),
                }
            )
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            print(f"  FAIL {msg}", flush=True)
            errors.append({"id": entry["id"], "error": msg})
            results.append({**entry, "ok": False, "error": msg})
        time.sleep(0.25)

    run_log = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": PROVIDER,
        "endpoint": "POST /v1/audio/speech",
        "model": MODEL,
        "voice": VOICE,
        "response_format": RESPONSE_FORMAT,
        "instructions": INSTRUCTIONS,
        "format": RESPONSE_FORMAT,
        "global_hermes_config_changed": False,
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
                "provider": PROVIDER,
                "model": MODEL,
                "voice": VOICE,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate Hapjes Avontuur Dutch static TTS assets via OpenAI gpt-4o-mini-tts.

Canonical offline route for committed MP3s. Requires OPENAI_API_KEY in the
environment (or loads it from Bitwarden Secrets Manager when BWS_ACCESS_TOKEN
is available). Never prints or writes the API key. Does not mutate Hermes
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

BWS = Path.home() / ".hermes" / "bin" / "bws"
# Secret UUID for OPENAI_API_KEY in the Hermes BWS project (EU vault).
OPENAI_SECRET_ID = "17fac135-91b5-4467-b832-b48c00b7542c"
BWS_SERVER = "https://vault.bitwarden.eu"
HERMES_PY = Path.home() / ".hermes" / "hermes-agent" / "venv" / "bin" / "python"


def _strip_wrapping_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return value.strip()


def resolve_openai_api_key() -> str:
    key = _strip_wrapping_quotes(os.environ.get("OPENAI_API_KEY", "") or "")
    if key:
        return key
    if not os.environ.get("BWS_ACCESS_TOKEN"):
        raise SystemExit(
            "OPENAI_API_KEY is not set and BWS_ACCESS_TOKEN is unavailable. "
            "Export OPENAI_API_KEY or run with BWS access."
        )
    if not BWS.is_file():
        raise SystemExit(f"bws binary not found at {BWS}")
    proc = subprocess.run(
        [
            str(BWS),
            "secret",
            "get",
            OPENAI_SECRET_ID,
            "-u",
            BWS_SERVER,
            "-o",
            "env",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    line = proc.stdout.strip().splitlines()[-1]
    if not line.startswith("OPENAI_API_KEY="):
        raise SystemExit("unexpected bws env output for OPENAI_API_KEY")
    key = _strip_wrapping_quotes(line.split("=", 1)[1])
    if not key:
        raise SystemExit("empty OPENAI_API_KEY from bws")
    os.environ["OPENAI_API_KEY"] = key
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
    # Prefer Hermes venv (has openai package) when available.
    if HERMES_PY.is_file() and Path(sys.executable).resolve() != HERMES_PY.resolve():
        env = os.environ.copy()
        # Ensure key is resolved before re-exec so child inherits it.
        resolve_openai_api_key()
        return subprocess.call([str(HERMES_PY), str(Path(__file__).resolve()), *sys.argv[1:]], env=env)

    from openai import OpenAI  # type: ignore

    key = resolve_openai_api_key()
    print(
        f"BATCH provider={PROVIDER} model={MODEL} voice={VOICE} "
        f"format={RESPONSE_FORMAT} n={len(ENTRIES)} key_len={len(key)}",
        flush=True,
    )

    client = OpenAI(api_key=key)
    OUT.mkdir(parents=True, exist_ok=True)

    smoke = OUT / "_smoke.mp3"
    print("SMOKE ...", flush=True)
    try:
        generate_one(client, ENTRIES[0]["text"], smoke)
        print(f"SMOKE ok bytes={smoke.stat().st_size}", flush=True)
    finally:
        if smoke.exists():
            smoke.unlink()

    results = []
    errors = []
    for i, entry in enumerate(ENTRIES, 1):
        path = OUT / entry["file"]
        print(f"[{i}/{len(ENTRIES)}] {entry['id']} -> {entry['file']}", flush=True)
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

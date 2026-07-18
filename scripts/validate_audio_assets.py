#!/usr/bin/env python3
"""Non-destructive validation: manifest ↔ files ↔ index.html source strings."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
MANIFEST = AUDIO / "manifest.json"
HTML = ROOT / "index.html"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def main() -> None:
    if not MANIFEST.is_file():
        fail(f"missing {MANIFEST}")
    if not HTML.is_file():
        fail(f"missing {HTML}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clips = manifest.get("clips") or {}
    if not clips:
        fail("manifest.clips empty")

    html = HTML.read_text(encoding="utf-8")

    # Extract messages array strings
    m = re.search(r"const messages = \[(.*?)\];", html, re.S)
    if m is None:
        fail("messages array not found in index.html")
    # Source uses plain UTF-8 string literals without escapes.
    messages = re.findall(r'"([^"]+)"', m.group(1))
    if len(messages) != 10:
        fail(f"expected 10 messages, got {len(messages)}: {messages}")

    rewards = {}
    for hapjes, title, text in re.findall(
        r"(\d+):\s*\{\s*emoji:\s*\"[^\"]+\",\s*title:\s*\"([^\"]+)\",\s*text:\s*\"([^\"]+)\"",
        html,
    ):
        rewards[int(hapjes)] = (title, text)
    if set(rewards) != {3, 5, 10, 15, 20}:
        fail(f"unexpected reward keys: {sorted(rewards)}")

    if "Klaar voor de eerste superhap?" not in html:
        fail("start/reset line missing from HTML")

    errors = []
    total_bytes = 0

    for cid, clip in clips.items():
        path = ROOT / clip["path"]
        if not path.is_file():
            errors.append(f"{cid}: missing file {clip['path']}")
            continue
        data = path.read_bytes()
        size = len(data)
        total_bytes += size
        if size != clip.get("bytes"):
            errors.append(f"{cid}: bytes mismatch file={size} manifest={clip.get('bytes')}")
        if size < 500:
            errors.append(f"{cid}: too small ({size})")
        if not (data[:3] == b"ID3" or data[0] == 0xFF):
            errors.append(f"{cid}: bad mp3 header")
        if clip.get("format") != "mp3":
            errors.append(f"{cid}: format not mp3")
        if not clip.get("text"):
            errors.append(f"{cid}: empty text")

    # Cross-check encouragement order
    for i, text in enumerate(messages):
        cid = f"msg_{i+1:02d}"
        if cid not in clips:
            errors.append(f"missing clip id {cid}")
        elif clips[cid]["text"] != text:
            errors.append(f"{cid}: text != messages[{i}] html={text!r} man={clips[cid]['text']!r}")

    # start
    if clips.get("start", {}).get("text") != "Klaar voor de eerste superhap?":
        errors.append("start text mismatch")

    # rewards
    for hapjes, (title, body) in rewards.items():
        cid = f"reward_{hapjes}"
        if cid not in clips:
            errors.append(f"missing {cid}")
            continue
        expected = f"{title} {body}"
        if clips[cid]["text"] != expected:
            errors.append(f"{cid}: spoken text mismatch expected={expected!r}")
        if clips[cid].get("title") != title or clips[cid].get("body") != body:
            errors.append(f"{cid}: title/body fields mismatch")

    # no stray committed temp files expected
    expected_files = {c["file"] for c in clips.values()} | {"manifest.json"}
    on_disk = {p.name for p in AUDIO.iterdir() if p.is_file() and not p.name.startswith("_")}
    extra = on_disk - expected_files
    missing = expected_files - on_disk
    if missing:
        errors.append(f"missing on disk: {sorted(missing)}")
    if extra:
        errors.append(f"unexpected files (non-temp): {sorted(extra)}")

    # architecture flags
    if manifest.get("runtime_tts") is not False:
        errors.append("runtime_tts must be false")
    if manifest.get("browser_api_keys") is not False:
        errors.append("browser_api_keys must be false")

    # index.html must still have no network TTS / API keys
    bad_patterns = [
        r"api\.x\.ai",
        r"api\.openai\.com",
        r"XAI_API_KEY",
        r"OPENAI_API_KEY",
        r"speechSynthesis",
        r"text-to-speech",
        r"/v1/tts",
    ]
    for pat in bad_patterns:
        if re.search(pat, html, re.I):
            errors.append(f"index.html contains forbidden pattern: {pat}")

    print("clips", len(clips))
    print("total_bytes", total_bytes)
    print("messages_ok", len(messages) == 10)
    print("rewards_ok", set(rewards) == {3, 5, 10, 15, 20})
    if errors:
        for e in errors:
            print("FAIL:", e)
        raise SystemExit(1)
    print("PASS: manifest, paths, MP3 headers, and HTML source texts align")


if __name__ == "__main__":
    main()

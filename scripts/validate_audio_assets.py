#!/usr/bin/env python3
"""Non-destructive validation: manifest ↔ files ↔ index.html source strings."""
from __future__ import annotations

import hashlib
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

    m = re.search(r"const messages = \[(.*?)\];", html, re.S)
    if m is None:
        fail("messages array not found in index.html")
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

    # AI-generated speech disclosure (OpenAI TTS policy)
    if "AI-gegenereerd" not in html and "AI-generated" not in html:
        fail("missing visible AI-generated speech disclosure in index.html")

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
        digest = hashlib.sha256(data).hexdigest()
        if clip.get("sha256") and clip["sha256"] != digest:
            errors.append(f"{cid}: sha256 mismatch")
        if clip.get("format") != "mp3":
            errors.append(f"{cid}: format not mp3")
        if not clip.get("text"):
            errors.append(f"{cid}: empty text")

    for i, text in enumerate(messages):
        cid = f"msg_{i+1:02d}"
        if cid not in clips:
            errors.append(f"missing clip id {cid}")
        elif clips[cid]["text"] != text:
            errors.append(
                f"{cid}: text != messages[{i}] html={text!r} man={clips[cid]['text']!r}"
            )

    if clips.get("start", {}).get("text") != "Klaar voor de eerste superhap?":
        errors.append("start text mismatch")

    if messages[2] != "Super goed bezig!":
        errors.append(f"messages[2] must be 'Super goed bezig!', got {messages[2]!r}")

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

    expected_files = {c["file"] for c in clips.values()} | {"manifest.json"}
    on_disk = {p.name for p in AUDIO.iterdir() if p.is_file() and not p.name.startswith("_")}
    extra = on_disk - expected_files
    missing = expected_files - on_disk
    if missing:
        errors.append(f"missing on disk: {sorted(missing)}")
    if extra:
        errors.append(f"unexpected files (non-temp): {sorted(extra)}")

    if manifest.get("runtime_tts") is not False:
        errors.append("runtime_tts must be false")
    if manifest.get("browser_api_keys") is not False:
        errors.append("browser_api_keys must be false")

    gen = manifest.get("generation") or {}
    if gen.get("provider") != "openai":
        errors.append(f"generation.provider must be openai, got {gen.get('provider')!r}")
    if gen.get("model") != "gpt-4o-mini-tts":
        errors.append(f"generation.model unexpected: {gen.get('model')!r}")
    if gen.get("voice") != "marin":
        errors.append(f"generation.voice unexpected: {gen.get('voice')!r}")
    # Stale xAI provenance must not remain as the canonical generation route.
    tooling = str(gen.get("tooling", "")).lower()
    if gen.get("provider") == "xai":
        errors.append("stale xAI generation.provider still present")
    if "generate_xai" in tooling:
        errors.append("stale xAI generate script still referenced in tooling")

    bad_patterns = [
        r"api\.x\.ai",
        r"api\.openai\.com",
        r"XAI_API_KEY",
        r"OPENAI_API_KEY",
        r"speechSynthesis",
        r"text-to-speech",
        r"/v1/tts",
        r"/v1/audio/speech",
    ]
    for pat in bad_patterns:
        if re.search(pat, html, re.I):
            errors.append(f"index.html contains forbidden pattern: {pat}")

    # README / scripts must not claim xAI as the canonical generator of the committed set.
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
    if "generate_xai_dutch_v1" in readme:
        errors.append("README still references generate_xai_dutch_v1 as active route")
    if (ROOT / "scripts" / "generate_xai_dutch_v1.py").is_file():
        errors.append("stale scripts/generate_xai_dutch_v1.py still present")

    print("clips", len(clips))
    print("total_bytes", total_bytes)
    print("provider", gen.get("provider"))
    print("model", gen.get("model"))
    print("voice", gen.get("voice"))
    print("messages_ok", len(messages) == 10)
    print("rewards_ok", set(rewards) == {3, 5, 10, 15, 20})
    if errors:
        for e in errors:
            print("FAIL:", e)
        raise SystemExit(1)
    print("PASS: manifest, paths, MP3 headers, checksums, and HTML source texts align")


if __name__ == "__main__":
    main()

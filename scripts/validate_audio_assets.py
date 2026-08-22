#!/usr/bin/env python3
"""Non-destructive validation: manifest ↔ files ↔ inventory ↔ index.html copy."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
MANIFEST = AUDIO / "manifest.json"
HTML = ROOT / "index.html"
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from speech_inventory import CHILD_FACING_CATEGORIES, ENTRIES  # noqa: E402


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def main() -> None:
    if shutil.which("ffprobe") is None:
        fail("ffprobe not found on PATH; install ffmpeg (bitrate checks need it)")
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

    # End-state lines that must appear in the HTML (positive, pressure-free).
    end_lines = [
        "Avontuur klaar!",
        "Verder eten is niet nodig. Je mag stoppen wanneer je wilt.",
        "Klaar met eten",
        "Bonusavontuur! Verder eten is niet nodig, maar mag wel.",
    ]
    for line in end_lines:
        if line not in html:
            fail(f"end-state line missing from HTML: {line!r}")

    # Issue #8: the AI-voice disclosure lives in the parent/info menu
    # (oudermenu), programmatically readable, no longer permanently on the
    # main child screen.
    if "De gesproken teksten zijn met AI gegenereerd." not in html:
        fail("AI-generated speech disclosure missing from HTML")
    if 'id="oudermenuStem"' not in html:
        fail("AI-generated speech disclosure not anchored in the oudermenu")
    oudermenu_start = html.find('<div class="oudermenu"')
    if oudermenu_start == -1:
        fail("oudermenu dialog markup missing")
    oudermenu_end = html.find("</body>", oudermenu_start)
    if html.find("De gesproken teksten zijn met AI gegenereerd.", oudermenu_start, oudermenu_end) == -1:
        fail("AI-generated speech disclosure must stay inside the oudermenu dialog")

    # No pressure copy may remain anywhere in the HTML.
    pressure_patterns = [
        "Je bord wordt al leger",
        "Nog eentje voor de power",
        "Je vliegt door dit avondeten heen",
        "groot en sterk",
        "Eetkoningin",
        "Eetkampioen",
        "Supereter",
        "Bordbaas",
        "Wat een prestatie",
        "echte kampioen",
    ]
    for pat in pressure_patterns:
        if pat in html:
            errors.append(f"pressure copy still present in HTML: {pat!r}")

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

    # end-state clips must exist and carry the expected pressure-free text
    end_expected = {
        "end": "Avontuur klaar! Verder eten is niet nodig. Je mag stoppen wanneer je wilt.",
        "end_done": "Avontuur klaar! Je mag stoppen wanneer je wilt.",
        "bonus": "Bonusavontuur! Verder eten is niet nodig, maar mag wel.",
    }
    for cid, expected in end_expected.items():
        if cid not in clips:
            errors.append(f"missing end-state clip {cid}")
        elif clips[cid]["text"] != expected:
            errors.append(f"{cid}: end-state text mismatch expected={expected!r}")

    # ── Issue #15: every child-facing clip must exist and match the HTML ──
    for entry in ENTRIES:
        cid = entry["id"]
        if cid not in clips:
            errors.append(f"issue #15: missing child-facing clip {cid}")
            continue
        if clips[cid]["text"] != entry["text"]:
            errors.append(
                f"{cid}: inventory/manifest text mismatch "
                f"inv={entry['text']!r} man={clips[cid]['text']!r}"
            )
        if clips[cid].get("file") != entry["file"]:
            errors.append(f"{cid}: file mismatch inv={entry['file']} man={clips[cid].get('file')}")

    # Manifest must not carry clips outside the inventory (drift guard).
    inventory_ids = {e["id"] for e in ENTRIES}
    for cid in clips:
        if cid not in inventory_ids:
            errors.append(f"manifest clip {cid} not in speech_inventory (drift)")

    # Child-facing categories must be exactly the enforced set.
    listed = manifest.get("child_facing_categories")
    if listed != CHILD_FACING_CATEGORIES:
        errors.append("manifest.child_facing_categories drifted from speech_inventory")

    # The HTML must reference every inventory clip via SPEECH_MAP and play
    # it: SPEECH_MAP keys mirror the inventory, and each new hook family is
    # present in the source.
    speech_map_block = re.search(r"const SPEECH_MAP = \{(.*?)\};", html, re.S)
    if speech_map_block is None:
        fail("SPEECH_MAP not found in index.html")
    map_keys = set(re.findall(r"([A-Za-z0-9_]+):\s*\"[^\"]+\"", speech_map_block.group(1)))
    for entry in ENTRIES:
        if entry["id"] not in map_keys:
            errors.append(f"issue #15: SPEECH_MAP missing key {entry['id']}")
    for key in map_keys:
        if key not in inventory_ids:
            errors.append(f"issue #15: SPEECH_MAP key {key} not in inventory")

    # Playback hooks: each child-facing family must actually call playSpeech.
    hook_checks = [
        ('playSpeech("picker_title_" + step)', "picker step titles"),
        ('playSpeech("meal_" + key)', "meal names"),
        ('playSpeech("extra_" + key)', "extra names"),
        ('playSpeech("chip_eat_" + selectedMealKey)', "chip chosen line"),
        ('playSpeech("chip_kies")', "chip invite line"),
        ('playSpeech("schatkist_intro")', "schatkist open"),
        ('playSpeech("schatkist_actief")', "schatkist active status"),
        ('playSpeech("schatkist_vrij")', "schatkist unlocked status"),
        ('playSpeech("spaar_reset_vraag")', "spaar reset question"),
        ('playSpeech("spaar_reset_nieuw")', "spaar reset confirmation"),
        ('playSpeech("unlock_" + ontgrendeldDoel.id)', "goal unlock line"),
        ('playSpeech("unlock_einde_" + ontgrendeldDoel.id)', "end-boundary unlock line"),
        ('playSpeech("start")', "start/reset line"),
    ]
    for needle, label in hook_checks:
        if needle not in html:
            errors.append(f"issue #15: playSpeech hook missing for {label}")

    # Issue #15: new child-facing spoken/hint copy cannot bypass the inventory.
    # Decorative group headings must be aria-hidden; spoken lines must exist
    # in speech_inventory. Deselect hints must reuse extra names, not invent
    # "niet meer." copy.
    spoken_group_labels = re.findall(
        r'class="picker-group-label"(?![^>]*aria-hidden="true")>([^<]+)<',
        html,
    )
    inventory_texts = {e["text"] for e in ENTRIES}
    for label in spoken_group_labels:
        if label not in inventory_texts:
            errors.append(
                f"issue #15: spoken picker group label {label!r} missing from speech_inventory"
            )
    if "niet meer." in html:
        errors.append("issue #15: deselect hint copy must use an inventory line, not 'niet meer.'")

    # The start clip may only play while its line is visible: the first
    # game start (picker close with the play area visible) and resetGame.
    if "startClipGevraagd" not in html:
        errors.append("issue #15: start clip guard (startClipGevraagd) missing")

    # Child-facing spoken texts must appear verbatim in the HTML (visible
    # line) or be assembled from visible copy fragments. Numeric progress
    # lines are the documented exception (manifest decisions).
    assembled_ok = {
        # chip lines: "Je eet nu: " + meals[key].name
        **{
            e["id"]: ('"Je eet nu: "' in html and e["text"].removeprefix("Je eet nu: ") in html)
            for e in ENTRIES
            if e["id"].startswith("chip_eat_")
        },
        # picker titles: title + note are separate visible elements
        "picker_title_1": ("Wat voor soort eten heb je vandaag?" in html and "Je mag zelf kiezen. Alle keuzes zijn goed." in html),
        "picker_title_2": ("Wat ligt er op je bord?" in html and "Je mag meerdere dingen kiezen. Overslaan mag ook." in html),
        # schatkist intro: title + standing question
        "schatkist_intro": (">Schatkist</h2>" in html and "Waar spaar jij voor? Elke hap geeft één muntje." in html),
        # unlocked status: emoji suffix is decorative
        "schatkist_vrij": '"Van jou! ✓"' in html,
        # unlock announcements: "Gefeliciteerd! " + naam + " is nu van jou!"
        **{
            e["id"]: ('"Gefeliciteerd! "' in html and e["text"].removeprefix("Gefeliciteerd! ").removesuffix(" is nu van jou!") in html)
            for e in ENTRIES
            if e["category"] == "unlock" and not e["id"].startswith("unlock_einde_")
        },
        **{
            e["id"]: ('"Avontuur klaar! "' in html and e["text"].removeprefix("Avontuur klaar! ").removesuffix(" is nu van jou!") in html)
            for e in ENTRIES
            if e["id"].startswith("unlock_einde_")
        },
        # spaar reset message assembled in spaarResetBevestig
        "spaar_reset_nieuw": '"Nieuwe spaarpot! Je ontgrendelde dingen mag je houden."' in html,
    }
    for entry in ENTRIES:
        cid = entry["id"]
        # reward/end_state texts are "{title} {body}" concatenations already
        # cross-checked against the HTML fragments above; skip verbatim here.
        if entry["category"] in ("reward", "end_state"):
            continue
        if cid in assembled_ok:
            if not assembled_ok[cid]:
                errors.append(f"issue #15: {cid} spoken text does not match visible copy")
        elif entry["text"] not in html:
            errors.append(f"issue #15: {cid} spoken text not found in index.html: {entry['text']!r}")

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

    gen = manifest.get("generation") or {}
    if gen.get("provider") != "openai":
        errors.append(f"generation.provider must be openai, got {gen.get('provider')!r}")
    if gen.get("model") != "gpt-4o-mini-tts":
        errors.append(f"generation.model must be gpt-4o-mini-tts, got {gen.get('model')!r}")
    if gen.get("voice") != "marin":
        errors.append(f"generation.voice must be marin, got {gen.get('voice')!r}")
    if gen.get("provider") == "edge-tts" or "Fenna" in str(gen.get("voice_id", "")):
        errors.append("edge-tts / Fenna is not an accepted fallback")

    # Bytes-level profile: OpenAI marin clips in this repo are 128 kbps CBR.
    # 48 kbps is the edge-tts Fenna signature. A lying marin manifest must fail.
    for cid, clip in clips.items():
        path = AUDIO / clip["file"]
        if not path.is_file():
            continue
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=bit_rate",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        try:
            bitrate = int((probe.stdout or "0").strip() or 0)
        except ValueError:
            bitrate = 0
        if gen.get("voice") == "marin" and bitrate and bitrate < 96000:
            errors.append(
                f"{cid}: bitrate {bitrate} looks like Fenna (48k), not marin (128k)"
            )
        declared = clip.get("bit_rate_bps")
        if declared and bitrate and declared != bitrate:
            errors.append(f"{cid}: bit_rate_bps manifest={declared} file={bitrate}")

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
    print("child_facing_clips", sum(1 for e in ENTRIES if e["category"] in CHILD_FACING_CATEGORIES))
    if errors:
        for e in errors:
            print("FAIL:", e)
        raise SystemExit(1)
    print("PASS: manifest, paths, MP3 headers, inventory, SPEECH_MAP hooks, and HTML source texts align")


if __name__ == "__main__":
    main()

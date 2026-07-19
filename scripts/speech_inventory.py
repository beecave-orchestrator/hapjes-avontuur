#!/usr/bin/env python3
"""Frozen stable-ID speech inventory for Hapjes Avontuur static TTS assets.

Single source of truth for generate + build_manifest. Keep IDs aligned with
index.html messages[] / rewards / start-reset copy.
"""
from __future__ import annotations

# Stable inventory. msg_03 uses the user-approved wording "Super goed bezig!".
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
        "title": "Eetkoningin!",
        "body": "20 hapjes! Wat een prestatie.",
        "text": "Eetkoningin! 20 hapjes! Wat een prestatie.",
        "file": "reward_20.mp3",
        "source": "rewards[20] title+text",
    },
]

# Canonical build-time generation settings (not runtime).
PROVIDER = "openai"
MODEL = "gpt-4o-mini-tts"
VOICE = "marin"
RESPONSE_FORMAT = "mp3"
LOCALE = "nl-NL"
INSTRUCTIONS = (
    "Speak warmly, clearly, and encouragingly in Dutch for young children. "
    "Use a calm, moderate pace. Sound friendly and proud, never rushed or harsh."
)

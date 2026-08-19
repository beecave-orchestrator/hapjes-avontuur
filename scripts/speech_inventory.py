#!/usr/bin/env python3
"""Frozen stable-ID speech inventory for Hapjes Avontuur static TTS assets.

Single source of truth for the speech pack. scripts/build_manifest.py,
scripts/regenerate_edge_tts.py, and scripts/generate_openai_dutch_v1.py all
import ENTRIES from here, so the pack can never drift between generators.

Issue #15: every child-facing visible line that is spoken has a frozen clip.
Numeric progress lines (goal card counters, "nog X muntjes", "X van Y") are
deliberately NOT frozen: they change every hap and re-speaking running
numbers each bite would contradict the pressure-free design. The oudermenu
(parent menu) stays silent by standing rule: not child-facing.

IDs are stable. Renaming an ID breaks audio/manifest.json + SPEECH_MAP and
must never happen silently.
"""
from __future__ import annotations

# Post-issue-#7 neutral, pressure-free copy (matches index.html exactly).
ENTRIES = [
    # ── start / reset ──────────────────────────────────────────────────────
    {
        "id": "start",
        "category": "start_reset",
        "text": "Klaar voor de eerste superhap?",
        "file": "start.mp3",
        "source": "initial #message + resetGame()",
    },
    # ── encouragements (messages[] order) ─────────────────────────────────
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
    # ── rewards (one clip: title + body) ───────────────────────────────────
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
    # ── end state ──────────────────────────────────────────────────────────
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
    # ── issue #15: meal picker titles + notes (one clip: title + note) ────
    {
        "id": "picker_title_1",
        "category": "picker",
        "text": "Wat eet je vandaag? Je mag zelf kiezen. Alle keuzes zijn goed.",
        "file": "picker_title_1.mp3",
        "source": "picker step 1 title + note",
    },
    {
        "id": "picker_title_2",
        "category": "picker",
        "text": "Wil je nog wat kiezen? Dit hoeft niet. Je mag deze stap ook overslaan.",
        "file": "picker_title_2.mp3",
        "source": "picker step 2 title + note",
    },
    # ── issue #15: meal + extra names (spoken on selection, match the
    #    picker hint line "X gekozen" visible after selecting) ──────────────
    {
        "id": "meal_aardappels",
        "category": "picker_name",
        "text": "Aardappels en groente",
        "file": "meal_aardappels.mp3",
        "source": "meals.aardappels.name",
    },
    {
        "id": "meal_pasta",
        "category": "picker_name",
        "text": "Pasta",
        "file": "meal_pasta.mp3",
        "source": "meals.pasta.name",
    },
    {
        "id": "meal_rijst",
        "category": "picker_name",
        "text": "Rijst",
        "file": "meal_rijst.mp3",
        "source": "meals.rijst.name",
    },
    {
        "id": "meal_noedels",
        "category": "picker_name",
        "text": "Noedels",
        "file": "meal_noedels.mp3",
        "source": "meals.noedels.name",
    },
    {
        "id": "meal_soep",
        "category": "picker_name",
        "text": "Soep",
        "file": "meal_soep.mp3",
        "source": "meals.soep.name",
    },
    {
        "id": "meal_eigen",
        "category": "picker_name",
        "text": "Mijn eigen eten",
        "file": "meal_eigen.mp3",
        "source": "meals.eigen.name",
    },
    {
        "id": "extra_groente",
        "category": "picker_name",
        "text": "Groente",
        "file": "extra_groente.mp3",
        "source": "extras.groente",
    },
    {
        "id": "extra_vlees",
        "category": "picker_name",
        "text": "Vlees of vis",
        "file": "extra_vlees.mp3",
        "source": "extras.vlees",
    },
    {
        "id": "extra_vegetarisch",
        "category": "picker_name",
        "text": "Vegetarisch",
        "file": "extra_vegetarisch.mp3",
        "source": "extras.vegetarisch",
    },
    {
        "id": "extra_saus",
        "category": "picker_name",
        "text": "Saus",
        "file": "extra_saus.mp3",
        "source": "extras.saus",
    },
    {
        "id": "extra_weetniet",
        "category": "picker_name",
        "text": "Weet ik niet",
        "file": "extra_weetniet.mp3",
        "source": "extras.weetniet",
    },
    # ── issue #15: meal chip lines ─────────────────────────────────────────
    {
        "id": "chip_kies",
        "category": "chip",
        "text": "Kies je eten",
        "file": "chip_kies.mp3",
        "source": "meal chip default #mealChipText",
    },
    {
        "id": "chip_eat_aardappels",
        "category": "chip",
        "text": "Je eet nu: Aardappels en groente",
        "file": "chip_eat_aardappels.mp3",
        "source": "meal chip \"Je eet nu: \" + name",
    },
    {
        "id": "chip_eat_pasta",
        "category": "chip",
        "text": "Je eet nu: Pasta",
        "file": "chip_eat_pasta.mp3",
        "source": "meal chip \"Je eet nu: \" + name",
    },
    {
        "id": "chip_eat_rijst",
        "category": "chip",
        "text": "Je eet nu: Rijst",
        "file": "chip_eat_rijst.mp3",
        "source": "meal chip \"Je eet nu: \" + name",
    },
    {
        "id": "chip_eat_noedels",
        "category": "chip",
        "text": "Je eet nu: Noedels",
        "file": "chip_eat_noedels.mp3",
        "source": "meal chip \"Je eet nu: \" + name",
    },
    {
        "id": "chip_eat_soep",
        "category": "chip",
        "text": "Je eet nu: Soep",
        "file": "chip_eat_soep.mp3",
        "source": "meal chip \"Je eet nu: \" + name",
    },
    {
        "id": "chip_eat_eigen",
        "category": "chip",
        "text": "Je eet nu: Mijn eigen eten",
        "file": "chip_eat_eigen.mp3",
        "source": "meal chip \"Je eet nu: \" + name",
    },
    # ── issue #15: Schatkist dialog copy ───────────────────────────────────
    # Note: the "Hiervoor sparen" button label is an action label, not a
    # progress/unlock/status line, and stays unspoken like every other
    # button in the game (standing pattern: messages/titles/status speak,
    # buttons do not).
    {
        "id": "schatkist_intro",
        "category": "schatkist",
        "text": "Schatkist. Waar spaar jij voor? Elke hap geeft één muntje.",
        "file": "schatkist_intro.mp3",
        "source": "schatkist title + initial #schatkistText",
    },
    {
        "id": "schatkist_actief",
        "category": "schatkist",
        "text": "Hier spaar je voor",
        "file": "schatkist_actief.mp3",
        "source": "renderSchatkist() active-goal status",
    },
    {
        "id": "schatkist_vrij",
        "category": "schatkist",
        "text": "Van jou!",
        "file": "schatkist_vrij.mp3",
        "source": "renderSchatkist() unlocked status \"Van jou! ✓\"",
    },
    {
        "id": "spaar_reset_vraag",
        "category": "schatkist",
        "text": "Opnieuw sparen? Je spaarpot wordt dan leeg. Je ontgrendelde dingen mag je houden.",
        "file": "spaar_reset_vraag.mp3",
        "source": "#spaarResetVraag",
    },
    {
        "id": "spaar_reset_nieuw",
        "category": "schatkist",
        "text": "Nieuwe spaarpot! Je ontgrendelde dingen mag je houden.",
        "file": "spaar_reset_nieuw.mp3",
        "source": "spaarResetBevestig() message",
    },
    # ── issue #15: goal-unlock announcements (message card copy) ──────────
    {
        "id": "unlock_confetti",
        "category": "unlock",
        "text": "Gefeliciteerd! Feestconfetti is nu van jou!",
        "file": "unlock_confetti.mp3",
        "source": "\"Gefeliciteerd! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_bord",
        "category": "unlock",
        "text": "Gefeliciteerd! Feestbord is nu van jou!",
        "file": "unlock_bord.mp3",
        "source": "\"Gefeliciteerd! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_panda",
        "category": "unlock",
        "text": "Gefeliciteerd! Dierenvriendje is nu van jou!",
        "file": "unlock_panda.mp3",
        "source": "\"Gefeliciteerd! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_regenboog",
        "category": "unlock",
        "text": "Gefeliciteerd! Regenbooglucht is nu van jou!",
        "file": "unlock_regenboog.mp3",
        "source": "\"Gefeliciteerd! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_strik",
        "category": "unlock",
        "text": "Gefeliciteerd! Feeststrik is nu van jou!",
        "file": "unlock_strik.mp3",
        "source": "\"Gefeliciteerd! \" + naam + \" is nu van jou!\"",
    },
    # ── issue #15: end-state unlock variant (goal lands on the final hap) ──
    {
        "id": "unlock_einde_confetti",
        "category": "unlock",
        "text": "Avontuur klaar! Feestconfetti is nu van jou!",
        "file": "unlock_einde_confetti.mp3",
        "source": "\"Avontuur klaar! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_einde_bord",
        "category": "unlock",
        "text": "Avontuur klaar! Feestbord is nu van jou!",
        "file": "unlock_einde_bord.mp3",
        "source": "\"Avontuur klaar! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_einde_panda",
        "category": "unlock",
        "text": "Avontuur klaar! Dierenvriendje is nu van jou!",
        "file": "unlock_einde_panda.mp3",
        "source": "\"Avontuur klaar! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_einde_regenboog",
        "category": "unlock",
        "text": "Avontuur klaar! Regenbooglucht is nu van jou!",
        "file": "unlock_einde_regenboog.mp3",
        "source": "\"Avontuur klaar! \" + naam + \" is nu van jou!\"",
    },
    {
        "id": "unlock_einde_strik",
        "category": "unlock",
        "text": "Avontuur klaar! Feeststrik is nu van jou!",
        "file": "unlock_einde_strik.mp3",
        "source": "\"Avontuur klaar! \" + naam + \" is nu van jou!\"",
    },
]


def by_category(category: str) -> list[dict]:
    return [e for e in ENTRIES if e["category"] == category]


# Child-facing categories the validator enforces (issue #15): every clip in
# these categories must exist on disk, or validation fails.
CHILD_FACING_CATEGORIES = [
    "start_reset",
    "encouragement",
    "reward",
    "end_state",
    "picker",
    "picker_name",
    "chip",
    "schatkist",
    "unlock",
]

# OpenAI-route generation settings (issue #15 asks for this route; requires
# OPENAI_API_KEY in the process environment — never embedded in the repo).
PROVIDER = "openai"
MODEL = "gpt-4o-mini-tts"
VOICE = "marin"
RESPONSE_FORMAT = "mp3"
LOCALE = "nl-NL"
INSTRUCTIONS = (
    "Speak warmly, clearly, and encouragingly in Dutch for young children. "
    "Use a calm, moderate pace. Sound friendly and proud, never rushed or harsh."
)

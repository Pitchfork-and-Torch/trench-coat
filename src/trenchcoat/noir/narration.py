"""Noir Mode — gritty detective narration for the cloak."""

from __future__ import annotations

import random

LINES = {
    "boot": [
        "Rain on the glass. The city doesn't care who you are — good. Neither should the wire.",
        "You put on the coat. The coat puts on the network.",
        "Neon signs lie. Packets don't have to.",
    ],
    "engage": [
        "The shadows have you covered… for now.",
        "Chain locked. Faces blur. Names dissolve.",
        "You are a rumor on a wet street.",
    ],
    "rotate": [
        "New alley. Same coat. Keep walking.",
        "The trail goes cold mid-sentence.",
        "Circuits rebuild like broken glass under a streetlamp.",
    ],
    "dead_hop": [
        "A door slammed shut. Find another stairwell.",
        "That hop went dark. The rain keeps falling.",
        "Dead end in the neon. Rerouting through the fog.",
    ],
    "disengage": [
        "Coat off. The cameras remember how to look again.",
        "Back under the streetlights. Mind the puddles — they reflect everything.",
        "Session closed. The dossier stays in the drawer.",
    ],
    "legal": [
        "This coat is for walking free — not for walking dirty. Stay on the right side of the law.",
        "Privacy is a right. Crime is a choice. Don't confuse the two.",
    ],
    "healthy": [
        "All layers dry on the inside. Outside, the city drowns.",
        "Hops singing in tune. Jazz for ghosts.",
    ],
}


def say(event: str) -> str:
    pool = LINES.get(event) or LINES["boot"]
    return random.choice(pool)

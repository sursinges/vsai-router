import re

PATTERNS = {
    "coding": [
        r"code",
        r"python",
        r"javascript",
        r"function",
        r"class",
        r"algorithm",
        r"write.*code"
    ],

    "reasoning": [
        r"explain",
        r"why",
        r"how",
        r"reason"
    ],

    "translation": [
        r"translate",
        r"переведи"
    ]
}


def detect_skill(text: str) -> str:

    text = text.lower()

    for skill, patterns in PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, text):
                return skill

    return "chat"
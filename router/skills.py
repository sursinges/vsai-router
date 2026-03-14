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
        r"how does",
        r"reason"
    ],

    "translation": [
        r"translate",
        r"переведи"
    ],

    "chat": [
        r"hello",
        r"hi",
        r"hey"
    ]
}


def detect_skill(text: str):

    text = text.lower()

    for skill, patterns in PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, text):
                return skill

    return "chat"
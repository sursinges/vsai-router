from router.skills import detect_skill
import g4f
import json
import asyncio
import os
import time
import re



BASE_DIR = os.path.dirname(__file__)

LOG_FILE = os.path.join(BASE_DIR, "logs.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache.json")
MODELS_FILE = "working_models.json"

MODEL_PATTERNS = [

r"claude[^a-z0-9]*opus[^a-z0-9]*4[^a-z0-9]*6",
r"claude[^a-z0-9]*opus[^a-z0-9]*4[^a-z0-9]*5",
r"claude[^a-z0-9]*opus[^a-z0-9]*4",

r"gpt[^a-z0-9]*5[^a-z0-9]*4",
r"gpt[^a-z0-9]*5[^a-z0-9]*3",
r"gpt[^a-z0-9]*5"
]

def load_models():

    if not os.path.exists(MODELS_FILE):
        return []

    with open(MODELS_FILE, "r") as f:
        data = json.load(f)

    models = []

    for m in data:
        models.append(f"{m['provider']}:{m['model']}")

    return models

def is_target_model(model_key):

    try:
        provider, model = model_key.split(":")
    except:
        model = model_key

    name = model.lower()

    for pattern in MODEL_PATTERNS:

        if re.search(pattern, name):
            return True

    return False


def load_cache():

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)

    return {"good": [], "bad": []}


def save_cache(cache):

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def log_result(data):

    logs = []

    if os.path.exists(LOG_FILE):

        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except:
                logs = []

    logs.append(data)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def model_priority(model):

    m = model.lower()

    if "claude" in m:
        return 3

    if "gpt" in m:
        return 2

    return 1


def filter_by_skill(models, skill):

    if skill == "coding":
        return [m for m in models if "code" in m.lower() or "gpt" in m.lower()]

    if skill == "reasoning":
        return [m for m in models if "deepseek" in m.lower() or "claude" in m.lower()]

    return models


def try_model(model_key, messages):

    try:

        provider_name, model = model_key.split(":")

        provider = getattr(g4f.Provider, provider_name)

        r = g4f.ChatCompletion.create(
            model=model,
            provider=provider,
            messages=messages,
            timeout=20
        )

        if not r:
            return None

        r = str(r)

        if len(r) < 20:
            return None

        return r

    except Exception:
        return None


async def ask_provider(model, messages):

    start = time.time()

    r = await asyncio.to_thread(
        try_model,
        model,
        messages
    )

    if not r:
        return None

    latency = time.time() - start

    return {
        "model": model,
        "response": r,
        "latency": latency,
        "length": len(r)
    }


async def ask(messages, mode="auto"):

    text = messages[-1]["content"]

    skill = detect_skill(text)

    models = load_models()

    models = [m for m in models if is_target_model(m)]

    if not models:
        return {"error": "no models"}

    models = filter_by_skill(models, skill)

    tasks = []

    for m in models:

        tasks.append(
            ask_provider(m, messages)
        )

    results = await asyncio.gather(
        *tasks,
        return_exceptions=True
    )

    clean = []

    for r in results:

        if isinstance(r, Exception):
            continue

        if r:
            clean.append(r)

    if not clean:
        return {"error": "all providers failed"}

    for r in clean:

        r["score"] = r["length"] / r["latency"]
        r["priority"] = model_priority(r["model"])

    clean.sort(
        key=lambda x: (x["priority"], x["score"]),
        reverse=True
    )

    best = clean[0]

    log_result(best)

    return {
        "skill": skill,
        "best": best,
        "alternatives": clean[1:3]
    }
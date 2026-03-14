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
MODELS_FILE = os.path.join(BASE_DIR, "working_models.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

BATCH_SIZE = 4
TIMEOUT = 60

MODEL_PATTERNS = [

r"claude[^a-z0-9]*opus[^a-z0-9]*4[^a-z0-9]*6",
r"claude[^a-z0-9]*opus[^a-z0-9]*4[^a-z0-9]*5",
r"claude[^a-z0-9]*opus[^a-z0-9]*4",

r"gpt[^a-z0-9]*5[^a-z0-9]*4",
r"gpt[^a-z0-9]*5[^a-z0-9]*3",
r"gpt[^a-z0-9]*5"
]


def load_history():

    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def load_skill_configs():

    path = os.path.join(BASE_DIR, "skill_configs.json")

    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_models():

    if not os.path.exists(MODELS_FILE):
        return []

    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = []

    for m in data:
        models.append(f"{m['provider']}:{m['model']}")

    return models


def is_target_model(model_key):

    if "search" in model_key.lower():
        return False

    try:
        provider, model = model_key.split(":")
    except:
        model = model_key

    name = model.lower()

    for pattern in MODEL_PATTERNS:

        if re.search(pattern, name):
            return True

    return False


def log_result(data):

    logs = []

    if os.path.exists(LOG_FILE):

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except:
                logs = []

    logs.append(data)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
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
        return [m for m in models if "gpt" in m.lower() or "claude" in m.lower()]

    if skill == "reasoning":
        return [m for m in models if "claude" in m.lower()]

    return models


def is_bad_response(text):

    t = text.lower()

    if len(t) < 30:
        return True

    html_signals = [
        "<html",
        "<!doctype",
        "<body",
        "<head",
        "cdn.prod.website-files",
        "<script",
        "<meta"
    ]

    for s in html_signals:
        if s in t:
            return True

    return False


def try_model(model_key, messages):

    try:

        provider_name, model = model_key.split(":")
        provider = getattr(g4f.Provider, provider_name)

        r = g4f.ChatCompletion.create(
            model=model,
            provider=provider,
            messages=messages,
            timeout=TIMEOUT
        )

        if not r:
            return None

        r = str(r).strip()

        if is_bad_response(r):
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


async def ask(messages, mode="auto", session="default"):

    text = messages[-1]["content"]

    if text.startswith("/raw"):
        mode = "raw"
        text = text.replace("/raw", "", 1).strip()
        messages[-1]["content"] = text

    history = load_history()

    chat = history.get(session, [])

    chat.extend(messages)

    messages = chat[-20:]

    skill = None

    if mode == "auto":
        skill = detect_skill(text)

    skill_configs = load_skill_configs()

    config = skill_configs.get(skill, {}) if skill else {}

    system_prompt = config.get("system")

    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages

    models = load_models()

    models = [m for m in models if is_target_model(m)]

    if not models:
        return {"error": "no models"}

    models = filter_by_skill(models, skill)

    results = []

    for i in range(0, len(models), BATCH_SIZE):

        batch = models[i:i+BATCH_SIZE]

        tasks = [
            ask_provider(m, messages)
            for m in batch
        ]

        r = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        for item in r:

            if isinstance(item, Exception):
                continue

            if item:
                results.append(item)

    if not results:
        return {"error": "all providers failed"}

    for r in results:

        latency = max(r["latency"], 0.1)

        r["priority"] = model_priority(r["model"])

        r["score"] = (r["length"] / latency) * r["priority"]

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best = results[0]

    chat.append({
        "role": "assistant",
        "content": best["response"]
    })

    history[session] = chat

    save_history(history)

    log_result(best)

    return {
        "skill": skill,
        "best": best,
        "alternatives": results[1:3]
    }
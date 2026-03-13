import g4f
import json
import re
import os
import asyncio
import time

LOG_FILE = "router/logs.json"
CACHE_FILE = "router/cache.json"
MODELS_FILE = "working_models.json"


def log_result(data):

    if not os.path.exists(LOG_FILE):
        logs = []

    else:
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(data)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


MODEL_PATTERNS = [

r"claude[^a-z0-9]*opus[^a-z0-9]*4[^a-z0-9]*6",
r"claude[^a-z0-9]*opus[^a-z0-9]*4[^a-z0-9]*5",
r"claude[^a-z0-9]*opus[^a-z0-9]*4",

r"gpt[^a-z0-9]*5[^a-z0-9]*4",
r"gpt[^a-z0-9]*5[^a-z0-9]*3",
r"gpt[^a-z0-9]*5"

]


def normalize_model(name):

    n = name.lower()

    if re.search(r"claude.*opus.*4.*6", n):
        return "claude-opus-4.6"

    if re.search(r"claude.*opus.*4", n):
        return "claude-opus-4"

    if re.search(r"gpt.*5.*4", n):
        return "gpt-5.4"

    if re.search(r"gpt.*5", n):
        return "gpt-5"

    return name


def load_cache():

    if os.path.exists(CACHE_FILE):

        with open(CACHE_FILE,"r") as f:
            return json.load(f)

    return {"good":[],"bad":[]}


def save_cache(cache):

    with open(CACHE_FILE,"w") as f:
        json.dump(cache,f,indent=2)


def load_models():

    if not os.path.exists(MODELS_FILE):
        return []

    with open(MODELS_FILE,"r") as f:
        data = json.load(f)

    normalized = []

    for m in data:

        provider = m["provider"]
        model = normalize_model(m["model"])

        key = f"{provider}:{model}"

        if key not in normalized:
            normalized.append(key)

    return normalized


def try_model(model_key, prompt):

    try:

        provider_name, model = model_key.split(":")

        blocked = [
            "CachedSearch",
            "Browser",
            "Search",
            "You",
            "Bing",
            "DuckDuckGo"
        ]

        for b in blocked:
            if b.lower() in provider_name.lower():
                print("SKIP SEARCH PROVIDER:", model_key)
                return None

        provider = getattr(g4f.Provider, provider_name)

        r = g4f.ChatCompletion.create(
            model=model,
            provider=provider,
            messages=[{"role": "user", "content": prompt}],
            timeout=20
        )

        if not r:
            return None

        r = str(r)

        if "<html" in r.lower() or "<!doctype" in r.lower():
            print("HTML RESPONSE:", model_key)
            return None

        blocked_phrases = [
            "important notice",
            "deprecated",
            "enable it in your dashboard",
            "requires 2 requests",
            "discord.gg",
            "model not found",
            "object has no attribute",
        ]

        for phrase in blocked_phrases:
            if phrase in r.lower():
                print("SERVICE MESSAGE:", model_key)
                return None

        if len(r) < 20:
            return None

        return r

    except Exception as e:
        print("MODEL ERROR:", model_key, e)

    return None


async def ask_provider(model, prompt):

    start = time.time()

    r = await asyncio.to_thread(try_model, model, prompt)

    if not r:
        return None

    latency = time.time() - start

    return {
        "model": model,
        "response": r,
        "latency": latency,
        "length": len(r)
    }


async def ask(prompt):

    cache = load_cache()
    models = load_models()

    if not models:
        return {"error": "no models"}

    tasks = []

    for m in models:

        if m not in cache["bad"]:
            tasks.append(ask_provider(m, prompt))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    clean = []

    for r in results:
        if isinstance(r, Exception):
            continue
        if r:
            clean.append(r)

    results = clean

    if not results:
        return {"error": "all providers failed"}

    for r in results:
        r["score"] = r["length"] / r["latency"]

    results.sort(key=lambda x: x["score"], reverse=True)

    best = results[0]
    alternatives = results[1:4]

    cache["good"].append(best["model"])
    save_cache(cache)

    log_result(best)

    if not best["response"] and alternatives:
        best = alternatives[0]

    return {
        "best": best,
        "alternatives": alternatives
    }
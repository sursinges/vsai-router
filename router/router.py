import json
import random
import asyncio
from pathlib import Path

import g4f


WORKING_MODELS_FILE = Path("working_models.json")

REQUEST_TIMEOUT = 15


def load_models():
    if not WORKING_MODELS_FILE.exists():
        return []

    with open(WORKING_MODELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def model_variants(name: str):
    return list({
        name,
        name.replace("-", "_"),
        name.replace("-", "."),
        name.replace("_", "-"),
        name.replace("_", "."),
        name.replace(".", "-"),
        name.replace(".", "_"),
    })


def is_valid_response(text: str):

    if not text:
        return False

    text = text.strip()

    if len(text) < 20:
        return False

    lower = text.lower()

    if "<html" in lower:
        return False

    if "<!doctype" in lower:
        return False

    if "error" in lower:
        return False

    return True


async def ask_provider(provider_name, model_name, messages):

    try:

        provider = getattr(g4f.Provider, provider_name)

        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=model_name,
                provider=provider,
                messages=messages
            ),
            timeout=REQUEST_TIMEOUT
        )

        if not is_valid_response(response):
            print(f"INVALID RESPONSE: {provider_name}:{model_name}")
            return None

        print(f"SUCCESS: {provider_name}:{model_name}")

        return {
            "model": f"{provider_name}:{model_name}",
            "response": response
        }

    except asyncio.TimeoutError:

        print(f"TIMEOUT: {provider_name}:{model_name}")
        return None

    except Exception as e:

        print(f"MODEL ERROR: {provider_name}:{model_name} {e}")
        return None


async def route_request(messages):

    models = load_models()

    if not models:
        return {
            "model": None,
            "response": "working_models.json empty"
        }

    random.shuffle(models)

    for entry in models:

        provider = entry["provider"]
        model = entry["model"]

        variants = model_variants(model)

        for variant in variants:

            result = await ask_provider(provider, variant, messages)

            if result:
                return result

    return {
        "model": None,
        "response": "no provider returned valid response"
    }

import g4f
import json
import re

PATTERNS = {
    "claude": re.compile(r"claude[^a-zA-Z0-9]*opus[^a-zA-Z0-9]*4[^a-zA-Z0-9]*6", re.I),
    "gpt": re.compile(r"gpt[^a-zA-Z0-9]*5[^a-zA-Z0-9]*4", re.I),
}

TEST_MODELS = [
    "claude-opus-4.6",
    "claude_opus_4_6",
    "claude.opus.4.6",
    "gpt-5.4",
    "gpt_5_4",
    "gpt.5.4"
  ]

providers = [
    p for p in dir(g4f.Provider)
    if not p.startswith("_")
]

working = []

print("providers:", len(providers))

for provider_name in providers:

    provider = getattr(g4f.Provider, provider_name)

    # пропускаем search providers
    if "Search" in provider_name:
        continue

    for model in TEST_MODELS:

        try:

            r = g4f.ChatCompletion.create(
                model=model,
                provider=provider,
                messages=[{"role": "user", "content": "hello"}],
                timeout=12
            )

            if r and len(str(r)) > 5:

                print("FOUND:", provider_name, model)

                working.append({
                    "provider": provider_name,
                    "model": model
                })

        except:
            pass

with open("working_models.json", "w") as f:
    json.dump(working, f, indent=2)

print("saved:", len(working))
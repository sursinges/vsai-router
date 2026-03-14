import g4f
import json
import time

TEST_PROMPT = "Say OK"

working = []

for provider_name in dir(g4f.Provider):

    if provider_name.startswith("_"):
        continue

    provider = getattr(g4f.Provider, provider_name)

    try:
        start = time.time()

        r = g4f.ChatCompletion.create(
            model="gpt-4",
            provider=provider,
            messages=[{"role":"user","content":TEST_PROMPT}],
            timeout=15
        )

        if r and len(str(r)) > 2:

            latency = time.time() - start

            working.append({
                "provider": provider_name,
                "model": "gpt-5.4",
                "latency": latency
            })

            print("WORKING:", provider_name)

    except:
        pass

with open("working_models.json","w") as f:
    json.dump(working,f,indent=2)
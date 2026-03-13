import g4f
import json
import re

# паттерны нужных моделей
PATTERNS = {

"claude_opus_4_6": re.compile(
r"claude[^a-zA-Z0-9]*opus[^a-zA-Z0-9]*4[^a-zA-Z0-9]*6",
re.IGNORECASE
),

"gpt_5_4": re.compile(
r"gpt[^a-zA-Z0-9]*5[^a-zA-Z0-9]*4",
re.IGNORECASE
)

}

providers = [p for p in dir(g4f.Provider) if not p.startswith("_")]

print("providers:", len(providers))

working = []

TEST_MODELS = [

"claude-opus-4.6",
"claude_opus_4_6",
"claude.opus.4.6",
"gpt-5.4",
"gpt_5_4",
"gpt.5.4"

]

for provider_name in providers:

    provider = getattr(g4f.Provider, provider_name)

    for test_model in TEST_MODELS:

        try:

            r = g4f.ChatCompletion.create(
                model=test_model,
                provider=provider,
                messages=[{"role":"user","content":"hello"}],
                timeout=12
            )

            if r:

                model_name = test_model

                for key, pattern in PATTERNS.items():

                    if pattern.search(model_name):

                        print("FOUND:", provider_name, model_name)

                        working.append({
                            "provider": provider_name,
                            "model": model_name
                        })

        except:
            pass


with open("working_models.json","w") as f:

    json.dump(working,f,indent=2)

print("saved:", len(working))
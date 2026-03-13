import g4f

for model in g4f.Model.__dict__:
    if not model.startswith("_"):
        print(model)
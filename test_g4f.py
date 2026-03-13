import g4f

response = g4f.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "hello"}]
)

print(response)
from g4f.client import Client

# подключаемся к локальному API gpt4free
client = Client(api_base="http://127.0.0.1:8080/v1")

# отправляем запрос модели
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Напиши простую функцию Python которая складывает два числа"}
    ]
)

# выводим ответ
print(response.choices[0].message.content)
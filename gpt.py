from transformers import AutoTokenizer
import requests
import logging
from config import endpoint


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def generate_story(task):
    system_content = ("Ты - дружелюбный бот-рассказчик, Твоя задача писать маленькие рассказы, исходя из промтов "
                      "пользователей на русском языке")
    assistant_content = "Проложи предыдущий рассказ... "
    max_tokens = 2048

    def count_token(text):
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
        return len(tokenizer.encode(text))

    def get_answer_from_gpt(user_promt, previous_answer=""):
        answer = previous_answer
        while True:
            if count_token(user_promt) > max_tokens:
                return None, "Текст задачи слишком длинный!"

            if user_promt == 'Завершить':
                return "Хорошо, доброго вам дня!"

            if user_promt != "Продолжить":
                answer = ""

            resp = requests.post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json={
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_promt},
                        {"role": "assistant", "content": assistant_content + answer},
                    ],
                    "temperature": 1,
                    "max_tokens": max_tokens
                }
            )

            if resp.status_code == 200 and 'choices' in resp.json():
                result = resp.json()['choices'][0]['message']['content']
                if result == "":
                    return answer
                else:
                    answer += " " + result
                    return result
            else:
                return None, f"Не удалось получить ответ от нейросети. Текст ошибки: {resp.text}"

    return get_answer_from_gpt(task)

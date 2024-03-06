import json
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def load_user_data():
    try:
        with open("user_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print(f"Error loading user data: {e}")
        data = {}
    return data


def save_user_data(data):
    try:
        with open("user_data.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving user data: {e}")


user_data = load_user_data()


def record_user_data(data):
    user_id = str(data.from_user.id)
    dictionary_with_initial_data = {"first_name": data.from_user.first_name,
                                    "system_content": "Ты - дружелюбный бот-рассказчик, Ты должен писать "
                                                      "небольшой рассказ, исходя из промта "
                                                      "пользователя на русском языке",
                                    "user_request": "", "assistant_content": "Вот ваш рассказ: "}
    if user_id not in user_data:
        user_data[user_id] = dictionary_with_initial_data
    else:
        del user_data[user_id]
        user_data[user_id] = dictionary_with_initial_data
    save_user_data(user_data)


def saving_data(message, key_name="", data=""):
    global user_data
    user_id = str(message.from_user.id)
    user_info = user_data.get(user_id, {})
    user_info[key_name] = data
    save_user_data(user_data)

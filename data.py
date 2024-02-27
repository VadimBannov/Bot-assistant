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
    dictionary_with_initial_data = {"username": data.from_user.username, "first_name": data.from_user.first_name,
                                    "last_name": data.from_user.last_name, "progress": "user_first_response"}
    if user_id not in user_data:
        user_data[user_id] = dictionary_with_initial_data
    else:
        del user_data[user_id]
        user_data[user_id] = dictionary_with_initial_data
    save_user_data(user_data)

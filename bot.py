import telebot
from telebot.types import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup,
                           InlineKeyboardButton)
import logging
import config
import time
from gpt import generate_story
from data import save_user_data, record_user_data, load_user_data

token = config.BOT_TOKEN
bot = telebot.TeleBot(token)


image_addresses = config.image_addresses


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt", filemode="w",
)


@bot.message_handler(commands=['debug'])
def send_logs(message):
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


def create_replymarkup(button_labels):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for label in button_labels:
        markup.add(KeyboardButton(label))
    return markup


def create_inlinemarkup(button_labels):
    markup = InlineKeyboardMarkup()
    for label in button_labels:
        markup.add(InlineKeyboardButton(label, callback_data=label))
    return markup


@bot.message_handler(commands=['end_dialog'])
@bot.callback_query_handler(func=lambda call: call.data == 'Завершить')
def end_dialog(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_info = user_data.get(user_id, {})
    record_user_data(message)
    if isinstance(message, telebot.types.CallbackQuery):
        message = message.message
        pass
    if user_id not in user_data or user_info["progress"] == "user_first_response":
        bot.send_message(message.chat.id, "Сначала введите свой промт")
        bot.register_next_step_handler(message, get_promt)
        return
    answer = generate_story("Завершить")
    if isinstance(answer, str):
        bot.send_message(message.chat.id, answer)

    else:
        bot.send_message(message.chat.id, f"Произошла ошибка: {answer}")
    return


@bot.message_handler(commands=['continue'])
@bot.callback_query_handler(func=lambda call: call.data == 'Продолжить')
def continue_commands(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_info = user_data.get(user_id, {})
    record_user_data(message)
    if user_id not in user_data or user_info["progress"] == "user_first_response":
        bot.send_message(message.chat.id, "Сначала введите свой промт")
        bot.register_next_step_handler(message, get_promt)
        return
    if isinstance(message, telebot.types.CallbackQuery):
        message = message.message
        pass
    bot.send_message(message.chat.id, "Рассказ генерируется. Пожалуйста, подождите некоторое время", )
    answer = generate_story("Продолжить")
    if isinstance(answer, str):
        bot.send_message(message.chat.id, "Вот ваш рассказ")
        time.sleep(1)
        bot.send_message(message.chat.id, answer, reply_markup=create_inlinemarkup(["Продолжить", "Завершить",
                                                                                    "Перезапустить бота"]))
    else:
        bot.send_message(message.chat.id, f"Произошла ошибка: {answer}")
    bot.register_next_step_handler(message, get_promt)


@bot.message_handler(commands=["reset"])
@bot.callback_query_handler(func=lambda call: call.data == 'Перезапустить бота')
def reset_command(message):
    record_user_data(message)
    if isinstance(message, telebot.types.CallbackQuery):
        message = message.message
        pass
    bot.send_message(message.chat.id, "перезагрузка бота . . .", reply_markup=ReplyKeyboardRemove())
    time.sleep(3)
    start_command(message)


@bot.message_handler(commands=["solve_task"])
def solve_task_command(message):
    bot.send_message(message.chat.id, "Напишите свой промт:")
    bot.register_next_step_handler(message, get_promt)


@bot.message_handler(commands=["start"])
def start_command(message):
    user_name = message.from_user.first_name
    messages_for_user = (f"Добро пожаловать {user_name}! Вас приветствует бот Сказочник. Для генерации рассказов "
                         f"выберите один из двух вариантов. Рекомендуем начать с инструкции, если вы впервые "
                         f"пользуетесь ботом.")
    bot.send_photo(message.chat.id, image_addresses["Картинки"]["1"], messages_for_user,
                   reply_markup=create_replymarkup(["📚Начать с инструкции", "Пропустить инструкцию и начать",
                                                    "🤖Описание бота"]))


@bot.message_handler(commands=["help"])
def help_command(message):
    message_text = message.text
    if message_text == "/help":
        bot.send_message(message.chat.id, "Клавиатурные кнопки были убраны", reply_markup=ReplyKeyboardRemove())
    bot.send_message(message.chat.id, "Инструкция по использованию бота:\n\n"
                                      "Во-первых, важно знать, что есть два способа использования бота. "
                                      "Первый - это использование команд, функциональный способ, но неудобный для "
                                      "обычных пользователей, так как таковой интерфейса нет. "
                                      "Вы можете найти список команд слева от поля ввода текста, в меню. И второй "
                                      "способ - использование всплывающих клавиатурных кнопок. К некоторым сообщениям "
                                      "будут прикреплены клавиатурные кнопки с ответами, нужно лишь нажимать на них. "
                                      "Этот метод удобен и понятен, но менее функционален. Выберите понравившуюся один "
                                      "из методов на свой вкус.\n\n Когда вы вводите команду /solve_task или нажимаете "
                                      "кнопку «Прочитал инструкцию и готов начать» - бот попросит вас прислать ему "
                                      "промт, то есть, текст из которого вы хотите сделать рассказ. После того как "
                                      "вы отправите свой промт, вам нужно будет подождать некоторое время, обычно это "
                                      "занимает около 1 минуты. Через некоторое время бот пришлет вам ваш " 
                                      "рассказ;\n— Команда /continue или кнопка «Продолжить» - нужна в тех случаях, "
                                      "когда бот не дописал рассказ. Если вы хотите, чтобы бот завершил рассказ до "
                                      "конца, то вводите эту команду или нажмите кнопку.\n— Команда /end_dialog или "
                                      "кнопка «Завершить» - завершает диалог с ботом, и он забывает ваши предыдущие "
                                      "сообщения.\n— Команда /reset или кнопка «Перезапустить бота» - перезапускает "
                                      "бота и возвращает вас к началу.")


@bot.message_handler(commands=["about"])
def about_command(message):
    message_text = message.text
    if message_text == "/about":
        bot.send_message(message.chat.id, "Клавиатурные кнопки были убраны", reply_markup=ReplyKeyboardRemove())
    bot.send_message(message.chat.id, "Описание бота:\n\n— Этот бот-помощник, разработанный для помощи в создании "
                                      "небольших рассказы. Благодаря своим возможностям, бот может написать историю "
                                      "основываясь на ваших пожеланиях и идеях. Он может предложить свои варианты "
                                      "развития сюжета, персонажей и идей.")


@bot.message_handler(content_types=["text"])
def user_first_response(message):
    message_text = message.text
    if message_text == "📚Начать с инструкции":
        help_command(message)
        bot.send_message(message.chat.id, "Почитайте инструкцию и затем нажмите кнопку",
                         reply_markup=create_replymarkup(["Порчитал_а инструкцию и готов_а начать"]))
    elif message_text == "🤖Описание бота":
        about_command(message)
        bot.send_message(message.chat.id, "Почитайте описание бота и затем нажмите кнопку",
                         reply_markup=create_replymarkup(["Прочитал_а описание и готов_а начать"]))
    elif message_text == "Пропустить инструкцию и начать":
        bot.send_message(message.chat.id, "Супер!")
        time.sleep(1)
        bot.send_message(message.chat.id, "Напишите свой промт:")
    else:
        bot.send_message(message.chat.id, "Я не понял вашего действия, выберите клавиатурную кнопку!")
        return
    record_user_data(message)
    bot.register_next_step_handler(message, get_promt)


def get_promt(message):
    message_text = message.text
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    user_info = user_data.get(user_id, {})
    if message_text in ["Порчитал_а инструкцию и готов_а начать", "Прочитал_а описание и готов_а начать"]:
        bot.send_message(message.chat.id, "Напишите свой промт:")
        bot.register_next_step_handler(message, get_promt)
        return
    if message.content_type != "text":
        bot.send_message(message.chat.id, "Отправь промт текстовым сообщением")
        bot.register_next_step_handler(message, get_promt)
        return
    user_info["progress"] = "get_promt"
    save_user_data(user_data)
    user_promt = message_text
    bot.send_message(message.chat.id, "Рассказ генерируется. Пожалуйста, подождите некоторое время", )
    answer = generate_story(user_promt)
    if isinstance(answer, str):
        bot.send_message(message.chat.id, "Вот ваш рассказ")
        time.sleep(1)
        bot.send_message(message.chat.id, answer, reply_markup=create_inlinemarkup(["Продолжить", "Завершить",
                                                                                    "Перезапустить бота"]))
    else:
        bot.send_message(message.chat.id, f"Произошла ошибка: {answer}")
    if user_info["progress"] != "get_promt":
        bot.register_next_step_handler(message, get_promt)
        return


bot.polling(timeout=60)

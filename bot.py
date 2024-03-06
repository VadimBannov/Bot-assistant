import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import time
from data import *
from config import BOT_TOKEN, MAX_TOKENS, image_addresses
from gpt import GPT
import logging

bot = telebot.TeleBot(BOT_TOKEN)
gpt = GPT()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt", filemode="w",
)


@bot.message_handler(commands=['debug'])
def send_logs(message):
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


def create_markup(button_labels):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for label in button_labels:
        markup.add(KeyboardButton(label))
    return markup


@bot.message_handler(commands=["start"])
def start_command(message):
    user_name = message.from_user.first_name
    messages_for_user = (f"Добро пожаловать {user_name}! Вас приветствует бот Сказочник. Для генерации рассказов "
                         f"выберите один из двух вариантов. Рекомендуем начать с инструкции, если вы впервые "
                         f"пользуетесь ботом.")
    bot.send_photo(message.chat.id, image_addresses[0], messages_for_user,
                   reply_markup=create_markup(["Написать промт", "📚Инструкция",
                                               "🤖Описание бота"]))
    record_user_data(message)


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
                                      "из методов на свой вкус.\n\n Когда вы вводите команду /solve_task - бот "
                                      "попросит вас прислать ему "
                                      "промт, то есть, текст из которого вы хотите сделать рассказ. После того как "
                                      "вы отправите свой промт, вам нужно будет подождать некоторое время, обычно это "
                                      "занимает около 1 минуты. Через некоторое время бот пришлет вам ваш " 
                                      "рассказ;\n— Команда /continue или кнопка «Продолжить» - нужна в тех случаях, "
                                      "когда бот не дописал рассказ. Если вы хотите, чтобы бот завершил рассказ до "
                                      "конца, то вводите эту команду или нажмите кнопку.\n— Команда /end_dialog или "
                                      "кнопка «Завершить рассказ» - завершает диалог с ботом, и он забывает "
                                      "ваши предыдущие сообщения.\n— Команда /reset или кнопка "
                                      "«Перезапустить бота» - перезапускает бота и возвращает вас к началу.")


@bot.message_handler(commands=["about"])
def about_command(message):
    message_text = message.text
    if message_text == "/about":
        bot.send_message(message.chat.id, "Клавиатурные кнопки были убраны", reply_markup=ReplyKeyboardRemove())
    bot.send_message(message.chat.id, "Описание бота:\n\nЭтот бот-помощник, разработанный для помощи в создании "
                                      "небольших рассказы. Благодаря своим возможностям, бот может написать историю "
                                      "основываясь на ваших пожеланиях и идеях. Он может предложить свои варианты "
                                      "развития сюжета, персонажей и идей.")


@bot.message_handler(commands=["solve_task"])
def solve_task_command(message):
    bot.send_message(message.chat.id, "Напишите свой промт:")
    bot.register_next_step_handler(message, get_promt)


@bot.message_handler(commands=['end_dialog'])
@bot.message_handler(func=lambda message: "Завершить рассказ" in message.text)
def end_task_commands(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id] == {}:
        bot.send_message(user_id, "Чтобы продолжить рассказ, сначала нужно отправить свой промт: ",
                         reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_promt)
        return
    bot.send_message(user_id, "Текущий рассказ завершено, напиши новый рассказ: ", reply_markup=ReplyKeyboardRemove())
    record_user_data(message)
    bot.register_next_step_handler(message, get_promt)
    return


@bot.message_handler(commands=['continue'])
@bot.message_handler(func=lambda message: "Продолжить" in message.text)
def continue_commands(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id] == {}:
        bot.send_message(message.chat.id, "Чтобы продолжить рассказ, сначала нужно отправить свой промт: ",
                         reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Чтобы продолжить рассказ, нужно написать дополнительный промт, который "
                                          "будет продолжать рассказ: ", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_promt)
    return


@bot.message_handler(commands=['reset'])
@bot.message_handler(func=lambda message: "Перезапустить бота" in message.text)
def reset_command(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id] == {}:
        bot.send_message(message.chat.id, "Вы и так находится в начале")
        return
    record_user_data(message)
    bot.send_message(message.chat.id, "перезагрузка бота . . .", reply_markup=ReplyKeyboardRemove())
    time.sleep(3)
    start_command(message)
    return


@bot.message_handler(content_types=["text"])
def user_first_response(message):
    message_text = message.text
    if message_text == "Написать промт":
        bot.send_message(message.chat.id, "Супер!")
        time.sleep(1)
    elif message_text in ["📚Инструкция", "🤖Описание бота"]:
        if message_text == "📚Инструкция":
            help_command(message)
            time.sleep(1)
        else:
            about_command(message)
            time.sleep(1)
        bot.send_message(message.chat.id, "Почитайте описание бота и затем")
        time.sleep(3)
    else:
        bot.send_message(message.chat.id, "Я не понял вашего действия, выберите клавиатурную кнопку!")
        return
    bot.send_message(message.chat.id, "Напишите свой промт:")
    bot.register_next_step_handler(message, get_promt)


@bot.message_handler()
def get_promt(message):
    message_text = message.text
    user_id = str(message.from_user.id)
    if message.content_type != "text":
        bot.send_message(message.chat.id, "Отправь промт текстовым сообщением")
        bot.register_next_step_handler(message, get_promt)
        return

    user_promt = message_text
    saving_data(message, "user_request", user_promt)

    if gpt.count_tokens(user_promt) > MAX_TOKENS:
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, get_promt)
        return
    if (user_id not in user_data or user_data[user_id] == {}) and user_promt == "/continue":
        bot.send_message(user_id, "Чтобы продолжить рассказ, сначала нужно отправить текст: ")
        bot.register_next_step_handler(message, get_promt)
        return
    if user_id not in user_data or user_data[user_id] == {}:
        record_user_data(message)
        saving_data(message, "user_request", user_promt)

    bot.send_message(message.chat.id, "Рассказ генерируется. Пожалуйста, подождите некоторое время",
                     reply_markup=ReplyKeyboardRemove())
    promt = gpt.make_promt(user_data[user_id])
    resp = gpt.send_request(promt)
    answer = gpt.process_resp(resp)
    user_data[user_id]['assistant_content'] += answer

    bot.send_message(message.chat.id, user_data[user_id]['assistant_content'],
                     reply_markup=create_markup(["Продолжить", "Завершить рассказ", "Перезапустить бота"]))


bot.polling()

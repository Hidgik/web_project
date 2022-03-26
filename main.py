import telebot
from telebot import types
import urllib.request
import re
from googlesearch import search
from data.regulars import abort_if_not_found, is_author
from data.regulars import RegularResource, RegularsResource
from data.users import Users
from threading import Thread


bot = telebot.TeleBot('5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA')
@bot.message_handler(commands=["start"])
def start(message, res=False):
    bot.send_message(message.chat.id, 'Команды\n\n/begin\n/list\n/add\n/delete', reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(commands=["begin"])
def handle_text(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["IP адрес", "email", "Телефоны"]
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, 'Выбери, что искать',  reply_markup=keyboard)
    bot.register_next_step_handler(message, choice_search)


def choice_search(message):
    regular = RegularResource()
    bot.send_message(message.chat.id, 'Напиши запрос, по которому я буду искать', reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_results, regular.get_one_regular(message.text.strip()))


def get_results(message, regular):
    query = message.text.strip()
    user = Users(id=message.chat.id, query=query, regular=regular)
    user.save(force_insert=True)


@bot.message_handler(commands=["add"])
def add_name(message):
    bot.send_message(message.chat.id, 'Введите уникальное название для вашего выражения',  reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, add_regular)


def add_regular(message):
    if not is_author(message.text.strip(), message.chat.id, True):
        bot.send_message(message.chat.id, f'Имя уже занято, выберите другое',  reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, 'Введите регулярное выражение',  reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, add_regular_to_db, message.text.strip())


def add_regular_to_db(message, name):
    regular = RegularResource()
    regular.add_regular(name, message.text.strip(), message.chat.id)
    bot.send_message(message.chat.id, 'Успешно',  reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(commands=["list"])
def all_regular(message):
    regular = RegularsResource()
    regulars = regular.get_all_regulars()
    m = '\n\n'.join(regulars)
    bot.send_message(message.chat.id, f'{m}',  reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(commands=["delete"])
def del_regular(message):
    bot.send_message(message.chat.id, 'Введите название выражения',  reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, del_regular_from_db)


def del_regular_from_db(message):
    if not is_author(message.text.strip(), message.chat.id, False):
        bot.send_message(message.chat.id, f'Вы не можете удалить, так как не являетесь автором данного названия или данного названия не существует',  reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        regular = RegularResource()
        regular.del_regular(message.text.strip())
        bot.send_message(message.chat.id, 'Успешно',  reply_markup=telebot.types.ReplyKeyboardRemove())


def main_threading():
    while True:
        for user in Users.select():
            th = Thread(target=threading, args=(user.id, user.query, user.regular))
            th.start()
            us = Users.get(Users.id == user.id)
            us.delete_instance()


def threading(idd, query, regular):
    links = []
    for j in search(query, tld="co.in", num=10, stop=10, pause=2): 
        try:
            links.append(j)
        except Exception:
            pass
    for i in links:
        try:
            uf = urllib.request.urlopen(i)
            html = uf.read()
            items = [
                m.group()
                for m in re.finditer(regular, html.decode('utf-8'))
            ]
            if items:
                bot.send_message(idd, i, reply_markup=telebot.types.ReplyKeyboardRemove())
                bot.send_message(idd, ", ".join(list(set(items))), reply_markup=telebot.types.ReplyKeyboardRemove())
        except Exception:
            pass
    bot.send_message(idd, "Готово", reply_markup=telebot.types.ReplyKeyboardRemove())


th = Thread(target=main_threading, args=())
th.start()

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.polling(none_stop=True, interval=0)
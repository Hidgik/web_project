from tkinter.tix import Tree
import traceback
from black import cancel
from bs4 import BeautifulSoup
import requests
import telebot
from data.regulars import Expressions
from threading import Thread
from flow import Flow


class Stage:
    def __init__(self, bot):
        self.bot = bot
        self.variables = {}
        self.commonCS = {}
        self.notfirst = False
        self.oldname = ''
    
    def cancel_or_not(self, message):
        if message.text.strip() == 'Отмена команды':
            self.CS = [1]
            self.bot.send_message(
                message.chat.id, 'Отменено',
                reply_markup=telebot.types.ReplyKeyboardRemove())
            return False
        return True

    def ValidateName_for_delete(self, message):
        if self.cancel_or_not(message):
            regular = Expressions()
            if regular.get_one_regular(
                    self.variables['Name'],
                    message.from_user.id, startid=False):
                return None
            self.CS = self.commonCS['askName'] + self.CS
            return "Данного имени нет в бд, введите другое"

    def ValidateName_for_begin(self, message):
        if self.cancel_or_not(message):
            regular = Expressions()
            if regular.get_one_regular(
                    self.variables['Name'],
                    message.from_user.id):
                return None
            self.CS = self.commonCS['askName'] + self.CS
            keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["IP адрес", "email", "Телефоны"]
            keyboard.add(*buttons)
            return ["Данного имени нет в бд, введите другое", keyboard]

    def ValidateName_for_add(self, message):
        if self.cancel_or_not(message):
            regular = Expressions()
            if self.oldname:
                if self.variables['Name'] == 'Отмена':
                    self.CS = [1]
                    self.bot.send_message(
                        message.chat.id, 'Отменено',
                        reply_markup=telebot.types.ReplyKeyboardRemove())
                    return None
                if self.variables['Name'] == 'Заменить':
                    self.variables['Name'] = self.oldname
                    self.oldname = ''
                    return None
            if regular.get_one_regular(
                    self.variables['Name'],
                    message.from_user.id, startid=False):
                self.CS = self.commonCS['askName'] + self.CS
                self.notfirst = True
                keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                buttons = ["Заменить", "Отмена"]
                keyboard.add(*buttons)
                self.oldname = self.variables['Name']
                return ["Данное имя уже есть в бд, хотите заменить или выбрать другое?", keyboard]
            self.oldname = ''
            return None

    def check_number(self, message):
        if self.cancel_or_not(message):
            keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["10", "25", "50"]
            keyboard.add(*buttons)
            if message.text.strip().isdigit():
                if 0 < int(message.text.strip()) <= 100:
                    self.variables.update({'Num': int(message.text.strip())})
                    return None
                self.CS = [1] + self.CS
                return ["Вы ввели число, которое не соответствует условию, введите другое", keyboard]
            self.CS = [1] + self.CS
            return ["Неверный формат, ожидается число", keyboard]

    def execute_begin(self, message):
        regular = Expressions.get(
            (Expressions.name == self.variables['Name']) &
            (Expressions.author_id << [message.from_user.id, -7]))
        self.flow = Flow(self.bot)
        self.th = Thread(
            target=self.flow.start,
            args=(message.chat.id, self.variables['Query'],
                  regular.expression, self.variables['Num']))
        self.th.start()
        self.expr = regular.expression
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Завершить", "Получить csv досрочно"]
        keyboard.add(*buttons)
        return ["Для получения csv или раннего завершения нажмите на кнопку", keyboard]

    def wait_stop(self, message):
        if not self.th.is_alive():
            self.CS = [1]
            handle_text(message)
        if message.text.strip() == 'Завершить':
            self.flow.stop(message.chat.id)
            self.CS = [1]
            self.bot.send_message(
                message.chat.id, "Завершено",
                reply_markup=telebot.types.ReplyKeyboardRemove())
            return None
        if message.text.strip() == "Получить csv досрочно":
            self.flow.create_csv(message.chat.id)
        self.bot.register_next_step_handler(message, self.wait_stop)

    def execute_add(self, message):
        if self.cancel_or_not(message):
            self.bot.send_message(
                message.chat.id,
                f"Ваше имя: {self.variables['Name']}\nВаше выражение: {self.variables['Regular']}",
                reply_markup=telebot.types.ReplyKeyboardRemove())
            regular = Expressions()
            try:
                regular.add_regular(
                    self.variables['Name'],
                    self.variables['Regular'],
                    message.from_user.id)
            except Exception:
                self.bot.send_message(
                    message.chat.id, f"Ой, ошибка...",
                    reply_markup=telebot.types.ReplyKeyboardRemove())

    def execute_delete(self, message):
        regular = Expressions()
        try:
            regular.del_regular(self.variables['Name'], message.from_user.id)
            self.bot.send_message(
                message.chat.id, f"Готово",
                reply_markup=telebot.types.ReplyKeyboardRemove())
        except Exception:
            self.bot.send_message(
                message.chat.id, f"Ой, ошибка...",
                reply_markup=telebot.types.ReplyKeyboardRemove())

    def list_of_ev(self, message):
        regular = Expressions()
        regulars = regular.get_all_regulars(message.from_user.id)
        self.bot.send_message(
            message.chat.id, '\n\n'.join(regulars),
            reply_markup=telebot.types.ReplyKeyboardRemove())
        return None

    def test_regular(self, message):
        if self.cancel_or_not(message):
            regular = Expressions.get(
                (Expressions.name == self.variables['Name']) &
                (Expressions.author_id << [message.from_user.id, -7]))
            self.flow = Flow(self.bot)
            self.th = Thread(target=self.flow.find, args=(
                self.variables['Query'], regular.expression, True, message.chat.id))
            self.th.start()

    def updateQuery(self, message):
        if message.text:
            self.variables.update({'Query': message.text.strip()})
        else:
            photo_id = message.photo[0].file_id
            file_info = bot.get_file(photo_id)
            text = f'http://api.telegram.org/file/bot5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA/{file_info.file_path}'
            self.variables.update({'Query': text})

    def processChat(self, message):
        res = self.CS[0](message)
        del self.CS[0]
        if res:
            if type(res) == list:
                self.bot.send_message(
                    message.chat.id, res[0],
                    reply_markup=res[1])
                self.bot.register_next_step_handler(message, self.processChat)
            else:
                self.bot.send_message(
                    message.chat.id, res,
                    reply_markup=telebot.types.ReplyKeyboardRemove())
                self.bot.register_next_step_handler(message, self.processChat)
        elif self.CS:
            self.processChat(message)
    
    def check_query(self, message):
        if message.text:
            self.cancel_or_not(message)


bot = telebot.TeleBot('5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA')


@ bot.message_handler(commands=["start"])
def start(message, res=False):
    bot.send_message(
        message.chat.id, 'Команды\n\n/begin\n/list\n/add\n/delete',
        reply_markup=telebot.types.ReplyKeyboardRemove())


@ bot.message_handler(content_types=["text"])
def handle_text(message):
    stage = Stage(bot)
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["IP адрес", "email", "Телефоны"]
    keyboard.add(*buttons)
    keyboard2 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons2 = ["10", "25", "50"]
    keyboard2.add(*buttons2)
    keyboard.add(*["Отмена команды"])
    keyboard4 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard4.add(*["Отмена команды"])
    keyboard
    stage.commonCS['askName'] = [
        lambda v: ["Введите имя", keyboard],
        lambda v: stage.variables.update({'Name': v.text.strip()})]
    CS = {
        '/begin': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_begin(v),
                                               lambda v: ["Введите запрос", keyboard4], lambda v: stage.check_query(v), lambda v: stage.updateQuery(v), lambda v: ["Сколько результатов искать? (Не более 100)", keyboard2], lambda v: stage.check_number(v), lambda v: stage.execute_begin(v), lambda v: stage.wait_stop(v)],
        '/add': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_add(v),
                                             lambda v: ["Введите регулярное выражение", keyboard4], lambda v: stage.variables.update({'Regular': v.text.strip()}), lambda v: stage.execute_add(v)],
        '/list': [lambda v: stage.list_of_ev(v)],
        '/delete': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_delete(v),
                                                lambda v: stage.execute_delete(v)],
        '/test_regular': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_begin(v),
                                                      lambda v: ["Введите ссылку", keyboard4], lambda v: stage.updateQuery(v), lambda v: stage.test_regular(v)]
    }
    try:
        stage.CS = CS[message.text.strip()]
        if stage.CS:
            stage.processChat(message)
    except Exception:
        print('Ошибка:\n', traceback.format_exc())


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.polling(none_stop=True, interval=0)

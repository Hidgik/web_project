import telebot
from data.regulars import Expressions, RegularResource
from data.settings import SettingResource, init_user
from threading import Thread
from flow import Flow
from register_search_sys import register_sys_for_text, register_sys_for_image


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
            regular = RegularResource()
            if regular.get_one_regular(
                    self.variables['Name'],
                    message.from_user.id, startid=False):
                return None
            self.CS = self.commonCS['askName'] + self.CS
            return "Данного имени нет в бд, введите другое"

    def ValidateName_for_begin(self, message):
        if self.cancel_or_not(message):
            regular = RegularResource()
            if regular.get_one_regular(
                    self.variables['Name'],
                    message.from_user.id):
                return None
            self.CS = self.commonCS['askName'] + self.CS
            choice_name = telebot.types.ReplyKeyboardMarkup(
                resize_keyboard=True)
            choice_name.add(*["IP адрес", "email", "Телефоны"])
            choice_name.add(*["Отмена команды"])
            return ["Данного имени нет в бд, введите другое", choice_name]

    def ValidateName_for_add(self, message):
        if self.cancel_or_not(message):
            regular = RegularResource()
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
                change = telebot.types.ReplyKeyboardMarkup(
                    resize_keyboard=True)
                buttons = ["Заменить", "Отмена"]
                change.add(*buttons)
                self.oldname = self.variables['Name']
                return ["Данное имя уже есть в бд, хотите заменить или выбрать другое?", change]
            self.oldname = ''
            return None

    def check_number(self, message):
        if self.cancel_or_not(message):
            choice_num = telebot.types.ReplyKeyboardMarkup(
                resize_keyboard=True)
            choice_num.add(*["10", "25", "50"])
            choice_num.add(*["Отмена команды"])
            if message.text.strip().isdigit():
                if 0 < int(message.text.strip()) <= 100:
                    self.variables.update({'Num': int(message.text.strip())})
                    return None
                self.CS = [1] + self.CS
                return ["Вы ввели число, которое не соответствует условию, введите другое", choice_num]
            self.CS = [1] + self.CS
            return ["Неверный формат, ожидается число", choice_num]

    def execute_begin(self, message):
        setting = SettingResource()
        info = setting.get_info(message.from_user.id)
        regular = Expressions.get(
            (Expressions.name == self.variables['Name']) &
            (Expressions.author_id << [message.from_user.id, -7]))
        self.flow = Flow(
            self.bot, self.variables['Query'],
            message.chat.id, [info.search_sys, info.search_sys_image],
            regular.expression, info.delim_csv, info.type_file)
        self.th = Thread(
            target=self.flow.start,
            args=(int(self.variables['Num']), ))
        self.th.start()
        self.expr = regular.expression
        wait_ = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Завершить", "Получить файл досрочно"]
        wait_.add(*buttons)
        return ["Для получения csv или раннего завершения нажмите на кнопку", wait_]

    def wait_stop(self, message):
        if not self.th.is_alive():
            self.CS = [1]
            handle_text(message)
        if message.text.strip() == 'Завершить':
            self.flow.stop()
            self.CS = [1]
            self.bot.send_message(
                message.chat.id, "Завершено",
                reply_markup=telebot.types.ReplyKeyboardRemove())
            return None
        if message.text.strip() == "Получить файл досрочно":
            self.flow.create_file()
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
            self.flow = Flow(
                self.bot, self.variables['Query'],
                message.chat.id, 'Google', regular.expression)
            self.th = Thread(target=self.flow.find, args=(
                self.variables['Query'], True))
            self.th.start()

    def updateQuery(self, message):
        if message.text:
            self.variables.update({'Query': message.text.strip()})
        else:
            photo_id = message.photo[0].file_id
            file_info = bot.get_file(photo_id)
            text = f'http://api.telegram.org/file/bot5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA/{file_info.file_path}'
            self.variables.update({'Query': ['image', text]})

    def change_num_lines(self, message):
        if self.cancel_or_not(message):
            choice_num = telebot.types.ReplyKeyboardMarkup(
                resize_keyboard=True)
            choice_num.add(*["10", "25", "50"])
            choice_num.add(*["Всегда спрашивать"])
            choice_num.add(*["Отмена команды"])
            if message.text.strip().isdigit() or message.text.strip() == 'Всегда спрашивать':
                if message.text.strip() == 'Всегда спрашивать' or 0 < int(
                        message.text.strip()) <= 100:
                    setting = SettingResource()
                    setting.change_object(
                        message.from_user.id,
                        {'default': message.text.strip()})
                    self.bot.send_message(
                        message.chat.id, "Обновлено",
                        reply_markup=telebot.types.ReplyKeyboardRemove())
                    return None
                self.CS = [1] + self.CS
                return ["Вы ввели число, которое не соответствует условию, введите другое", choice_num]
            self.CS = [1] + self.CS
            return ["Неверный формат, ожидается число", choice_num]

    def change_sys(self, message, text_or_im):
        if self.cancel_or_not(message):
            if text_or_im == 'text':
                if message.text.strip() in register_sys_for_text().keys():
                    setting = SettingResource()
                    setting.change_object(
                        message.from_user.id,
                        {'search_sys': message.text.strip()})
                    self.bot.send_message(
                        message.chat.id, "Обновлено",
                        reply_markup=telebot.types.ReplyKeyboardRemove())
                    return None
                cancel = telebot.types.ReplyKeyboardMarkup(
                    resize_keyboard=True)
                cancel.add(*["Отмена команды"])
                self.CS = [1] + self.CS
                return ["Такая поисковая система не реализована, введите другую", cancel]
            elif text_or_im == 'image':
                if message.text.strip() in register_sys_for_image().keys():
                    setting = SettingResource()
                    setting.change_object(
                        message.from_user.id,
                        {'search_sys_image': message.text.strip()})
                    self.bot.send_message(
                        message.chat.id, "Обновлено",
                        reply_markup=telebot.types.ReplyKeyboardRemove())
                    return None
                cancel = telebot.types.ReplyKeyboardMarkup(
                    resize_keyboard=True)
                cancel.add(*["Отмена команды"])
                self.CS = [1] + self.CS
                return ["Такая поисковая система не реализована, введите другую", cancel]

    def change_format(self, message):
        if self.cancel_or_not(message):
            if message.text.strip() in ['txt', 'csv']:
                setting = SettingResource()
                setting.change_object(
                    message.from_user.id,
                    {'type_file': message.text.strip()})
                self.bot.send_message(
                    message.chat.id, "Обновлено",
                    reply_markup=telebot.types.ReplyKeyboardRemove())
                return None
            cancel = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel.add(*["Отмена команды"])
            self.CS = [1] + self.CS
            return ["Такой формат не реализован, введите другой", cancel]

    def change_delim(self, message):
        if self.cancel_or_not(message):
            setting = SettingResource()
            setting.change_object(
                message.from_user.id,
                {'delim_csv': message.text.strip()})
            self.bot.send_message(
                message.chat.id, "Обновлено",
                reply_markup=telebot.types.ReplyKeyboardRemove())
            return None

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

    def get_settings(self, message):
        setting = SettingResource()
        info = setting.get_info(message.from_user.id)
        self.bot.send_message(
            message.chat.id,
            f"Текущие настройки:\n\nПриоритетная поисковая система для текста:{info.search_sys}\nПриоритетная поисковая система для картинок: {info.search_sys_image}\nФормат файла:\{info.type_file}\nРазделитель в csv файле: '{info.delim_csv}'\nКоличество ссылок с результатами: {info.default}",
            reply_markup=telebot.types.ReplyKeyboardRemove())

    def ask_num_res(self, message):
        setting = SettingResource()
        info = setting.get_info(message.from_user.id)
        if info.default != 'Всегда спрашивать':
            self.variables.update({'Num': info.default})
            self.CS = [
                1, lambda v: self.execute_begin(v),
                lambda v: self.wait_stop(v)]
            return None
        choice_num = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        choice_num.add(*["10", "25", "50"])
        choice_num.add(*["Отмена команды"])
        return ["Сколько результатов искать? (Не более 100)", choice_num]


bot = telebot.TeleBot('5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA')


@ bot.message_handler(commands=["start"])
def start(message, res=False):
    init_user(message.from_user.id)
    bot.send_message(
        message.chat.id, 'Команды\n\n/begin\n/list\n/add\n/delete',
        reply_markup=telebot.types.ReplyKeyboardRemove())


@ bot.message_handler(content_types=["text"])
def handle_text(message):
    stage = Stage(bot)

    choice_name = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    choice_name.add(*["IP адрес", "email", "Телефоны"])
    choice_name.add(*["Отмена команды"])

    cancel = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel.add(*["Отмена команды"])

    choice_num = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    choice_num.add(*["10", "25", "50"])
    choice_num.add(*["Всегда спрашивать"])
    choice_num.add(*["Отмена команды"])
    stage.commonCS['askName'] = [
        lambda v: ["Введите имя", choice_name],
        lambda v: stage.variables.update({'Name': v.text.strip()})]
    CS = {
        '/begin': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_begin(v),
                                               lambda v: ["Введите запрос", cancel], lambda v: stage.check_query(v),
                                               lambda v: stage.updateQuery(v), lambda v: stage.ask_num_res(v),
                                               lambda v: stage.check_number(v), lambda v: stage.execute_begin(v),
                                               lambda v: stage.wait_stop(v)],
        '/add': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_add(v),
                                             lambda v: ["Введите регулярное выражение", cancel],
                                             lambda v: stage.variables.update({'Regular': v.text.strip()}),
                                             lambda v: stage.execute_add(v)],
        '/list': [lambda v: stage.list_of_ev(v)],
        '/settings': [lambda v: stage.get_settings(v)],
        '/change_num_lines': [lambda v: ["Выберите стандартное значение количества строк", choice_num], lambda v: stage.change_num_lines(v)],
        '/change_sys_for_text': [lambda v: [f"Выберите приоритетную поисковую систему ({', '.join(register_sys_for_text().keys())})", cancel],
                                 lambda v: stage.change_sys(v, 'text')],
        '/change_sys_for_image': [lambda v: [f"Выберите приоритетную поисковую систему ({', '.join(register_sys_for_image().keys())})", cancel],
                                  lambda v: stage.change_sys(v, 'image')],
        '/change_delim': [lambda v: ["Введите разделитель для csv", cancel], lambda v: stage.change_delim(v)],
        '/change_format': [lambda v: ["Выберите формат вывода (txt или csv)", cancel], lambda v: stage.change_format(v)],
        '/delete': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_delete(v),
                                                lambda v: stage.execute_delete(v)],
        '/test_regular': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_begin(v),
                                                      lambda v: ["Введите ссылку", cancel], lambda v: stage.updateQuery(v),
                                                      lambda v: stage.test_regular(v)]
    }
    try:
        stage.CS = CS[message.text.strip()]
        if stage.CS:
            stage.processChat(message)
    except Exception:
        pass


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.polling(none_stop=True, interval=0)

import telebot
from data.regulars import Expressions

class Stage:
    def __init__(self, bot):
        self.bot = bot
        self.variables = {}
        self.commonCS = {}
        self.notfirst = False
        self.oldname = ''
    
    def ValidateName_for_delete(self, message):
        regular = Expressions()
        if regular.get_one_regular(self.variables['Name'], message.from_user.id, startid=False):
            return None
        self.CS = [1]
        self.bot.send_message(message.chat.id, "Данного имени нет в бд", reply_markup=telebot.types.ReplyKeyboardRemove())
        return None
    
    def ValidateName_for_begin(self, message):
        regular = Expressions()
        if regular.get_one_regular(self.variables['Name'], message.from_user.id):
            return None
        self.CS = self.commonCS['askName'] + self.CS
        return "Данного имени нет в бд, Введите другое"
    
    def ValidateName_for_add(self, message):
        regular = Expressions()
        if self.oldname:
            if self.variables['Name'] == 'Отмена':
                self.CS = [1]
                self.bot.send_message(message.chat.id, 'Отменено', reply_markup=telebot.types.ReplyKeyboardRemove())
                return None
            if self.variables['Name'] == 'Заменить':
                self.variables['Name'] = self.oldname
                self.oldname = ''
                return None
        if regular.get_one_regular(self.variables['Name'], message.from_user.id):
            self.CS = self.commonCS['askName'] + self.CS
            self.notfirst = True
            keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["Заменить", "Отмена"]
            keyboard.add(*buttons)
            self.oldname = self.variables['Name']
            return ["Данное имя уже есть в бд, хотите заменить или выбрать другое?", keyboard]
        self.oldname = ''
        return None

    def execute_begin(self):
        return None

    def execute_add(self, message):
        self.bot.send_message(message.chat.id, f"Ваше имя: {self.variables['Name']}\nВаше выражение: {self.variables['Regular']}", reply_markup=telebot.types.ReplyKeyboardRemove())
        regular = Expressions()
        try:
            regular.add_regular(self.variables['Name'], self.variables['Regular'], message.from_user.id)
        except Exception:
            self.bot.send_message(message.chat.id, f"Ой, ошибка...", reply_markup=telebot.types.ReplyKeyboardRemove())

    def execute_delete(self, message):
        regular = Expressions()
        try:
            regular.del_regular(self.variables['Name'], message.from_user.id)
            self.bot.send_message(message.chat.id, f"Готово", reply_markup=telebot.types.ReplyKeyboardRemove())
        except Exception:
            self.bot.send_message(message.chat.id, f"Ой, ошибка...", reply_markup=telebot.types.ReplyKeyboardRemove())

    def list_of_ev(self, message):
        regular = Expressions()
        regulars = regular.get_all_regulars(message.from_user.id)
        self.bot.send_message(message.chat.id, '\n\n'.join(regulars), reply_markup=telebot.types.ReplyKeyboardRemove())
        return None

    def processChat(self, message):
        res = self.CS[0](message)
        del self.CS[0]
        if res:
            if type(res) == list:
                self.bot.send_message(message.chat.id, res[0], reply_markup=res[1])
                self.bot.register_next_step_handler(message, self.processChat)
            else:
                self.bot.send_message(message.chat.id, res, reply_markup=telebot.types.ReplyKeyboardRemove())
                self.bot.register_next_step_handler(message, self.processChat)
        elif self.CS:
            self.processChat(message)


bot = telebot.TeleBot('5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA')
@bot.message_handler(commands=["start"])
def start(message, res=False):
    bot.send_message(message.chat.id, 'Команды\n\n/begin\n/list\n/add\n/delete', reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(content_types=["text"])
def handle_text(message):
    stage = Stage(bot)
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["IP адрес", "email", "Телефоны"]
    keyboard.add(*buttons)
    stage.commonCS['askName'] = [lambda v: ["Введите имя", keyboard], lambda v: stage.variables.update({'Name':v.text.strip()})]
    CS = {
        '/begin': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_begin(v),
            lambda v: "Введите запрос", lambda v: stage.variables.update({'Query':v.text.strip()}), lambda v: stage.execute_begin()],
        '/add': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_add(v),
            lambda v: "Введите регулярное выражение", lambda v: stage.variables.update({'Regular':v.text.strip()}), lambda v: stage.execute_add(v)],
        '/stop':[],
        '/list': [lambda v: stage.list_of_ev(v)],
        '/delete': stage.commonCS['askName'] + [lambda v: stage.ValidateName_for_delete(v),
            lambda v: stage.execute_delete(v)]
    }
    try:
        stage.CS=CS[message.text.strip()]
        if stage.CS:
            stage.processChat(message) 
    except Exception:
        pass


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.polling(none_stop=True, interval=0)

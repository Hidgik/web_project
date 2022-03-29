import telebot


class Stage:
    def __init__(self, bot):
        self.bot = bot
        self.variables = {}
        self.commonCS = {}
    
    def ValidateName(self):
        if self.variables['Name'] == '10':
            return None
        self.CS = self.commonCS['askName'][:-1] + self.CS
        return "Данного имени нет в бд, Введите другое"

    def execute(self):
        return None
    
    def processChat(self, message):
        res = self.CS[0](message.text.strip())
        del self.CS[0]
        if res:
            self.bot.send_message(message.chat.id, res, reply_markup=telebot.types.ReplyKeyboardRemove())
            self.bot.register_next_step_handler(message, self.processChat)
        elif self.CS:
            self.processChat(message)
        else:
            self.bot.send_message(message.chat.id, f"Ваше имя: {self.variables['Name']}\nВаш запрос: {self.variables['Query']}", reply_markup=telebot.types.ReplyKeyboardRemove())


bot = telebot.TeleBot('5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA')
@bot.message_handler(commands=["start"])
def start(message, res=False):
    bot.send_message(message.chat.id, 'Команды\n\n/begin\n/list\n/add\n/delete', reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(content_types=["text"])
def handle_text(message):
    stage = Stage(bot)
    stage.commonCS['askName'] = [lambda v: "Введите имя", lambda v: stage.variables.update({'Name':v}), lambda v: stage.ValidateName()]
    CS = {
        '/begin': stage.commonCS['askName'] + [            
            lambda v: "Введите запрос", lambda v: stage.variables.update({'Query':v}), lambda v: stage.execute()],
        '/add':[
            lambda v: "Введите имя", lambda v: stage.variables.update({'Name':v}), lambda v: stage.ValidateName(),
            lambda v: "Введите выражение", lambda v: stage.variables.update({'Query':v}), lambda v: stage.execute()],
    }
    stage.CS=CS[message.text.strip()]
    if stage.CS:
        stage.processChat(message)


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.polling(none_stop=True, interval=0)

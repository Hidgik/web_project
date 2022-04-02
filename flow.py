import telebot
import urllib.request
import re
import googlesearch
from googlesearch import search

class Flow:
    def __init__(self, bot):
        self.bot = bot
        self.flag = True
    
    def start(self, idd, query, regular):
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Пауза", "Стоп"]
        keyboard.add(*buttons)
        self.bot.send_message(idd, query, reply_markup=keyboard)
        self.bot.send_message(idd, regular, reply_markup=keyboard)
        links = []
        count = 0
        while self.flag:
            user_agent = googlesearch.get_random_user_agent()
            print(user_agent)
            for j in search(query, start=count, stop=10, user_agent=user_agent): 
                try:
                    links.append(j)
                except Exception:
                    pass
            count += 10
            for i in links:
                try:
                    uf = urllib.request.urlopen(i)
                    html = uf.read()
                    items = [
                        m.group()
                        for m in re.finditer(regular, html.decode('utf-8'))
                    ]
                    if items:
                        if not self.flag:
                            break
                        self.bot.send_message(idd, i, reply_markup=keyboard)
                        self.bot.send_message(idd, ", ".join(list(set(items))), reply_markup=keyboard)
                except Exception:
                    pass
            if count == 100:
                break
            links = []
        self.bot.send_message(idd, "Готово", reply_markup=telebot.types.ReplyKeyboardRemove())
    
    def stop(self):
        self.flag = False
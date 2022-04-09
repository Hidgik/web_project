import telebot
import urllib.request
import re
import googlesearch
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class Flow:
    def __init__(self, bot):
        self.bot = bot
        self.flag = True
        self.count = 0
        self.page = 1
        self.links = []

    def start(self, idd, query, regular):
        self.flag = True
        ua = UserAgent()
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Пауза", "Стоп"]
        keyboard.add(*buttons)
        self.bot.send_message(idd, query, reply_markup=keyboard)
        self.bot.send_message(idd, regular, reply_markup=keyboard)
        while self.flag:
            if '5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA' not in query:
                user_agent = googlesearch.get_random_user_agent()
                for j in search(
                        query, start=self.count, stop=10, user_agent=user_agent):
                    try:
                        self.links.append(j)
                    except Exception:
                        pass
                self.count += 10
            else:
                url = fr'https://yandex.ru/images/search?source=collections&rpt=imageview&p={self.page}&url={query}'
                soup = BeautifulSoup(requests.get(url, headers={'User-Agent': ua.random}).text, 'lxml')
                similar = soup.find_all('div', class_='CbirSites-ItemTitle')
                for i in similar:
                    self.links.append(f"{i.find('a').get('href')}")
                    #  e = str(i.find('a'))
                    # print(f"""{e[e.find('target="_blank"') + 16:-4]}\n""")
                self.page += 1
            for i in self.links:
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
                        self.bot.send_message(
                            idd, ", ".join(list(set(items))),
                            reply_markup=keyboard)
                except Exception:
                    pass
            if self.count == 100:
                break
            self.links = []

    def stop(self):
        self.flag = False

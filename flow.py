import csv
import sys
import traceback
import telebot
import urllib.request
import re
import googlesearch
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from random import choice
from string import ascii_letters
import os


class Flow:
    def __init__(self, bot):
        self.bot = bot
        self.flag = True
        self.page = 1
        self.links = []
        self.text = []
        self.al = []
        self.count = 0
        self.count2 = 0
        self.count3 = 0

    def start(self, idd, query, regular, num=100):
        self.flag = True
        ua = UserAgent()
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Пауза", "Стоп"]
        keyboard.add(*buttons)
        # , reply_markup=keyboard)
        msg = self.bot.send_message(idd, f"Выполнено 0/{num}")
        while self.flag and self.count2 < num:
            if '5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA' not in query:
                user_agent = googlesearch.get_random_user_agent()
                for j in search(query, start=self.count, stop=10,
                                user_agent=user_agent):
                    self.links.append(j)
                self.count += 10
            else:
                url = fr'https://yandex.ru/images/search?source=collections&rpt=imageview&p={self.page}&url={query}'
                soup = BeautifulSoup(requests.get(
                    url, headers={'User-Agent': ua.random}).text, 'lxml')
                similar = soup.find_all('div', class_='CbirSites-ItemTitle')
                for i in similar:
                    self.links.append(f"{i.find('a').get('href')}")
                self.page += 1
            for i in self.links:
                res = self.find(i, regular)
                if res:
                    self.count2 += 1
                    self.bot.edit_message_text(
                        chat_id=idd, message_id=msg.message_id,
                        text=f"Выполнено {self.count2}/{num}")
                if not self.flag:
                    break
                self.count3 += 1
                if self.count2 == num:
                    self.create_csv(idd)
                    self.bot.send_message(
                        idd, "Завершено",
                        reply_markup=telebot.types.ReplyKeyboardRemove())
                    break
            self.links = []
        self.count = self.count3

    def find(self, query, regular, typ=False, idd=''):
        res = []
        try:
            uf = urllib.request.urlopen(query)
            html = uf.read()
            items = [
                m.group()
                for m in re.finditer(regular, html.decode('utf-8'))
            ]
            if items:
                try:
                    reqs = requests.get(query)
                    soup = BeautifulSoup(reqs.text, 'html.parser')
                    for title in soup.find_all('title'):
                        tex = title.get_text()
                    res.append(f"<a href='{query}'>{tex}</a>")
                    self.al.append([query, tex])
                except Exception:
                    res.append(query)
                    self.al.append([query, "Текст не найден"])
                res.append(", ".join(list(set(items))))
                self.al[-1] = self.al[-1] + [", ".join(list(set(items)))]
            if typ:
                self.bot.send_message(idd, res[1])
            return res
        except Exception:
            pass

    def stop(self, idd):
        self.create_csv(idd)
        self.flag = False

    def create_csv(self, idd):
        if self.al:
            name = ''.join(choice(ascii_letters) for _ in range(12))
            while os.path.exists(name):
                name = ''.join(choice(ascii_letters) for _ in range(12))
            with open(f'{name}.csv', 'w', newline='', encoding='utf16') as csvfile:
                writer = csv.writer(
                    csvfile, delimiter=';', quotechar='"',
                    quoting=csv.QUOTE_MINIMAL)
                for i in self.al:
                    c = f'=ГИПЕРССЫЛКА("{i[0]}";"{i[1]}")'
                    writer.writerow([c, i[2]])
            self.bot.send_document(idd, open(f'{name}.csv', 'rb'))
            f = os.path.join(os.path.abspath(f'{name}.csv'))
            os.remove(f)

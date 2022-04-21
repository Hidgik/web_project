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


class YandexSearch:
    def __init__(self, query):
        self.query = query
        self.ua = UserAgent()

    def search_text(self):
        pass

    def search_image(self, page):
        res = []
        url = fr'https://yandex.ru/images/search?source=collections&rpt=imageview&p={page}&url={self.query}'
        soup = BeautifulSoup(requests.get(
            url, headers={'User-Agent': self.ua.random}).text, 'lxml')
        links = soup.find_all('div', class_='CbirSites-ItemTitle')
        for link in links:
            res.append(f"{link.find('a').get('href')}")
        return res


class GoogleSearch:
    def __init__(self, query):
        self.query = query

    def search_text(self, start, stop=10):
        res = []
        user_agent = googlesearch.get_random_user_agent()
        for j in search(self.query, start=start, stop=stop,
                        user_agent=user_agent):
            res.append(j)
        return res

    def search_image(self):
        pass


class Flow:
    def __init__(self, bot, query, chat_id, search_sys, regular):
        self.bot = bot
        self.query = query
        self.chat_id = chat_id
        self.search_sys = search_sys
        self.regular = regular
        self.flag = True
        self.page = 1
        self.links = []
        self.al = []
        self.count = 0
        self.count2 = 0
        dict_sys = {'Google': GoogleSearch, 'Yandex': YandexSearch}
        self.search_sys = dict_sys[search_sys](query)

    def start(self, num=100):
        msg = self.bot.send_message(self.chat_id, f"Выполнено 0/{num}")
        while self.flag and self.count2 < num:
            if '5260510912:AAHbZZ2dsYVFUapmsN2VLMY-KP62A8NSjuA' not in self.query:
                self.links = self.search_sys.search_text(self.count)
                self.count += 10
            else:
                self.links = self.search_sys.search_image(self.page)
                self.page += 1
            for i in self.links:
                res = self.find(i)
                if res:
                    self.count2 += 1
                    self.bot.edit_message_text(
                        chat_id=self.chat_id, message_id=msg.message_id,
                        text=f"Выполнено {self.count2}/{num}")
                if not self.flag:
                    break
                if self.count2 == num:
                    self.create_csv()
                    self.bot.send_message(
                        self.chat_id, "Завершено",
                        reply_markup=telebot.types.ReplyKeyboardRemove())
                    break
            self.links = []

    def find(self, link, typ=False):
        res = []
        try:
            uf = urllib.request.urlopen(link)
            html = uf.read()
            items = [
                m.group()
                for m in re.finditer(self.regular, html.decode('utf-8'))
            ]
            if items:
                try:
                    reqs = requests.get(link)
                    soup = BeautifulSoup(reqs.text, 'html.parser')
                    for title in soup.find_all('title'):
                        tex = title.get_text()
                    res.append(f"<a href='{link}'>{tex}</a>")
                    self.al.append([link, tex])
                except Exception:
                    res.append(link)
                    self.al.append([link, "Текст не найден"])
                res.append(", ".join(list(set(items))))
                self.al[-1] = self.al[-1] + [", ".join(list(set(items)))]
            if typ:
                self.bot.send_message(self.chat_id, res[1], reply_markup=telebot.types.ReplyKeyboardRemove())
            return res
        except Exception:
            pass

    def stop(self):
        self.create_csv()
        self.flag = False

    def create_csv(self):
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
            self.bot.send_document(self.chat_id, open(f'{name}.csv', 'rb'))
            f = os.path.join(os.path.abspath(f'{name}.csv'))
            os.remove(f)

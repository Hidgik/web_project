import csv
import telebot
import urllib.request
import re
import requests
from bs4 import BeautifulSoup
from random import choice
from string import ascii_letters
import os
from register_search_sys import register_sys_for_text, register_sys_for_image


class Flow:
    def __init__(self, bot, query, chat_id, search_sys, regular, delim,
                 type_format):
        self.bot = bot
        self.delim = delim
        self.chat_id = chat_id
        self.type_format = type_format
        self.search_sys = search_sys
        self.regular = regular
        self.flag = True
        self.page = 1
        self.links = []
        self.al = []
        self.count = 0
        self.count2 = 0
        self.query = query
        if type(query) == list:
            dict_sys = register_sys_for_image()
            self.search_sys = dict_sys[search_sys[1]](query[1])
        else:
            dict_sys = register_sys_for_text()
            self.search_sys = dict_sys[search_sys[0]](query)

    def start(self, num=100):
        msg = self.bot.send_message(self.chat_id, f"Выполнено 0/{num}")
        while self.flag and self.count2 < num:
            if type(self.query) != list:
                self.links = self.search_sys.search_text(self.count, self.page)
                self.count += 10
                self.page += 1
            else:
                self.links = self.search_sys.search_image(
                    self.count, self.page)
                self.count += 10
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
                    self.create_file()
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
                self.bot.send_message(
                    self.chat_id, res[1],
                    reply_markup=telebot.types.ReplyKeyboardRemove())
            return res
        except Exception:
            pass

    def stop(self):
        self.create_file()
        self.flag = False

    def create_file(self):
        if self.al:
            name = ''.join(choice(ascii_letters) for _ in range(12))
            while os.path.exists(name):
                name = ''.join(choice(ascii_letters) for _ in range(12))
            if self.type_format == 'csv':
                with open(f'{name}.csv', 'w', newline='', encoding='utf16') as csvfile:
                    writer = csv.writer(
                        csvfile, delimiter=self.delim, quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
                    for i in self.al:
                        c = f'=ГИПЕРССЫЛКА("{i[0]}";"{i[1]}")'
                        writer.writerow([c, i[2]])
                self.bot.send_document(self.chat_id, open(f'{name}.csv', 'rb'))
                f = os.path.join(os.path.abspath(f'{name}.csv'))
                os.remove(f)
            else:
                with open(f'{name}.txt', 'w', newline='\n') as txtfile:
                    for i in self.al:
                        print(f"{i[0]}" + '\n' + f"{i[2]}" + "\n", file=txtfile)
                self.bot.send_document(self.chat_id, open(f'{name}.txt', 'r'))
                f = os.path.join(os.path.abspath(f'{name}.txt'))
                os.remove(f)

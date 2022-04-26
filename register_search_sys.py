import googlesearch
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


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
        for j in googlesearch.search(self.query, start=start, stop=stop,
                        user_agent=user_agent):
            res.append(j)
        return res

    def search_image(self):
        pass


class MailRuSearch:
    def __init__(self, query):
        self.query = query
        self.ua = UserAgent()

    def search_text(self, start, stop=10):
        res = []
        url = fr'https://go.mail.ru/search?q=Привет&sf={start}'
        soup = BeautifulSoup(requests.get(
            url, headers={'User-Agent': self.ua.random}).text, 'lxml')
        links = soup.find_all('span', class_='block-info__hidden')
        for link in links:
            res.append(f"{link.find('a').get('onmousedown')[12:-9]}")
        return res

    def search_image(self):
        pass


def register_sys():
    sys = {'Google': GoogleSearch, 'Yandex': YandexSearch, 'MailRu': MailRuSearch}
    return sys
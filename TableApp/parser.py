import requests
from datetime import datetime
from bs4 import BeautifulSoup

import time
import threading
from queue import Queue

HOST_ROZETKA = 'https://rozetka.com.ua/'
HOST_EPICENTR = 'https://epicentrk.ua/'
HOST_BIGL = 'https://bigl.ua/'

URL_ROZETKA ='https://rozetka.com.ua/ua/krupy/c4628397/sort=cheap;vid-225787=grechka/'
URL_EPICENTR = 'https://epicentrk.ua/ua/shop/krupy-i-makaronnye-izdeliya/fs/vid-krupa-grechnevaya/?sort=asc'
URL_BIGL = 'https://bigl.ua/ua/search?search_term=%D0%BA%D1%80%D1%83%D0%BF%D0%B0+%D0%B3%D1%80%D0%B5%D1%87%D0%B0%D0%BD%D0%B0&category=20521&sort=price'

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
}


result = []


def get_html(url, params=''):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_groats_rozetka(q, url=URL_ROZETKA, count_items=3):
    event = threading.Event()
    html = get_html(url)
    soup = BeautifulSoup(html.text, 'lxml')
    items = soup.find_all('li', class_='catalog-grid__cell')
    groats = []

    for item, _ in zip(items, range(count_items)):
        groats.append(
            {
                'title': item.find('span', class_='goods-tile__title').get_text(strip=True),
                'price': item.find('span', class_='goods-tile__price-value').get_text(strip=True).replace(",", "."),
                'link_img': item.find('img', class_='lazy_img_hover').get('src'),
                'link_item': item.find('a', class_='goods-tile__picture').get('href')
            }
        )
    q.put((groats, event))
    event.wait()


def get_groats_epicentr(q, url=URL_EPICENTR, count_items=3):
    event = threading.Event()
    html = get_html(url)
    soup = BeautifulSoup(html.text, 'lxml')
    items = soup.find_all('div', class_='columns product-Wrap card-wrapper')
    groats = []
    for item, _ in zip(items, range(count_items)):
        groats.append(
            {
                'title': item.find('div', class_='card__name').get_text(strip=True),
                'price': item.find('span', class_='card__price-sum').get_text(strip=True)[:-3].replace(",", "."),
                'link_img': item.find('a', class_='card__photo').find('img').get('src'),
                'link_item': HOST_EPICENTR + item.find('a', class_='custom-link custom-link--big custom-link--inverted custom-link--blue').get('href')
            }
        )
    q.put((groats, event))
    event.wait()


def get_groats_bigl(q, url=URL_BIGL, count_items=3):
    event = threading.Event()
    html = get_html(url)
    soup = BeautifulSoup(html.text, 'lxml')
    items = soup.find_all('div', class_='bgl-product')
    groats = []
    for item, _ in zip(items, range(count_items)):
        groats.append(
            {
                'title': item.find('span', class_='translate').get_text(strip=True),
                'price': item.find('span', class_='bgl-product-price__value').get_text(strip=True).replace(",", "."),
                'link_img': item.find('img', class_='ek-picture__item').get('src'),
                'link_item': item.find('a', class_='bgl-product__title').get('href')
            }
        )
    q.put((groats, event))
    event.wait()


def packer(q, count_iterations):
    for i in range(count_iterations):
        value, event = q.get()
        for j in value:
            result.append(j)

        event.set()
        q.task_done()


def get_groats(count_items=3):
    global result
    result = []
    q = Queue()

    thread_one = threading.Thread(target=get_groats_rozetka, args=(q, URL_ROZETKA, count_items))
    thread_second = threading.Thread(target=get_groats_epicentr, args=(q, URL_EPICENTR, count_items))
    thread_third = threading.Thread(target=get_groats_bigl, args=(q, URL_BIGL, count_items))
    thread_packer = threading.Thread(target=packer, args=(q, count_items))
    thread_one.start()
    thread_second.start()
    thread_third.start()
    thread_packer.start()
    q.join()
    limit = count_items * 3
    while len(result) < limit:
        time.sleep(0.01)
    return result


if __name__ == '__main__':
    def print_items(items):
        for item in items:
            print(item)
    a = datetime.now()
    groats = get_groats(3)
    b = datetime.now()
    print_items(groats)
    print(b-a)

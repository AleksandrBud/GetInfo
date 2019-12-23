import requests
import time
import json
import datetime
import sys
import con_db
from bs4 import BeautifulSoup
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists

sys.path.insert(0, "~/bin")


def get_profile():
    profile = webdriver.FirefoxProfile()
    #    profile.set_preference("browser.autostart", True)
    profile.set_preference("browser.privatebrowsing.autostart", True)
    return profile


def get_page_html(link):
    html = requests.get(link).text
    return BeautifulSoup(html, 'lxml')


# now = datetime.datetime.fromtimestamp(1577018142).strftime('%Y-%m-%d %H:%M:%S')
# d142)atetime.(1577018
asd = con_db.connect_string()
db_conect = create_engine(asd)
Base = declarative_base()


class News(Base):
    __tablename__ = 'news'
    date = Column(Date, primary_key=True)
    description = Column(String(200), primary_key=True)
    link = Column(String(200))
    source = Column(String(20))

    def __init__(self, date, desc, ln, source):
        self.date = date
        self.description = desc
        self.link = ln
        self.source = source


tran_db = db_conect.connect()
Session = sessionmaker(bind=db_conect)
session = Session()

main_link = 'https://www.rbc.ru/'
# Используем драйвер Firefox для имитации работы пользователя в браузере
driver = webdriver.Firefox(firefox_profile=get_profile())
driver.implicitly_wait(10)
driver.get(main_link)
last_height = driver.execute_script('return document.body.scrollHeight')
# Прокручиваем страницу до конца, для загрузки всех элементов (они подгружаются динамически)
for i in range(10):
    driver.execute_script('window.scrollTo(0,  document.body.scrollHeight);')
    time.sleep(3)
    last_height = driver.execute_script('return document.body.scrollHeight')
html = driver.page_source
driver.quit()
# Начинаем парсить страницу
parsed_html = BeautifulSoup(html, 'lxml')
news_blok = parsed_html.find_all('a', {'class', 'news-feed__item js-news-feed-item js-yandex-counter'})
news = []
for line_news in news_blok:
    date_modify = datetime.datetime.fromtimestamp(int(line_news['data-modif'])).strftime('%Y-%m-%d %H:%M:%S')
    new = {'date': date_modify,
           'href': line_news['href'],
           'desc': line_news.find('span', {'class': 'news-feed__item__title'}).getText()[2:].strip(),
           'source': 'RBC'}
    news.append(new)
    a = News(new['date'], new['desc'], new['href'], new['source'])
    ex = session.query(exists().where(News.date == a.date and News.description == a.description)).scalar()
    if not ex:
        session.add(a)
        session.commit()

main_link = 'https://bcs-express.ru'
category_input = int(input('Выбириет категорию для БКС:\n 1 - Все\n 2 - Российский рынок\n 3 - Мировой рынок\n 4 - '
                           'Валютный рынок\n 5 - Рынок нефти:\n'))
category_list = {1: '/category', 2: '/category/rossiyskiy-rynok', 3: '/category/mirovye-rynki',
                 4: '/category/valyutnyy-rynok', 5: '/category/rynok-nefti'}
month = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
         'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}
category = category_list[category_input]

parsed_html = get_page_html(main_link + category)
#   Получаем id первой новости
first_id_news = parsed_html.find('a', {'class', 'feed-item__favorite tooltip favorite js-favorite'})['data-id']
category_link = category.split('/')[-1]

for i in range(3):
    #   Формируем ссылку для доступа к API
    link = f'/webapi/api/news/getlist?after={first_id_news}&rubric={category_link}'
    #   Грузим информацию
    data_api = json.loads(get_page_html(main_link + link).find('p').getText())
    for line_news in data_api['items']:
        date_split = line_news['publishDate'].split(' ')
        dt = '2019' + '-' + str(month[date_split[1]]) + '-' + date_split[0] + ' ' + date_split[3] + ':00'
        new = {'date': dt,
               'href': main_link + line_news['hyperLink'],
               'desc': line_news['title'],
               'source': 'BCS'}
        first_id_news = line_news['id']
        news.append(new)
        a = News(new['date'], new['desc'], new['href'], new['source'])
        ex = session.query(exists().where(News.date == a.date and News.description == a.description)).scalar()
        if not ex:
            session.add(a)
            session.commit()

#with open('news.json', 'w', encoding='utf-8') as f:
#    json.dump(news, f, ensure_ascii=False, indent=4)
#for i in news:
#    pprint(i)
for instance in session.query(News).filter(News.date > '2019-12-22 00:00:00'):
    print(instance.description, instance.link)

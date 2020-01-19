import sys
import requests
import time
import json
import datetime
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
from lxml import html


def get_profile():
    profile = webdriver.FirefoxProfile()
    #    profile.set_preference("browser.autostart", True)
    profile.set_preference("browser.privatebrowsing.autostart", True)
    return profile


def get_page_html_BS(link):
    headers = {
        'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/79.0.3945.79 Chrome/79.0.3945.79 Safari/537.36'}
    ret_html = requests.get(link, headers=headers).text
    return BeautifulSoup(ret_html, 'lxml')


def get_html(link):
    response = requests.get(link).text
    ret_html = html.fromstring(response)
    return ret_html


class News:
    session = ''

    def __init__(self, connection_string):
        engine = create_engine(connection_string)
        session_maker = sessionmaker(bind=engine)
        self.session = session_maker()

    class NewsDB(declarative_base()):
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

    def unique_record(self, new_date, new_desc):
        result = self.session.query(exists().where(
            self.NewsDB.description == new_desc)).scalar()
        return result

    def new_record(self, arr_news: object) -> object:
        for element in arr_news:
            if not self.unique_record(element['date'], element['desc']):
                record = self.NewsDB(element['date'], element['desc'], element['href'], element['source'])
                self.session.add(record)
                self.session.commit()
            else:
                print(element['date'], element['desc'])

    def get_records_by_date(self, date_from, date_to):
        for instance in self.session.query(self.NewsDB).filter(self.NewsDB.date > date_from,
                                                               self.NewsDB.date < date_to):
            print(instance.date, instance.description, instance.link)


class RBC:
    main_link = 'https://www.rbc.ru/'
    PAUSE = 2

    def get_html(self):
        driver = webdriver.Firefox(firefox_profile=get_profile())
        driver.implicitly_wait(5)
        driver.get(self.main_link)
        new_height = driver.execute_script('return document.body.scrollHeight')
        last_height = ''
        while last_height != new_height:
            last_height = new_height
            driver.execute_script('window.scrollTo(0,  document.body.scrollHeight);')
            time.sleep(self.PAUSE)
            new_height = driver.execute_script('return document.body.scrollHeight')
        ret_html = driver.page_source
        driver.quit()
        return ret_html

    def parce_html_BS(self, proc_html):
        parsed_html = BeautifulSoup(proc_html, 'lxml')
        news_blok = parsed_html.find_all('a', {'class', 'news-feed__item js-news-feed-item js-yandex-counter'})
        news = []
        for line_news in news_blok:
            date_modify = datetime.datetime.fromtimestamp(int(line_news['data-modif'])).strftime('%Y-%m-%d %H:%M:%S')
            new = {'date': date_modify,
                   'desc': line_news.find('span', {'class': 'news-feed__item__title'}).getText()[2:].strip(),
                   'href': line_news['href'],
                   'source': 'RBC'}
            news.append(new)
        return news


class BCS:
    main_link = 'https://bcs-express.ru'
    category = ''
    category_list = {1: '/category', 2: '/category/rossiyskiy-rynok', 3: '/category/mirovye-rynki',
                     4: '/category/valyutnyy-rynok', 5: '/category/rynok-nefti'}

    def __init__(self):
        self.category_input = int(input('Выбириет категорию для БКС:\n 1 - Все\n 2 - Российский рынок\n 3 - Мировой '
                                        'рынок\n 4 - Валютный рынок\n 5 - Рынок нефти:\n'))

    def get_html(self):
        category = self.category_list[self.category_input]
        ret_html = get_page_html_BS(self.main_link + category)
        return ret_html

    def get_news_api(self, proc_html):
        #   Получаем id первой новости
        first_id_news = proc_html.find('a', {'class', 'feed-item__favorite tooltip favorite js-favorite'})['data-id']
        category_link = self.category.split('/')[-1]
        news = []
        # for i in range(3):
        last_id = 0
        while last_id < int(first_id_news):
            if last_id != 0:
                first_id_news = last_id
            #   Формируем ссылку для доступа к API
            link = ''
            if category_link == '/category':
                link = f'/webapi/api/news/getlist?after={first_id_news}'
            else:
                link = f'/webapi/api/news/getlist?after={first_id_news}&rubric={category_link}'
            data_api = json.loads(get_page_html_BS(self.main_link + link).find('p').getText())
            for line_news in data_api['items']:
                date_split = line_news['publishDate'].split(' ')
                if len(date_split) == 4:
                    dt = datetime.datetime.now().year.__str__() + '-' + str(month[date_split[1]]) + '-' + date_split[
                        0] + ' ' + date_split[3] + ':00'
                elif len(date_split) == 3:
                    dt = date_split[2] + '-' + str(month[date_split[1]]) + '-' + date_split[0] + ' ' + '00:00:00'
                new = {'date': dt,
                       'desc': line_news['title'],
                       'href': self.main_link + line_news['hyperLink'],
                       'source': 'BCS'}
                last_id = line_news['id']
                news.append(new)
        return news


class Mailru:
    main_link = 'https://mail.ru/'

    def __init__(self):
        pass

    def get_news_xpath(self):
        response = requests.get(self.main_link).text
        ret_html = html.fromstring(response)
        main_news = ret_html.xpath("//div[contains(@id,'news:item')]")
        news_arr = []
        for n in main_news:
            href = n.xpath(".//a/@href")[0]
            response_link = requests.get(href).text
            ret_html_link = html.fromstring(response_link)
            date_news_s = ret_html_link.xpath(".//span[@class = 'note__text breadcrumbs__text js-ago']/@datetime")[0]
            datetime_news = datetime.datetime.fromisoformat(date_news_s)
            datetime_news = datetime_news + datetime.timedelta(hours=int(datetime_news.timetz().__str__()[-5:-3]))
            date_news = datetime_news.strftime('%Y-%m-%d %H:%M:%S')
            desc = n.xpath(".//span[contains(@class,'news__list__item__link__text')]/text()")[0].replace('\xa0', ' ')
            if len(desc) != 0:
                new = {'date': date_news,
                       'desc': desc,
                       'href': href,
                       'source': 'MAIL.RU'}
                news_arr.append(new)
        return news_arr


class Lenta:
    main_link = 'https://lenta.ru'

    def __init__(self):
        pass

    def get_news_xpath(self):
        response = requests.get(self.main_link).text
        ret_html = html.fromstring(response)
        main_news = ret_html.xpath(".//div[@class='b-yellow-box__wrap']/div[@class='item']/a")
        news_arr = []
        for n in main_news:
            href = n.xpath("@href")[0]
            desc = n.xpath("text()")[0].replace('\xa0', ' ')
            link_arr = href.split('/')
            year = link_arr[2]
            month = link_arr[3]
            day = link_arr[4]
            if len(day) > 2:
                year = day[-8:-4]
                month = day[-11:-9]
                day = day[-14:-12]
            date_news = year + '-' + month + '-' + day + ' ' + '00:00:00'
            new = {'date': date_news,
                   'desc': desc,
                   'href': self.main_link + href,
                   'source': 'LENTA.RU'}
            news_arr.append(new)
        return news_arr


class Yandex:
    main_link = 'https://yandex.ru/news/'

    def __init__(self):
        pass

    def get_news_xpath(self):
        response = requests.get(self.main_link).text
        ret_html = html.fromstring(response)
        # main_news = ret_html.xpath(".//div[@class='stories-set stories-set_main_yes stories-set_pos_0']")
        table_news = ret_html.xpath("//td[@class='stories-set__item']")
        news_arr = []
        for n in table_news:
            href = n.xpath(".//a[@class='link link_theme_black i-bem']/@href")[0]
            desc = n.xpath(".//a[@class='link link_theme_black i-bem']/text()")[0].replace('\xa0', ' ')
            date_news = n.xpath(".//div[@class='story__date']/text()")[0]
            split_arr = n.xpath(".//div[@class='story__date']/text()")[0].replace('\xa0', ' ').split(' ')
            year = datetime.datetime.now().year.__str__()
            month = datetime.datetime.now().month.__str__()
            if len(month) == 1:
                month = '0' + month
            day_str = ''
            if len(split_arr) > 2:
                day_str = split_arr[-3]
            day = datetime.datetime.now().day.__str__()
            if day_str == 'вчера':
                day = str(int(day) - 1)
            if len(day) == 1:
                day = '0' + day
            date_news = year + '-' + month + '-' + day + ' ' + split_arr[-1] + ':' + '00'
            new = {'date': date_news,
                   'desc': desc,
                   'href': self.main_link + href,
                   'source': 'YANDEX.RU'}
            news_arr.append(new)
        return news_arr


month = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
         'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}
input_source = int(input('Из какого источника собирать данные:\n1. РБК\n2. БКС\n3. Mail\n4. Lenta\n5. Yandex\n0. '
                         'Вывод из БД\nВвод:'))

news_collection = News(con_db.connect_string())
if input_source == 1:
    rbc = RBC()
    rbc_html = rbc.get_html()
    arr_news = rbc.parce_html_BS(rbc_html)
    news_collection.new_record(arr_news)
elif input_source == 2:
    bcs = BCS()
    arr_news = bcs.get_news_api(bcs.get_html())
    news_collection.new_record(arr_news)
elif input_source == 3:
    mail = Mailru()
    arr_news = mail.get_news_xpath()
    news_collection.new_record(arr_news)
elif input_source == 4:
    l_news = Lenta()
    arr_news = l_news.get_news_xpath()
    news_collection.new_record(arr_news)
elif input_source == 5:
    yandex = Yandex()
    arr_news = yandex.get_news_xpath()
    news_collection.new_record(arr_news)
elif input_source == 0:
    search_date = input('Введите дату в формате (ддммгггг)')
    search_date_from = search_date[4:8] + '-' + search_date[2:4] + '-' + search_date[:2] + ' 00:00:00'
    search_date_to = search_date[4:8] + '-' + search_date[2:4] + '-' + search_date[:2] + ' 23:59:59'
    news_collection.get_records_by_date(search_date_from, search_date_to)
else:
    print('Не корректный ввод!')

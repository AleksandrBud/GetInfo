from bs4 import BeautifulSoup
import requests
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import json

def get_profile():
    profile = webdriver.FirefoxProfile()
#    profile.set_preference("browser.autostart", True)
    profile.set_preference("browser.privatebrowsing.autostart", True)
    return profile


def get_page_html(link):
    html = requests.get(link).text
    return BeautifulSoup(html, 'lxml')


main_link = 'https://www.rbc.ru/'
#Используем драйвер Firefox для имитации работы пользователя в браузере
driver = webdriver.Firefox(firefox_profile=get_profile())
driver.implicitly_wait(10)
driver.get(main_link)
last_height = driver.execute_script('return document.body.scrollHeight')
#Прокручиваем страницу до конца, для загрузки всех элементов (они подгружаются динамически)
for i in range(10):
    driver.execute_script('window.scrollTo(0,  document.body.scrollHeight);')
    time.sleep(3)
    last_height = driver.execute_script('return document.body.scrollHeight')
html = driver.page_source
driver.quit()
#Начинаем парсить страницу
parsed_html = BeautifulSoup(html, 'lxml')
news_blok = parsed_html.find_all('a', {'class', 'news-feed__item js-news-feed-item js-yandex-counter'})
news = []
for line_news in news_blok:
    new = {'href': line_news['href'],
           'desc': line_news.find('span', {'class': 'news-feed__item__title'}).getText()[2:].strip(),
           'source': 'RBC'}
    news.append(new)

main_link = 'https://bcs-express.ru'
category_input = int(input('Выбириет категорию для БКС:\n 1 - Все\n 2 - Российский рынок\n 3 - Мировой рынок\n 4 - '
                           'Валютный рынок\n 5 - Рынок нефти:\n'))
category_list = {1: '/category', 2: '/category/rossiyskiy-rynok', 3: '/category/mirovye-rynki',
                4: '/category/valyutnyy-rynok', 5: '/category/rynok-nefti'}
category = category_list[category_input]

parsed_html = get_page_html(main_link + category)
#   Получаем id первой новости
first_id_news = parsed_html.find('a', {'class', 'feed-item__favorite tooltip favorite js-favorite'})['data-id']
category_link = category.split('/')[-1]

for i in range(3):
#   Формируем ссылку для доступа к API
    link = f'/webapi/api/news/getlist?after={first_id_news}&rubric={category_link}'
#   Грузим информацию
    data = json.loads(get_page_html(main_link + link).find('p').getText())
    for line_news in data['items']:
        new = {'href': main_link + line_news['hyperLink'],
               'desc': line_news['title'],
               'source': 'BCS'}
        first_id_news = line_news['id'],
        news.append(new)

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(news, f, ensure_ascii=False, indent=4)
#for i in news:
#    pprint(i)

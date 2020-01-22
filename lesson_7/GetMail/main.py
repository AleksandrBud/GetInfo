import con_db
import time
import chardet
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine, and_
from sqlalchemy import Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from selenium.webdriver.firefox.options import Options
from getpass import getpass

class MailDB(declarative_base()):
    __tablename__ = 'mails'
    title = Column(String(200), primary_key=True)
    sender = Column(String(200), primary_key=True)
    date = Column(String(50), primary_key=True)
    mess = Column(Text)

    def __init__(self, title, sender, date, mess):
        self.title = title
        self.sender = sender
        self.date = date
        self.mess = mess


def unique_record(session, mail):
    result = session.query(exists().where(and_(MailDB.title == mail['title'],
                                                    MailDB.sender == mail['sender'],
                                                    MailDB.date == mail['date']))).scalar()
    return result


def new_record(session, element: object) -> object:
    if not unique_record(session, element):
        try:
            mess_bytes = element['mess'].encode()
            code = chardet.detect(mess_bytes)
            if code['encoding'] is not None:
                record = MailDB(element['title'], element['sender'], element['date'], mess_bytes.decode('UTF-8'))
                session.add(record)
                session.commit()
        except Exception as e:
            print('dbError:', element['title'], element['sender'], element['date'], e)
    else:
        print('dublicat value: ', element['title'], element['sender'], element['date'])


def mail_login(driver, login, password):
    element = driver.find_element_by_css_selector('.button2_theme_mail-white')
    element.click()
    driver.implicitly_wait(20)
    element = driver.find_element_by_id('passp-field-login')
    element.send_keys(login)
    element.send_keys(Keys.RETURN)
    driver.implicitly_wait(20)
    element = driver.find_element_by_id('passp-field-passwd')
    element.send_keys(password)
    element.send_keys(Keys.RETURN)
    driver.implicitly_wait(20)
    return driver


brows_options = Options()
brows_options.add_argument('--headless')
driver = webdriver.Firefox(options=brows_options)
driver.implicitly_wait(20)
driver.get('https://mail.yandex.ru/')
login = input('Input login: ')
password = getpass('Input password: ')
driver = mail_login(driver, login, password)
engine = create_engine(con_db.connect_string())
session_maker = sessionmaker(bind=engine)
session = session_maker()
folders = driver.find_elements_by_xpath('//a[contains(@class,"ns-view-folder")]')
for folder in folders:
    try:
        title = folder.get_attribute('title')
        href = folder.get_attribute('href')
        driver.get(href)
        driver.implicitly_wait(20)
        time.sleep(2)
        mails = driver.find_elements_by_xpath('//a[contains(@class, "mail-MessageSnippet")]')
        for mail in mails:
            try:
                mail_href = mail.get_attribute('href')
                driver.get(mail_href)
                driver.implicitly_wait(20)
                sender = driver.find_element_by_xpath('//span[contains(@class, "ns-view-message-head-sender-name")]').get_attribute('title')
                date_mess = driver.find_element_by_xpath('//div[contains(@class, "ns-view-message-head-date")]').text.strip()
                title_mess = driver.find_element_by_xpath('//div[contains(@class,"mail-Message-Toolbar-Subject_message")]').text.strip()
                message = driver.find_element_by_class_name('mail-Message-Body-Content').text
                text_message = message.strip().replace('\n', ' ')
                mess = {'title': title_mess,
                        'sender': sender,
                        'date': date_mess,
                        'mess': text_message}
                new_record(exept, session, mess)
            except Exception as e:
                print(e)
            driver.back()
            driver.implicitly_wait(20)
            time.sleep(2)
    except Exception as e:
        print(e)
driver.quit()
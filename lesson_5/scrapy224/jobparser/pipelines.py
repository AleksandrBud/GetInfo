# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import con_db
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from pymongo import MongoClient


class JobparserPipeline(object):

    def __init__(self):
        engine = create_engine(con_db.connect_string())
        session_maker = sessionmaker(bind=engine)
        self.session = session_maker()

    class VakanciesDB(declarative_base()):
        __tablename__ = 'vakancies'
        href = Column(String(500), primary_key=True)
        name = Column(String(300))
        min_price = Column(Integer)
        max_price = Column(Integer)
        source = Column(String(30))
        currency = Column(String(10))
        descr = Column(String(100))
        def __init__(self, href, name, min_price, max_price, source, currency, descr):
            self.href = href
            self.name = name
            self.min_price = min_price
            self.max_price = max_price
            self.source = source
            self.currency = currency
            self.descr = descr

    def unique_record(self, href):
        result = self.session.query(exists().where(
            self.VakanciesDB.href == href)).scalar()
        return result

    def new_record(self, element: object) -> object:
        if not self.unique_record(element['href']):
            record = self.VakanciesDB(element['href'], element['name'], element['min_price'], element['max_price'],
                                      element['source'], element['currency'], element['descr'])
            self.session.add(record)
            self.session.commit()
        # else:
        #     print(element['date'], element['desc'])

    def process_item(self, item, spider):
        #print(item._values)
        href = ''
        name = ''
        min_price = 0
        max_price = 0
        currency = ''
        desc = ''
        if spider.name == 'hhru':
            href = item._values['href']
            name = item._values['name']
            len_salary = len(item._values['salary'])
            if len_salary > 0:
                if item._values['salary'][0] == 'от':
                    min_price = int(item._values['salary'][1].replace('\xa0', ''))
                    if len_salary > 3:
                        currency = item._values['salary'][3].replace('\xa0', '')
                    if len_salary > 4:
                        desc = item._values['salary'][4].replace('\xa0', '')
                elif item._values['salary'][0] == 'до':
                    max_price = int(item._values['salary'][1].replace('\xa0', ''))
                    if len_salary > 3:
                        currency = item._values['salary'][3].replace('\xa0', '')
                    if len_salary > 4:
                        desc = item._values['salary'][4].replace('\xa0', '')
                else:
                    if len_salary > 2:
                        if item._values['salary'][1] == '-':
                            min_price = int(item._values['salary'][0].replace('\xa0', ''))
                            max_price = int(item._values['salary'][2].replace('\xa0', ''))
                            if len_salary > 4:
                                currency = item._values['salary'][4].replace('\xa0', '')
                            if len_salary > 5:
                                desc = item._values['salary'][5].replace('\xa0', '')
        elif spider.name == 'superjob':
            href = 'https://www.superjob.ru' + item._values['href']
            for word in item._values['name']:
                name = name + word
            len_salary = len(item._values['salary'])
            salary = item._values['salary']
            if len_salary == 1:
                desc = salary[0]
            elif len_salary == 3:
                if salary[2] == 'от':
                    min_price = salary[0].replace('\xa0', '')
                elif salary[2] == 'до':
                    max_price = salary[0].replace('\xa0', '')
                else:
                    min_price = salary[0].replace('\xa0', '')
                    max_price = min_price
                    desc = salary[2]
                currency = salary[1]

            elif len_salary == 7:
                min_price = salary[0].replace('\xa0', '')
                max_price = salary[4].replace('\xa0', '')
                currency = salary[5]
                desc = salary[6]

        rec = {'href': href,
               'name': name,
               'min_price': int(min_price),
               'max_price': int(max_price),
               'source': spider.name,
               'currency': currency,
               'descr': desc}
        self.new_record(rec)
        return item



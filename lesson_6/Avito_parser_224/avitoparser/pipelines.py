# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import con_db
import sqlalchemy
from sqlalchemy import create_engine, and_
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http import HtmlResponse, Response
import scrapy


class AvitoPhotosPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photos']:
            for img in item['photos']:
                try:
                    yield scrapy.Request(img)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        if results:
            item['photos'] = [itm[1] for itm in results if itm[0]]
        return item


class DataBasePipeline(object):
    def __init__(self):
        engine = create_engine(con_db.connect_string())
        session_maker = sessionmaker(bind=engine)
        self.session = session_maker()

    class AdvertisingTable(declarative_base()):
        __tablename__ = 'advertising'
        id = Column(String(40), primary_key=True)
        name = Column(String(200))
        href = Column(String(500))
        price = Column(sqlalchemy.Float)

        def __init__(self, id, name, href, price):
            self.id = id
            self.name = name
            self.href = href
            self.price = price

    class FotoTable(declarative_base()):
        __tablename__ = 'adv_foto'
        adv_id = Column(String(40), primary_key=True)
        name = Column(String(40), primary_key=True)
        href = Column(String(200))
        photo = Column(sqlalchemy.BINARY)

        def __init__(self, adv_id, name, href, photo):
            self.adv_id = adv_id
            self.name = name
            self.href = href
            self.photo = photo

    class ParamsTable(declarative_base()):
        __tablename__ = 'adv_param'
        advid = Column(String(40), primary_key=True)
        param = Column(String(100), primary_key=True)
        value = Column(String(200))

        def __init__(self, adv_id, param, value):
            self.advid = adv_id
            self.param = param
            self.value = value

    def unique_record_adv(self, id_val):
        result = self.session.query(exists().where(self.AdvertisingTable.id == id_val)).scalar()
        return result

    def new_record_adv(self, element: object) -> object:
        if not self.unique_record_adv(element['id']):
            record = self.AdvertisingTable(element['id'], element['name'], element['href'], element['price'])
            self.session.add(record)

    def process_param(self, spider_name, adv_id, param_list):
        if len(param_list) > 0:
            for param_blok in param_list:
                linkR = HtmlResponse(url='url', body=param_blok, encoding='utf-8')
                param = ''
                value = ''
                if spider_name == 'avito':
                    param = linkR.xpath('//text()').extract()[1]
                    value = linkR.xpath('//text()').extract()[2]
                elif spider_name == 'youla':
                    param = linkR.xpath('//text()').extract()[0]
                    value = linkR.xpath('//text()').extract()[1]
                self.new_record_adv_param(adv_id, param, value)

    def process_photo(self, photos):
        for photo in photos:
            if not self.unique_record_adv_photo(photo['id'], photo['name']):
                self.new_record_adv_photo(photo)

    def unique_record_adv_param(self, id_val, param_val):
        result = self.session.query(exists().where(and_(self.ParamsTable.advid == id_val,
                                                   self.ParamsTable.param == param_val))).scalar()
        return result

    def new_record_adv_param(self, adv_id, param, value) -> object:
        if not self.unique_record_adv_param(adv_id, param):
            record = self.ParamsTable(adv_id, param, value)
            self.session.add(record)

    def unique_record_adv_photo(self, adv_id, name):
        result = self.session.query(exists().where(and_(self.FotoTable.adv_id == adv_id,
                                                   self.FotoTable.name == name))).scalar()
        return result

    def new_record_adv_photo(self, element: object) -> object:
        if not self.unique_record_adv_param(element['id'], element['name']):
            record = self.FotoTable(element['id'], element['name'], element['href'], element['photo'])
            self.session.add(record)

    def process_item(self, item, spider):
        id_adv = ''
        name = ''
        href = ''
        # name_photo = ''
        price = 0.0
        # href_photo = ''
        photo: bin()
        photos = []
        if spider.name == 'avito':
            id_adv = item['href'].split('_')[-1]
            name = item['name']
            price = item['price'][0]
            href = item['href']
        elif spider.name == 'youla':
            id_adv = item['href'].split('/')[-2]
            name = item['name']
            price = item['price'][0]
            href = item['href']
        adv = {'id': id_adv,
               'name': name,
               'price': price,
               'href': href}
        for photo_parce in item['photos']:
            name_photo = photo_parce['url'].split('/')[-1].split('.')[0]
            #Связь фотографий с объявлением определяется в БД через id_adv
            href_photo = photo_parce['path']
            path = 'images/' + href_photo
            #Будем хранить дубликат фотографий в БД в бинарном виде
            fle = open(path, 'rb')
            photo = fle.read()
            fle.close()
            adv_photo = {'id': id_adv,
                         'name': name_photo,
                         'href': href_photo,
                         'photo': photo}
            photos.append(adv_photo)
        self.new_record_adv(adv)
        self.process_param(spider.name, id_adv, item['param'])
        self.process_photo(photos)
        self.session.commit()
        return item

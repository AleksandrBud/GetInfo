# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst


def cleaner_photo(value):
    if value[:2] == '//':
        return f'http://{value}'
    return value


def process_price(value):
    return float(value.replace('\u2009', ''))

def process_param(value):
    test = value
    return value

class AvitoparserItem(scrapy.Item):
    # define the fields for your item here like:
    _id = scrapy.Field()
    name = scrapy.Field(output_processor=TakeFirst())
    photos = scrapy.Field(input_processor=MapCompose(cleaner_photo))  #// -> http://
    href = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(input_processor=MapCompose(process_price))
    param = scrapy.Field(input_processor=MapCompose(process_param))


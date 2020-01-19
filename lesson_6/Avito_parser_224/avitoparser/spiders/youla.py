# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from avitoparser.items import AvitoparserItem
from scrapy.loader import ItemLoader


class YoulaSpider(scrapy.Spider):
    name = 'youla'
    allowed_domains = ['youla.ru']
    start_urls = ['https://auto.youla.ru/ufa/cars/']

    def parse(self, response):
        next_page = response.xpath('.//a[@class="Paginator_button__u1e7D ButtonLink_button__1wyWM '
                                   'Button_button__3NYks"]/@href').extract()
       # href = 'https://auto.youla.ru' + next_page[-1]
        yield response.follow(next_page[-1], callback=self.parse)
        ads_links = response.xpath('//a[@class="SerpSnippet_name__3F7Yu SerpSnippet_titleText__1Ex8A blackLink"]/@href').extract()
        for ads in ads_links:
            yield response.follow(ads, callback=self.parse_ads)

    def parse_ads(self, response: HtmlResponse):
        loader = ItemLoader(item=AvitoparserItem(), response=response)
        loader.add_xpath('photos', '//img[@class="PhotoGallery_photoImage__2mHGn"]/@src')
        loader.add_xpath('price', '//div[@class="AdvertCardStickyContacts_toolbar__pMpq1"]/div/text()')
        loader.add_xpath('name', '//div[@class="AdvertCard_advertTitle__1S1Ak"]/text()')
        loader.add_xpath('param', '//div[@class="AdvertSpecs_row__ljPcX"]')
        loader.add_value('href', response.url)
#        photos = response.xpath('price', '//div[@class="AdvertCardStickyContacts_toolbar__pMpq1"]/div/text()')
        yield loader.load_item()

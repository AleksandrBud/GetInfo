# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem


class SuperJobSpider(scrapy.Spider):
    name = 'superjob'
    allowed_domains = ['superjob.ru']
    start_urls = ['https://www.superjob.ru/vacancy/search/?keywords=python&geo%5Bc%5D%5B0%5D=1']

    def parse(self, response: HtmlResponse):
        next_page = response.xpath(
            '//a[@class="icMQ_ _1_Cht _3ze9n f-test-button-dalshe f-test-link-Dalshe"]/@href').extract_first()
        yield response.follow(next_page, callback=self.parse)

        vacansy = response.xpath('//div[@class="_3syPg _3P0J7 _9_FPy"]').extract()

        for link in vacansy:
            linkR = HtmlResponse(url='url', body=link, encoding='utf-8')
            name = linkR.xpath('//div[@class="_3mfro CuJz5 PlM3e _2JVkc _3LJqf"]/text()').extract()
            salary_pref = linkR.xpath(
                '//span[@class="_3mfro _2Wp8I f-test-text-company-item-salary PlM3e _2JVkc _2VHxz"]/text()').extract_first()
            salary = linkR.xpath(
                '//span[@class="_3mfro _2Wp8I f-test-text-company-item-salary PlM3e _2JVkc _2VHxz"]/span/text()').extract()
            salary.append(salary_pref)
            href = linkR.xpath('//div[@class="_3syPg _3P0J7 _9_FPy"]/div/a/@href').extract_first()
            yield JobparserItem(name=name, salary=salary, href=href)

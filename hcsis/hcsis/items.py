# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HcsisItem(scrapy.Item):
    # define the fields for your item here like:
    provider_name = scrapy.Field()
    provider_id = scrapy.Field()
    service_location = scrapy.Field()
    service_location_id = scrapy.Field()
    inspection_id = scrapy.Field()
    inspection_reason = scrapy.Field()
    inspection_date = scrapy.Field()
    inspection_status = scrapy.Field()
    regulation = scrapy.Field()
    non_compliance_area = scrapy.Field()
    correction_required = scrapy.Field()
    plans_of_correction = scrapy.Field()
    correction_date = scrapy.Field()
    poc_status = scrapy.Field()
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InspectionItem(scrapy.Item):
    provider_name = scrapy.Field()
    provider_id = scrapy.Field()
    certified_locations_url = scrapy.Field()
    service_location = scrapy.Field()
    service_location_id = scrapy.Field()

    region = scrapy.Field()
    county = scrapy.Field()
    service_specialty = scrapy.Field()
    address = scrapy.Field()
    first_cert_start_date = scrapy.Field()
    first_cert_end_date = scrapy.Field()
    last_cert_start_date = scrapy.Field()
    last_cert_end_date = scrapy.Field()

    inspections_found = scrapy.Field()
    inspections_page_url = scrapy.Field()
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

class SanctionItem(scrapy.Item):
    provider_name = scrapy.Field()
    provider_id = scrapy.Field()
    certified_locations_url = scrapy.Field()
    service_location = scrapy.Field()
    service_location_id = scrapy.Field()
    sanctions_page_url = scrapy.Field()
    sanctions = scrapy.Field()


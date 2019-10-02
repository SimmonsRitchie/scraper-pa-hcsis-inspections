# -*- coding: utf-8 -*-
import scrapy
from ..items import HcsisItem
import string
import re
from scrapy.http import FormRequest

class InspectionsSpider(scrapy.Spider):
    name = 'inspections'
    start_urls = ['https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders?alphabet=A']
    ALPHABET = re.findall('[B-Z]',string.ascii_uppercase) + ['OTHER']
    page_count = 0
    cert_page_count = 1

    def parse(self, response):

        provider_rows = response.css('blockquote td.BodyText')

        for row in provider_rows:
            item = HcsisItem()
            provider_name = row.css('td a::text').extract_first()
            provider_id = row.css('td a::attr(href)').re_first('\d+$')

            item['provider_name'] = provider_name
            item['provider_id'] = provider_id

            provider_cert_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages" \
                f"/certifiedservicelocationslist.aspx?p_varProvrId={provider_id}"
            if provider_id is not None:
                yield response.follow(provider_cert_page, callback=self.parse_cert_page, meta={'item': item})

        next_page = f'https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders' \
            f'?alphabet={InspectionsSpider.ALPHABET[InspectionsSpider.page_count]}'

        if InspectionsSpider.page_count < 2:
        # if InspectionsSpider.page_count < (len(InspectionsSpider.ALPHABET) - 1):
            InspectionsSpider.page_count += 1
            yield response.follow(next_page, callback=self.parse)

    def parse_cert_page(self,response):
        print(f'~~~~~~~~~ PAGE: {InspectionsSpider.cert_page_count}')

        item = response.meta.get('item')

        location_rows = response.css('td:nth-child(4) a')
        location_rows = [location_row for location_row in location_rows if not location_row.css('::attr('
                                                                                            'href)').re_first(
            'javascript')]
        item['provider_parent_address'] = None

        if location_rows:
            for location in location_rows:
                service_location = location.css('::text').extract_first()
                item['service_location'] = service_location

                yield item

        pagination = response.css('#ctl00_SSDPageContent_grdCertifiedServiceLocations td > table td').css(
            '::text').extract()
        if pagination:
            if InspectionsSpider.cert_page_count != int(pagination[-1]):
                print('~~~~~~ more pages detected... ')
                InspectionsSpider.cert_page_count += 1
                yield FormRequest.from_response(response, formdata={
                    '__EVENTTARGET': 'ctl00$SSDPageContent$grdCertifiedServiceLocations',
                    '__EVENTARGUMENT': f'Page${InspectionsSpider.cert_page_count}',
                }, callback=self.parse)


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

    def parse(self, response):

        provider_rows = response.css('blockquote td.BodyText')

        for count, row in enumerate(provider_rows):
            item = HcsisItem()
            provider_name = row.css('td a::text').extract_first()
            provider_id = row.css('td a::attr(href)').re_first('\d+$')

            item['provider_name'] = provider_name
            item['provider_id'] = provider_id

            provider_cert_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages" \
                f"/certifiedservicelocationslist.aspx?p_varProvrId={provider_id}"
            if provider_id is not None:
                yield response.follow(provider_cert_page, callback=self.parse_cert_page, meta={'item': item,
                                                                                               'cert_page_count': 1})

        next_page = f'https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders' \
            f'?alphabet={InspectionsSpider.ALPHABET[InspectionsSpider.page_count]}'

        # if InspectionsSpider.page_count > 0:
        if InspectionsSpider.page_count < (len(InspectionsSpider.ALPHABET) - 1):
            InspectionsSpider.page_count += 1
            yield response.follow(next_page, callback=self.parse)

    def parse_cert_page(self,response):
        page = response.meta.get('cert_page_count')
        print(f'~~~~~~~~~ PAGE: {page}')
        item = response.meta.get('item')
        location_rows = response.css('td:nth-child(4) a')
        location_rows = [location_row for location_row in location_rows if not location_row.css('::attr('
                                                                                            'href)').re_first(
            'javascript')]
        pagination = response.css('#ctl00_SSDPageContent_grdCertifiedServiceLocations td > table td').css(
            '::text').extract()

        if location_rows:
            for location in location_rows:
                service_location = location.css('::text').extract_first()
                item['service_location'] = service_location
                yield item
        else:
            item['service_location'] = "No certified locations"
            yield item

        if pagination:
            if page != int(pagination[-1]):
                print('~~~~~~ more pages detected... ')
                page += 1
                yield FormRequest.from_response(response, formdata={
                    '__EVENTTARGET': 'ctl00$SSDPageContent$grdCertifiedServiceLocations',
                    '__EVENTARGUMENT': f'Page${page}',
                }, callback=self.parse_cert_page, meta={'item': item, 'cert_page_count': page})


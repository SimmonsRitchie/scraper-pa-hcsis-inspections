# -*- coding: utf-8 -*-
import scrapy
import string
import re
from scrapy.http import FormRequest
from ..items import SanctionItem


class SanctionsSpider(scrapy.Spider):
    name = 'sanctions'
    start_urls = ['https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders?alphabet=A']
    ALPHABET = re.findall('[A-Z]',string.ascii_uppercase) + ['OTHER']
    page_count = 0


    def parse(self, response):

        provider_rows = response.css('blockquote td.BodyText')
        provider_list = [row.css('td a::text').extract_first() for row in provider_rows]

        self.log(f"SCRAPING PROVIDERS THAT START WITH LETTER: {SanctionsSpider.ALPHABET[SanctionsSpider.page_count]}")
        self.log(f"PROVIDER LIST: {provider_list}")
        self.log(f"PROVIDER COUNT: {len(provider_list)}")

        for count, row in enumerate(provider_rows):
            item = SanctionItem()
            provider_name = row.css('td a::text').extract_first()
            provider_id = row.css('td a::attr(href)').re_first('\d+$')

            item['provider_name'] = provider_name
            item['provider_id'] = provider_id

            locations_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/certifiedservicelocationslist.aspx?p_varProvrId={provider_id}"
            item['certified_locations_url'] = locations_page
            self.log(provider_name)
            if provider_id:
                yield response.follow(locations_page, callback=self.parse_locations_page, meta={'item': item.copy(),
                                                                                               'cert_page_count': 1})
            else:
                self.log(f">>>>>>> No provider ID found for provider: {provider_name}, id: {provider_id}")

        if SanctionsSpider.page_count > 20000: # only run one page
        # if SanctionsSpider.page_count < (len(SanctionsSpider.ALPHABET) - 1):
            SanctionsSpider.page_count += 1
            next_page = f'https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders' \
                f'?alphabet={SanctionsSpider.ALPHABET[SanctionsSpider.page_count]}'
            yield response.follow(next_page, callback=self.parse)


    def parse_locations_page(self, response):
        page = response.meta.get('cert_page_count')
        item = response.meta.get('item')
        self.log(f">>>>>>>>>>> PROCESSING PROVIDER: {item['provider_name']}, ID: {item['provider_id']}")
        self.log(f'~~~~~~~~~ PROCESSING CERTIFIED LOCATIONS, PAGE: {page}')
        location_rows = response.css('td:nth-child(4) a')
        location_rows = [location_row for location_row in location_rows if not location_row.css('::attr('
                                                                                            'href)').re_first(
            'javascript')]
        pagination = response.css('#ctl00_SSDPageContent_grdCertifiedServiceLocations td > table td').css(
            '::text').extract()

        if location_rows:
            for location in location_rows:

                service_location = location.css('::text').extract_first()
                service_location_id = location.css('::attr(href)').re_first('\d+$')
                sanction_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/NegativeSanctions.aspx" \
                    f"?p_varProvrId={item['provider_id']}&ServiceLocationID={service_location_id}"
                item['service_location'] = service_location
                item['service_location_id'] = service_location_id
                item['service_location_unique_id'] = f"{item['provider_id']}-{item['service_location_id']}"
                item['sanctions_page_url'] = sanction_page
                if service_location_id:
                    yield response.follow(sanction_page, callback=self.parse_sanction_page,
                                          meta={'item':item.copy()})

        else:
            self.log('~~~~~~~~~~~~~~~~~~~~~~~~')
            self.log(f"No certified locations found for {item['provider_name']} {item['provider_id']}")
            item['service_location'] = "No certified locations"
            list_of_vals = ["service_location_id",
                            "service_location_unique_id",
                            "sanctions"]

            for item_key in list_of_vals:
                item[item_key] = None
            yield item

        if pagination:
            if page != int(pagination[-1]):
                self.log('~~~~~~ more pages detected... ')
                page += 1
                yield FormRequest.from_response(response, formdata={
                    '__EVENTTARGET': 'ctl00$SSDPageContent$grdCertifiedServiceLocations',
                    '__EVENTARGUMENT': f'Page${page}',
                }, callback=self.parse_locations_page, meta={'item': item.copy(), 'cert_page_count': page})


    def parse_sanction_page(self, response):
        item = response.meta.get('item')

        rows = response.css('form div div table#grdNegativeSanctions > tr')

        if rows:
            self.info_service_location(item, "SANCTION DATA FOUND!")
            rows = rows[1:] # remove col headers
            self.info_service_location(item.copy(), f"NUMBER OF ROWS (minus col headers): {len(rows)}")
            self.log(rows.extract())

            for count, row in enumerate(rows):
                self.info_service_location(item, f"Extracting ROW {count}")
                item['sanction_id'] = row.css('td:nth-child(1) span::text').extract_first()
                item['sanction_type'] = row.css('td:nth-child(2) span::text').extract_first()
                item['sanction_issuance_date'] = row.css('td:nth-child(3) span::text').extract_first()
                item['sanction_status'] = row.css('td:nth-child(4) span::text').extract_first()
                yield item
        else:
            self.info_service_location(item, "No sanctions found")
            item['sanction_id'] = None
            item['sanction_type'] = None
            item['sanction_issuance_date'] = None
            item['sanction_status'] = None
            yield item

    def info_service_location(self, item, message=""):
        self.log('~~~~~~~~~~~~~~~~~~~~~~~~~')
        self.log(f"PROV: {item['provider_id']}, {item['service_location']} {item['service_location_id']} | {message}")

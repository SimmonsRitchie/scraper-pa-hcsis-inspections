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
            self.log(provider_name)

            # Some HCSIS providers are 'Supports Coordination Agencies'. These don't appear to have locations that
            # are inspected. We only want to scrape REAL providers
            prov_href = row.css('td a::attr(href)').extract_first()
            provider_type = re.match('.*ServicesSupportDirectory/(?P<provider_type>.*)\?.*',prov_href)
            provider_type = provider_type.group('provider_type')

            if 'ProviderDetails' in provider_type:
                item['provider_name'] = provider_name
                item['provider_id'] = provider_id
                certified_locations_page_url = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/certifiedservicelocationslist.aspx?p_varProvrId={provider_id}"
                item['certified_locations_url'] = certified_locations_page_url

                yield response.follow(certified_locations_page_url, callback=self.parse_locations_page, meta={'item': item.copy(),
                                                                                               'cert_page_count': 1})
            else:
                self.log(f"{provider_name}, id: {provider_id} is not a real provider ('{provider_type}') "
                         f"Not scraping info for this provider. Full URL to this provider's' page: {prov_href}")

        # if SanctionsSpider.page_count > 20000: # only run one page
        if SanctionsSpider.page_count < (len(SanctionsSpider.ALPHABET) - 1):
            SanctionsSpider.page_count += 1
            next_page_url = f'https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders' \
                f'?alphabet={SanctionsSpider.ALPHABET[SanctionsSpider.page_count]}'
            yield response.follow(next_page_url, callback=self.parse)


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
                location_page_url = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/CertificationInformationTabs" \
                    f".aspx" \
                    f"?p_varProvrId={item['provider_id']}&ServiceLocationID={service_location_id}"

                item['service_location'] = service_location
                item['service_location_id'] = service_location_id
                item['service_location_unique_id'] = f"{item['provider_id']}-{item['service_location_id']}"
                item['cert_info_tabs_url'] = \
                    f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/CertificationInformationTabs.aspx" \
                        f"?p_varProvrId={item['provider_id']}&ServiceLocationID={service_location_id}"
                if service_location_id:
                    yield response.follow(location_page_url, callback=self.parse_location_page,
                                          meta={'item':item.copy()})

        else:
            self.log(f"{item['provider_name']} {item['provider_id']}: No certified locations found ")

        if pagination:
            self.log(f"Last page, unclean format: {pagination[-1]}")
            last_page = int(pagination[-1]) if "..." not in pagination[-1] else int(pagination[-2]) + 1
            self.log(f"Last page, clean format: {last_page}")

            if page != last_page:
                self.log('~~~~~~ more pages detected... ')
                page += 1
                yield FormRequest.from_response(response, formdata={
                    '__EVENTTARGET': 'ctl00$SSDPageContent$grdCertifiedServiceLocations',
                    '__EVENTARGUMENT': f'Page${page}',
                }, callback=self.parse_locations_page, meta={'item': item.copy(), 'cert_page_count': page})


    def parse_location_page(self, response):
        item = response.meta.get('item')

        item['region'] = response.css('#ctl00_SSDPageContent_LabelRegion::text').extract_first().replace('Region: ','')
        item['county'] = response.css('#ctl00_SSDPageContent_LabelCouty::text').extract_first().replace('County: ','')
        item['service_specialty'] = response.css('#ctl00_SSDPageContent_LabelSpecialty::text').extract_first().replace(
            'Service Specialty: ','')
        item['address'] = response.css('#ctl00_SSDPageContent_LabelAddress::text').extract_first().replace('Address: '
                                                                                                          '','')
        sanction_page_url = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/NegativeSanctions.aspx" \
            f"?p_varProvrId={item['provider_id']}&ServiceLocationID={item['service_location_id']}"
        item['sanctions_page_url'] = sanction_page_url

        yield response.follow(sanction_page_url, callback=self.parse_sanction_page,
                              meta={'item': item.copy()})


    def parse_sanction_page(self, response):
        item = response.meta.get('item')

        rows = response.css('form div div table#grdNegativeSanctions > tr')

        if rows:
            self.info_service_location(item, "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nSANCTION DATA FOUND!")
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
            self.log(f"{item['service_location']} {item['service_location_unique_id']}: No sanctions found")

    def info_service_location(self, item, message=""):
        self.log('~~~~~~~~~~~~~~~~~~~~~~~~~')
        self.log(f"PROV: {item['provider_id']}, {item['service_location']} {item['service_location_id']} | {message}")

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
        provider_list = [row.css('td a::text').extract_first() for row in provider_rows]
        self.log(f"PROVIDER LIST: {provider_list}")

        for count, row in enumerate(provider_rows):
            # For testing purposes - delete this later
            if count > 16:
                break
            item = HcsisItem()
            provider_name = row.css('td a::text').extract_first()
            provider_id = row.css('td a::attr(href)').re_first('\d+$')

            item['provider_name'] = provider_name
            item['provider_id'] = provider_id

            provider_cert_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/certifiedservicelocationslist.aspx?p_varProvrId={provider_id}"
            if provider_id:
                yield response.follow(provider_cert_page, callback=self.parse_cert_page, meta={'item': item,
                                                                                               'cert_page_count': 1})
            else:
                self.log(f">>>>>>>>>>>> No provider ID found for name: {provider_name}, id: {provider_id}")

        next_page = f'https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders' \
            f'?alphabet={InspectionsSpider.ALPHABET[InspectionsSpider.page_count]}'

        if InspectionsSpider.page_count < 0:
        # if InspectionsSpider.page_count < (len(InspectionsSpider.ALPHABET) - 1):
            InspectionsSpider.page_count += 1
            yield response.follow(next_page, callback=self.parse)

    def parse_cert_page(self,response):
        page = response.meta.get('cert_page_count')
        item = response.meta.get('item')
        self.log(f">>>>>>>>>>> PROCESSING... {item['provider_name']}, ID: {item['provider_id']}")
        self.log(f'~~~~~~~~~ PAGE: {page}')
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
                self.log('~~~~~~~~~~~~~~~~~~~~~~~~~')
                self.log(f"           Processing service location: {service_location} {service_location_id}")
                # item['service_location'] = service_location
                # item['service_location_id'] = service_location_id

                location_inspection_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/Inspections.aspx" \
                    f"?p_varProvrId={item['provider_id']}&ServiceLocationID={service_location_id}"
                if service_location_id:
                    yield response.follow(location_inspection_page, callback=self.parse_inspection_page,
                                          meta={'item':item,
                                                'service_location': service_location,
                                                'service_location_id': service_location_id
                                                })

        else:
            self.log('~~~~~~~~~~~~~~~~~~~~~~~~')
            self.log(f"No certified locations found for {item['provider_name']} {item['provider_id']}")
            item['service_location'] = "No certified locations"
            list_of_vals = ["service_location_id","inspection_id", "inspection_reason", "inspection_date",
                            "inspection_status", "regulation", "non_compliance_area", "correction_required", "plans_of_correction",
                            "correction_date","poc_status"]
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
                }, callback=self.parse_cert_page, meta={'item': item, 'cert_page_count': page})


    def parse_inspection_page(self, response):
        item = response.meta.get('item')

        item['service_location'] = response.meta.get('service_location')
        item['service_location_id'] = response.meta.get('service_location_id')

        rows = response.css('form div div table#grdInspections > tr')
        # self.log(response.css('html').extract())
        if rows:
            rows = rows[1:] # remove col headers
            self.log(f"LENGTH OF ROWS: {len(rows)}")
            for count, row in enumerate(rows):
                self.log(f"ROW {count}")
                self.log(f"Column count: {len(row.css('tr > td').extract())}")
                if row.css('div table'):
                    # if the row is an inspection grid then do nothing because it will have already been saved in
                    # prior loop iteration
                    self.log("Contains inspection grid, moving on...")
                    continue
                else:
                    # Save meta inspection info
                    self.log("Saving inspection meta data...")
                    inspection_id = row.css('td:nth-child(1) span::text').extract_first()
                    inspection_reason = row.css('td:nth-child(2) span::text').extract_first()
                    inspection_date = row.css('td:nth-child(3) span::text').extract_first()
                    inspection_status = row.css('td:nth-child(4) span::text').extract_first()
                    item['inspection_id'] = inspection_id
                    item['inspection_reason'] = inspection_reason
                    item['inspection_date'] = inspection_date
                    item['inspection_status'] = inspection_status
                if count < (len(rows) - 1) and rows[count + 1].css('div table'):
                    self.log("Next row has inspection grid, saving inspection data...")
                    inspection_grid_rows = rows[count + 1].css('div table tr')
                    # loop over all rows except col headers
                    for i_row in inspection_grid_rows[1:]:
                        # save inspection data
                        item['regulation'] = i_row.css('td:nth-child(1)::text').extract_first()
                        item['non_compliance_area'] = i_row.css('td:nth-child(2)::text').extract_first()
                        item['correction_required'] = i_row.css('td:nth-child(3)::text').extract_first()
                        item['plans_of_correction'] = i_row.css('td:nth-child(4)::text').extract_first()
                        item['correction_date'] = i_row.css('td:nth-child(5) span::text').extract_first()
                        item['poc_status'] = i_row.css('td:nth-child(6)::text').extract_first()
                        yield item
                else:
                    self.log("Next row has no inspection grid...")

                    item['regulation'] = None
                    item['non_compliance_area'] = None
                    item['correction_required'] = None
                    item['plans_of_correction'] = None
                    item['correction_date'] = None
                    item['poc_status'] = None
                    yield item
        else:
            self.log("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            self.log("~~~~~~~~ NO ROWS FOUND! ~~~~~~")
            self.log("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")



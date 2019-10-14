# -*- coding: utf-8 -*-
import scrapy
from ..items import InspectionItem

import string
import re
from scrapy.http import FormRequest

class InspectionsSpider(scrapy.Spider):
    name = 'inspections'
    start_urls = ['https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders?alphabet=A']
    ALPHABET = re.findall('[A-Z]',string.ascii_uppercase) + ['OTHER']
    page_count = 0

    def parse(self, response):

        provider_rows = response.css('blockquote td.BodyText')
        provider_list = [row.css('td a::text').extract_first() for row in provider_rows]

        self.log(f"SCRAPING PROVIDERS THAT START WITH LETTER: {InspectionsSpider.ALPHABET[InspectionsSpider.page_count]}")
        self.log(f"PROVIDER LIST: {provider_list}")
        self.log(f"PROVIDER COUNT: {len(provider_list)}")

        for count, row in enumerate(provider_rows):
            # if count > 10:
            #     break
            item = InspectionItem()
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

        # if InspectionsSpider.page_count < 2: # only run one page
        if InspectionsSpider.page_count < (len(InspectionsSpider.ALPHABET) - 1):
            InspectionsSpider.page_count += 1
            next_page = f'https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders' \
                f'?alphabet={InspectionsSpider.ALPHABET[InspectionsSpider.page_count]}'
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
                location_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/CertificationInformationTabs" \
                    f".aspx" \
                    f"?p_varProvrId={item['provider_id']}&ServiceLocationID={service_location_id}"

                item['service_location'] = service_location
                item['service_location_id'] = service_location_id
                if service_location_id:
                    yield response.follow(location_page, callback=self.parse_location_page,
                                          meta={'item':item.copy()})

        else:
            self.log('~~~~~~~~~~~~~~~~~~~~~~~~')
            self.log(f"No certified locations found for {item['provider_name']} {item['provider_id']}")
            item['service_location'] = "No certified locations"
            list_of_vals = ["service_location_id",
                            "region",
                            "county",
                            "service_specialty",
                            "address",
                            "first_cert_start_date",
                            "first_cert_end_date",
                            "last_cert_start_date",
                            "last_cert_end_date",
                            "inspections_found",
                            "inspections_page_url",
                            "inspection_id",
                            "inspection_reason",
                            "inspection_date",
                            "inspection_status",
                            "regulation",
                            "non_compliance_area",
                            "correction_required",
                            "plans_of_correction",
                            "correction_date",
                            "poc_status"]
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


    def parse_location_page(self,response):
        item = response.meta.get('item')

        item['region'] = response.css('#ctl00_SSDPageContent_LabelRegion::text').extract_first().replace('Region: ','')
        item['county'] = response.css('#ctl00_SSDPageContent_LabelCouty::text').extract_first().replace('County: ','')
        item['service_specialty'] = response.css('#ctl00_SSDPageContent_LabelSpecialty::text').extract_first().replace(
            'Service Specialty: ','')
        item['address'] = response.css('#ctl00_SSDPageContent_LabelAddress::text').extract_first().replace('Address: '
                                                                                                          '','')

        certificate_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/CertificateHistory.aspx" \
            f"?p_varProvrId={item['provider_id']}&ServiceLocationID={item['service_location_id']}"

        yield response.follow(certificate_page, callback=self.parse_certificate_page,
                              meta={'item': item.copy()})

    def parse_certificate_page(self,response):
        item = response.meta.get('item')

        first_cert_start_date = response.css('div > div > table > tr:nth-child(2) > td:nth-child(3) > span::text').extract_first()
        first_cert_end_date = response.css('div > div > table > tr:nth-child(2) > td:nth-child(4) > '
                                           'span::text').extract_first()
        last_cert_start_date = response.css('div > div > table > tr:nth-last-child(1) > td:nth-child(3) > '
                                        'span::text').extract_first()
        last_cert_end_date = response.css('div > div > table > tr:nth-last-child(1) > td:nth-child(4) > '
                                        'span::text').extract_first()
        item['first_cert_start_date'] = first_cert_start_date
        item['first_cert_end_date'] = first_cert_end_date
        item['last_cert_start_date'] = last_cert_start_date
        item['last_cert_end_date'] = last_cert_end_date

        inspection_page = f"https://www.hcsis.state.pa.us/hcsis-ssd/ssd/odp/pages/Inspections.aspx" \
            f"?p_varProvrId={item['provider_id']}&ServiceLocationID={item['service_location_id']}"
        item['inspections_page_url'] = inspection_page

        yield response.follow(inspection_page, callback=self.parse_inspection_page,
                              meta={'item': item.copy()})

    def parse_inspection_page(self, response):
        item = response.meta.get('item')

        rows = response.css('form div div table#grdInspections > tr')

        if rows:
            rows = rows[1:] # remove col headers
            self.info_service_location(item.copy(), f"NUMBER OF ROWS (minus col headers): {len(rows)}")
            self.log(rows.extract())
            # We loop through each row of inspection info. Each row is one of two types: a row with metadata about an
            # inspection (eg. date, type of inspection, etc.) or a row that contains a grid with a list of violations.
            # An inspection grid row is always associated with the metadata row immediately preceding it. Not all
            # metadata rows are followed by inspection grids.
            for count, row in enumerate(rows):

                self.info_service_location(item.copy(), f"ROW {count}")
                self.info_service_location(item.copy(), f"Column count: {len(row.css('tr > td').extract())}")
                if row.css('div table'):
                    # if the row is an inspection grid then go to next loop iteration because it will have already been
                    # saved in prior loop iteration
                    self.log("Contains inspection grid, moving on...")
                    continue
                else:
                    # Since this row is not an inspection grid it must contain meta data about the inspection. We
                    # save it in item.
                    self.info_service_location(item.copy(),"Saving inspection meta data...")
                    inspection_id = row.css('td:nth-child(1) span::text').extract_first()
                    inspection_reason = row.css('td:nth-child(2) span::text').extract_first()
                    inspection_date = row.css('td:nth-child(3) span::text').extract_first()
                    inspection_status = row.css('td:nth-child(4) span::text').extract_first()
                    item['inspections_found'] = True
                    item['inspection_id'] = inspection_id
                    item['inspection_reason'] = inspection_reason
                    item['inspection_date'] = inspection_date
                    item['inspection_status'] = inspection_status
                    self.info_service_location(item.copy(), f"INSPECTION ID: {item['inspection_id']}")

                if count < (len(rows) - 1) and rows[count + 1].css('div table'):
                    # The next row has an inspection grid, we save info about each violation in the grid.
                    self.info_service_location(item.copy(),"Next row has inspection grid, saving violation data...")
                    inspection_grid_rows = rows[count + 1].css('div table tr')
                    # loop over all rows (except col headers) and save data
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
                    # the next row has no inspection grid because it is either the last two in the table or it
                    # doesn't contain a table element.
                    self.info_service_location(item.copy(),"Next row has no inspection grid...")
                    set_to_none = ['regulation',
                                   'non_compliance_area',
                                   'correction_required',
                                   'plans_of_correction',
                                   'correction_date',
                                   'poc_status']
                    for field in set_to_none:
                        item[field] = None
                    yield item


        else:
            self.info_service_location(item.copy(), "NO INSPECTIONS FOUND")
            item['inspections_found'] = False
            set_to_none = ['inspection_id',
                           'inspection_reason',
                           'inspection_date',
                           'inspection_status',
                           'regulation',
                           'non_compliance_area',
                           'correction_required',
                           'plans_of_correction',
                           'correction_date',
                           'poc_status']
            for field in set_to_none:
                item[field] = None
            yield item

    def info_service_location(self, item, message=""):
        self.log('~~~~~~~~~~~~~~~~~~~~~~~~~')
        self.log(f"PROV: {item['provider_id']}, {item['service_location']} {item['service_location_id']} | {message}")


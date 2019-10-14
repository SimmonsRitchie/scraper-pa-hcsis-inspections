# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3

class HcsisPipeline(object):
    def __init__(self):
        self.create_connection()
        self.create_table()

    def create_connection(self):
        self.conn = sqlite3.connect('hcsis.db')
        self.curr = self.conn.cursor()

    def create_table(self):
        self.curr.execute("""DROP TABLE IF EXISTS inspections_tb""")
        self.curr.execute("""create table inspections_tb(
            provider_name text,
            provider_id text,
            certified_locations_url text,
            service_location text,
            service_location_id text,
            service_location_unique_id text,
            
            region text,
            county text,
            service_specialty text,
            address text,
            first_cert_start_date text,
            
            first_cert_end_date text,
            last_cert_start_date text,
            last_cert_end_date text,
            inspections_page_url text,
            inspections_found text,
            
            inspection_id text,
            inspection_reason text,
            inspection_date text,
            inspection_status text,
            regulation text,
            
            non_compliance_area text,
            correction_required text,
            plans_of_correction text,
            correction_date text,
            poc_status text
            )""")

    def process_item(self, item, spider):
        self.store_db(item)
        return item

    def store_db(self, item):
        self.curr.execute("""insert into inspections_tb values (
        ?,?,?,?,?,
        ?,?,?,?,?,
        ?,?,?,?,?,
        ?,?,?,?,?,
        ?,?,?,?,?,
        ?
        )""", (
            item['provider_name'],
            item['provider_id'],
            item['certified_locations_url'],
            item['service_location'],
            item['service_location_id'],
            item['service_location_unique_id'],

            item['region'],
            item['county'],
            item['service_specialty'],
            item['address'],
            item['first_cert_start_date'],

            item['first_cert_end_date'],
            item['last_cert_start_date'],
            item['last_cert_end_date'],
            item['inspections_page_url'],
            item['inspections_found'],

            item['inspection_id'],
            item['inspection_reason'],
            item['inspection_date'],
            item['inspection_status'],
            item['regulation'],

            item['non_compliance_area'],
            item['correction_required'],
            item['plans_of_correction'],
            item['correction_date'],
            item['poc_status']
                )
            )
        self.conn.commit()

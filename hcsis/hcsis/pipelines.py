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
            service_location text,
            service_location_id text
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
        self.curr.execute("""insert into inspections_tb values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            item['provider_name'],
            item['provider_id'],
            item['service_location'],
            item['service_location_id'],
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

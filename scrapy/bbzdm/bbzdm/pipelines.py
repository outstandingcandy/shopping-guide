# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import log
import json
import sqlite3
import md5

class SmzdmPipeline(object):
    
    def __init__(self):
        webpage_database_path = "../../../data/smzdm"
        self.webpage_database_name = webpage_database_path.split("/")[-1]
        self.conn = sqlite3.connect(webpage_database_path)
        self.c = self.conn.cursor()
        # Drop table
        # self.c.execute("DROP TABLE %s" % (self.webpage_database_name))
        # Create table
        self.c.execute('''CREATE TABLE IF NOT EXISTS %s (url text unique, json text)''' % (self.webpage_database_name))
        self.conn.commit()
        self.json_file = open("../../../data/smzdm.json", "w")

    def process_item(self, item, spider):
        log.msg(item.__class__.__name__)
        line = json.dumps(dict(item)) + "\n"
        self.json_file.write(line)
        self.c.execute("INSERT OR REPLACE INTO %s (url, json) VALUES(?, ?)" % self.webpage_database_name, (item["url"], json.dumps(dict(item))))
        self.conn.commit()
        return item
        # img_md5_list = ""
        # for img_url in item["image_urls"]:
        #     img_md5_list += md5.new(img_url).hexdigest() + "\t"
        # img_md5_list= img_md5_list.strip()
        # if item.__class__.__name__ == "SmzdmItem":
        #     log.msg("Smzdm Item pipeline dbg: [%s] [%s] [%s] [%s] [%s]" % (item["title"], item["price"], item["url"], item["description"], item["image_urls"]) , level=log.INFO, spider=spider)
        #     log.msg("Smzdm Item pipeline: %s" % (line) , level=log.INFO, spider=spider)
        #     self.c.execute("INSERT OR REPLACE INTO %s (url, title, description, price, img_md5_list)\
        #     VALUES(?, ?, ?, ?, ?)" % self.webpage_database_name, (item['url'], item['title'], item['description'], item["price"], img_md5_list))
        #     self.conn.commit()
        #     return item
        # elif item.__class__.__name__ == "ShoppingItem":
        #     log.msg("Shopping Item pipeline dbg: [%s] [%s] [%s] [%s] [%s] [%s]" % (item["title"], item["price"], item["url"], item["description"], item["image_urls"], item["referer"]) , level=log.INFO, spider=spider)
        #     log.msg("Shopping Item pipeline: %s" % (line) , level=log.INFO, spider=spider)
        #     self.c.execute("INSERT OR REPLACE INTO %s (url, title, description, price, referer, img_md5_list)\
        #     VALUES(?, ?, ?, ?, ?, ?)" % self.webpage_database_name, (item['url'], item['title'], item['description'], item["price"], item["referer"], img_md5_list))
        #     self.conn.commit()
        #     return item


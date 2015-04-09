#!/usr/bin/python
#-*- coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../../jieba/')

import sqlite3
import jieba
import jieba.analyse
import Orange
from urlparse import urlparse

class ItemLabelCluster(object):
    """ Item Cluster
    """
    def __init__(self, webpage_database_path, item_database_path):
        self.item_list = []
        self.webpage_database_conn = sqlite3.connect(webpage_database_path)
        self.webpage_database_c = self.webpage_database_conn.cursor()
        self.webpage_database_name = webpage_database_path.split("/")[-1]
        self.item_database_conn = sqlite3.connect(item_database_path)
        self.item_database_c = self.item_database_conn.cursor()
        self.item_database_name = item_database_path.split("/")[-1]

        self.item_database_c.execute('CREATE TABLE IF NOT EXISTS %s (item_name unique, \
                                            jd_url text, jd_title text, jd_description text, jd_price float, jd_score float, \
                                            amazon_cn_url text, amazon_cn_title text, amazon_cn_description text, amazon_cn_price float, amazon_cn_score float, \
                                            amazon_com_url text, amazon_com_title text, amazon_com_description text, amazon_com_price float, amazon_com_score float, \
                                            amazon_jp_url text, amazon_jp_title text, amazon_jp_description text, amazon_jp_price float, amazon_jp_score float, \
                                            smzdm_url text, smzdm_title text, smzdm_description text, smzdm_price float, smzdm_score float)' % (self.item_database_name))
        self.item_database_conn.commit()
        for row in self.webpage_database_c.execute('SELECT url, title, description, recommanded_price, shopping_price, item_name, score FROM %s ORDER BY recommanded_price' % (self.webpage_database_name)):
            url = row[0]
            title = row[1]
            description = row[2]
            recommanded_price = row[3]
            shopping_price = row[4]
            if not shopping_price:
                shopping_price = '0'
            item_name = row[5]
            score = row[6]
            if not score:
                score = '0'
            print item_name
            domain = urlparse(url).hostname
            if domain == 'item.jd.com':
                self.insert_item('jd', item_name, url, title, description, shopping_price, score)
            elif domain == 'www.amazon.cn':
                self.insert_item('amazon_cn', item_name, url, title, description, shopping_price, score)
            elif domain == 'www.amazon.com':
                self.insert_item('amazon_com', item_name, url, title, description, shopping_price, score)
            elif domain == 'www.amazon.co.jp':
                self.insert_item('amazon_jp', item_name, url, title, description, shopping_price, score)
            elif domain == 'haitao.smzdm.com':
                self.insert_item('smzdm', item_name, url, title, description, shopping_price, score)
        self.item_database_conn.commit()
        
    def insert_item(self, site_name, item_name, url, title, description, price, score):
        self.item_database_c.execute("INSERT OR IGNORE INTO %s (item_name, %s_url, %s_title, %s_description, %s_price, %s_score) \
                VALUES(?, ?, ?, ?, ?, ?)" % (self.item_database_name, site_name, site_name, site_name, site_name, site_name), \
                (item_name, url, title, description, price, score))
        self.item_database_c.execute('UPDATE %s SET %s_url="%s", %s_title="%s", %s_description="%s", %s_price=%s, %s_score=%s WHERE item_name="%s"' \
                                     % (self.item_database_name, site_name, url, site_name, title, site_name, description, site_name, price, site_name, score, item_name))

if __name__ == '__main__':
    item_cluster = ItemLabelCluster('../../data/webpage', '../../data/item')
    

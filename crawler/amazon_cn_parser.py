#!/usr/bin/python
#-*- coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../beautifulsoup4-4.3.2')
sys.path.append('../util')
sys.path.append('../selenium-2.44.0/py')
sys.path.append('../python-gflags-2.0')
sys.path.append('.')

import re
import os
import urllib
import sqlite3
import md5

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urlparse import urlparse

import shopping_page_parser

class AmazonCnParser(object):
    """ Html Parser for amazon.cn

    Attributes:
    """

    def __init__(self, webpage_database):
        """Inits SmzdmParser"""
        self.list_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.list_page_driver.set_page_load_timeout(10) # seconds
        self.shopping_page_parser = shopping_page_parser.ShoppingPageParser(sys.argv[1])
        self.webpage_database = webpage_database
        self.conn = sqlite3.connect(self.webpage_database)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS %s
                               (url text unique, title text, description text, recommanded_price float, shopping_price float, shopping_url text)''' % (self.webpage_database))
        self.conn.commit()

    def __del__(self):
        self.list_page_driver.quit()

    def parse_list_page(self, url):
        try:
            self.list_page_driver.get(url)
        except:
            pass
        # self.list_page_wait.until(lambda list_page_driver : list_page_driver.find_elements_by_class_name("listTitle"))
        for div_elem in \
                self.list_page_driver.find_elements_by_xpath('//div[@class="zg_itemRow"]'):
            shopping_url = div_elem.find_element_by_class_name('zg_title').\
                    find_element_by_tag_name('a').get_attribute('href')
            print shopping_url
            self.shopping_page_parser.parse_shopping_page(shopping_url)
            data = self.shopping_page_parser.data
            self.c.execute("INSERT OR IGNORE INTO %s (url, title, description, shopping_price, shopping_url )\
                    VALUES ('%s', '%s', '%s', %f, '%s')" %
                    (self.webpage_database, data['url'], data['title'].encode('utf-8'), \
                        data['description'].encode('utf-8'), data['price'], data['url']))
            item_id = md5.new(data['url']).hexdigest()
            if not os.path.exists(item_id):
                os.mkdir(item_id)
            for img_index in range(len(data['img_src_list'])):
                print data['img_src_list'][img_index]
                urllib.urlretrieve(data['img_src_list'][img_index], "%s/%s/%d.jpg" % \
                        (os.getcwd(), item_id, img_index))

if __name__ == '__main__':
    amazon_cn_parser = AmazonCnParser('webpage')
    for page_num in range(1, 2):
        amazon_cn_parser.parse_list_page('http://www.amazon.cn/gp/bestsellers/baby/291444071/#%d' % page_num)

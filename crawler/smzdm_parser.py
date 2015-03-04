#!/usr/bin/python
#-*- coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../../selenium/py')
sys.path.append('../../python-gflags')
sys.path.append('.')

import re
import shopping_page_parser
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urlparse import urlparse
import urllib
import sqlite3
import md5
import ConfigParser

class url_is_from_shopping_site(object):
    def __init__(self, shopping_url_pattern_list):
        self.shopping_url_pattern_list = shopping_url_pattern_list

    def __call__(self, driver):
        for shopping_url_pattern in self.shopping_url_pattern_list:
            if shopping_url_pattern.match(driver.current_url):
                return True
        return False

class SmzdmParser(object):
    """ Html Parser for smzdm.com

    Attributes:
    """

    redundent_term = set([
      ]);

    def __init__(self, config_file_name):
        """Inits SmzdmParser"""
        config = ConfigParser.RawConfigParser()
        config.read(config_file_name)
        
        self.price_pattern = re.compile(config.get("item_page", "price_pattern"))
        self.head_separator = config.get("item_page", "head_separator_pattern").decode("gbk")
        self.attachment_pattern = re.compile(config.get("item_page", "attachment_pattern"))
        
        self.list_page_driver = webdriver.Chrome(config.get("webdriver", "path"))
        self.item_page_driver = webdriver.Chrome(config.get("webdriver", "path"))
        self.shopping_page_driver = webdriver.Chrome(config.get("webdriver", "path"))
        self.middle_page_driver = webdriver.Chrome(config.get("webdriver", "path"))
        # self.list_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        # self.item_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        # self.shopping_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        # self.middle_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.list_page_driver.set_page_load_timeout(10) # seconds
        self.item_page_driver.set_page_load_timeout(10) # seconds
        self.shopping_page_driver.set_page_load_timeout(10) # seconds
        self.middle_page_driver.set_page_load_timeout(10) # seconds

        self.data = {}
        self.shopping_page_parser = shopping_page_parser.ShoppingPageParser(config.get("shopping_page", "shopping_page_config_file_name"))
        self.txt_file = open(config.get("debug", "txt_file_name"), "w")
        
        self.img_path = config.get("img", "path")

        webpage_database_path = config.get("database", "path")
        self.conn = sqlite3.connect(webpage_database_path)
        self.webpage_database_name = webpage_database_path.split("/")[-1]
        self.c = self.conn.cursor()
        # Drop table
        # self.c.execute("DROP TABLE %s" % (self.webpage_database))
        # Create table
        self.c.execute('''CREATE TABLE IF NOT EXISTS %s (url text unique, title text, description text, recommanded_price float, shopping_price float, shopping_url text)''' % (self.webpage_database_name))
        self.conn.commit()

    def __del__(self):
        self.list_page_driver.close()
        self.item_page_driver.close()
        self.middle_page_driver.close()
        self.shopping_page_driver.close()
        self.conn.close()

    def parse_list_page(self, url):
        sys.stderr.write('get %s\n' % url)
        try:
            self.list_page_driver.get(url)
        except:
            pass
        sys.stderr.write('get url finished\n')
        # self.list_page_wait.until(lambda list_page_driver : list_page_driver.find_elements_by_class_name("listTitle"))
        for div_elem in self.list_page_driver.find_elements_by_class_name("listTitle"):
            a_elem = div_elem.find_element_by_tag_name('h3').find_element_by_tag_name('a')
            url = a_elem.get_attribute('href')
            self.parse_item_page(url)
            
    def download_imgs(self, url, img_src_list):
        print url
        item_id = md5.new(url).hexdigest()
        img_path = "%s/%s" % (self.img_path, item_id)
        if not os.path.exists(img_path):
            os.mkdir(img_path)
        for img_count in range(len(img_src_list)):
            try:
                urllib.urlretrieve(img_src_list[img_count], "%s/%d.jpg" % \
                            (img_path, img_count))
            except:
                sys.stderr.write('[WARNING] Description image download failed in this item page: %s\n' % (url))
                pass

    def parse_item_page(self, url):

        try:
            self.item_page_driver.get(url)
        except:
            pass
        try:
            title = WebDriverWait(self.item_page_driver, \
                    10).until(EC.presence_of_element_located((By.XPATH, \
                        '/html/body/section/div[1]/article/h1'))).text
        except:
            sys.stderr.write('[ERROR] No title in this item page: %s\n' % (url))
            return              
        (item_name, price) = self.parse_title(title)
        
        try:
            item_description_list = WebDriverWait(self.item_page_driver, \
                    20).until(EC.presence_of_all_elements_located((By.XPATH, \
                        '/html/body/section/div[1]/article/div[2]/p[@itemprop="description"]')))
        except:
            sys.stderr.write('[ERROR] Description is not found in this item page: %s\n' % (url))
            return
        
        try:
            item_shopping_url = WebDriverWait(self.item_page_driver,
                    20).until(EC.presence_of_element_located((By.XPATH, \
                        '/html/body/section/div[1]/article/div[2]/div/div/a'))).get_attribute('href')
        except:
            sys.stderr.write('[ERROR] No shopping url in this item page: %s\n' % (url))
            return
        
        img_src_list = []
        for description in item_description_list:
            try:
                img_element = description.find_element_by_tag_name('img')
                img_src_list.append(img_element.get_attribute('src'));
            except:
                pass
            
        self.download_imgs(url, img_src_list)
        
        item_description = ''    
        for description in item_description_list:
            try:
                item_description += description.text
            except:
                sys.stderr.write('[ERROR] Description text is not found in this item page: %s\n' % (url))
        print item_name, price, item_description
        self.c.execute("INSERT OR IGNORE INTO %s (url, title, description, recommanded_price, shopping_url )\
                VALUES ('%s', '%s', '%s', %f, '%s')" %
                (self.webpage_database_name, url, item_name.encode('utf-8'), \
                    item_description.encode('utf-8'), price, item_shopping_url))

        data = self.parse_shopping_page(item_shopping_url)
        if not data:
            sys.stderr.write('[ERROR] No shopping data in this shopping url: %s\n' % (item_shopping_url))
            return
        self.txt_file.write('%s\t%f\t%s\t%s\t%f\n' % (data['title'], data['price'], \
            data['description'], data['url'], data['price']))
        
        self.download_imgs(data['url'], data['img_src_list'])
        
        self.c.execute("INSERT OR IGNORE INTO %s (url, title, description, recommanded_price, shopping_price, shopping_url )\
                VALUES ('%s', '%s', '%s', %f, %f, '%s')" %
                (self.webpage_database_name, data['url'], data['title'].encode('utf-8'), \
                    data['description'].encode('utf-8'), price, data['price'], data['url']))
        self.conn.commit()

    def parse_middle_page(self, url):
        o = urlparse(url)
        if o.hostname == 're.jd.com':
            try:
                jump_url = self.shopping_page_driver.find_element_by_xpath("/html/body/div[@class='land_center w clearfix']/div[@class='land_center_bd']/div[@class='land_cen_l']/div[@class='land_a clearfix']/div[@class='land_a_r_l']/div[@class='l_info_b']/a").get_attribute('href')
            except:
                sys.stderr.write('parse jump_url error in middle page: %s\n' % url)
            try:
                self.middle_page_driver.get(jump_url)
            except:
                pass
            real_url = self.middle_page_driver.current_url
            try:
                self.middle_page_driver.get(real_url)
            except:
                pass
            '''
            divs = self.middle_page_driver.find_elements_by_xpath("/html/body//div[@class='w']")
            price = ''
            for div in divs:
                try:
                    price = div.find_element_by_xpath("div[@id='product-intro']/div[@class='clearfix']/ul[@id='summary']/li[@id='summary-price']/div[@class='dd']").text
                except:
                    continue
                else:
                    break
            '''
            price = self.middle_page_driver.find_element_by_id('jd-price').text
            return price

    def parse_shopping_page(self, url):
        try:
            self.shopping_page_driver.get(url)
        except:
            pass
        try:
            WebDriverWait(self.shopping_page_driver, 10) \
                    .until(url_is_from_shopping_site(self.shopping_page_parser.url_pattern_list))
        except:
            sys.stderr.write('[ERROR] Is not shopping page: %s\n' %
                    self.shopping_page_driver.current_url)
        url = self.shopping_page_driver.current_url
        o = urlparse(url)
        if o.hostname == 're.jd.com':
            try:
                jump_url = WebDriverWait(self.shopping_page_driver, 10) \
                        .until(EC.presence_of_element_located((By.XPATH, \
                        '/html/body/div[5]/div/div/div[1]/div[2]/div[3]/a'))).get_attribute('href')
                self.shopping_page_driver.get(jump_url)
                WebDriverWait(self.shopping_page_driver, 10) \
                        .until(url_is_from_shopping_site(self.shopping_page_parser.url_pattern_list))
                url = self.shopping_page_driver.current_url
                print url
            except:
                sys.stderr.write('parse jump_url error in middle page: %s\n' % url)
        self.shopping_page_parser.parse_shopping_page(url)
        return self.shopping_page_parser.data

    def parse_title(self, title):
        item_name = ''
        price = 0.0
        title.decode('utf-8')
        head_end_pos = title.find(self.head_separator)
        if head_end_pos != -1:
            title = title[head_end_pos+1:]
        tokens = title.split(' ')
        for token in tokens:
            attachment_match = self.attachment_pattern.match(token)
            if attachment_match:
                continue
            price_match = self.price_pattern.match(token)
            if price_match:
                price = float(price_match.group(1))
                continue
            item_name += token + ' '
        return (item_name.strip(), price)


if __name__ == '__main__':
    '''
    smzdm_parser = SmzdmParser()
    html_code = open(sys.argv[1]).read()
    soup = BeautifulSoup(html_code)
    for div in soup.findAll('div', class_='listTitle'):
        url = div.h3.a.get('href')
        (item_name, price) = smzdm_parser.parse_title(div.h3.a.text)
        sys.stderr.write('%s\t%s\t%f\n' % (url, item_name, price))
        smzdm_parser.parse_item_page(url)
    '''
    smzdm_parser = SmzdmParser("../configure/smzdm.ini")
    for page_num in range(2, 13):
        smzdm_parser.parse_list_page('http://www.smzdm.com/fenlei/yingertuiche/haitao/p%d' % page_num)

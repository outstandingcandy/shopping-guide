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

    def __init__(self, webpage_database, txt_file_name):
        """Inits SmzdmParser"""
        self.price_pattern = re.compile(u'((?:\d+|\d+\.\d+))元(?:包邮)?.+')
        self.head_separator = '：'.decode('utf-8')
        self.attachment_pattern = re.compile(u'\(.+\)')
        # self.list_page_driver = webdriver.Chrome()
        # self.item_page_driver = webdriver.Chrome('chromedriver')
        # self.list_page_driver = webdriver.Firefox()
        # self.list_page_wait = ui.WebDriverWait(self.list_page_driver, 2)
        # self.item_page_driver = webdriver.Firefox()
        # self.item_page_wait = ui.WebDriverWait(self.item_page_driver, 10)
        # self.middle_page_driver = webdriver.Firefox()
        self.list_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.list_page_driver.set_page_load_timeout(10) # seconds
        self.item_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.item_page_driver.set_page_load_timeout(10) # seconds
        self.shopping_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.middle_page_driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.middle_page_driver.set_page_load_timeout(10) # seconds
        self.data = {}
        self.shopping_page_parser = shopping_page_parser.ShoppingPageParser(sys.argv[1])

        self.txt_file = open(txt_file_name, 'w')

        self.webpage_database = webpage_database
        self.conn = sqlite3.connect(self.webpage_database)
        self.c = self.conn.cursor()
        # Drop table
        # self.c.execute("DROP TABLE %s" % (self.webpage_database))
        # Create table
        self.c.execute('''CREATE TABLE IF NOT EXISTS %s
                               (url text unique, title text, description text, recommanded_price float, shopping_price float, shopping_url text)''' % (self.webpage_database))
        self.conn.commit()

    def __del__(self):
        self.list_page_driver.quit()
        self.item_page_driver.quit()
        self.middle_page_driver.quit()
        self.shopping_page_driver.quit()
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

    def parse_item_page(self, url):
        print url
        item_id = md5.new(url).hexdigest()
        if not os.path.exists(item_id):
            os.mkdir(item_id)
        try:
            self.item_page_driver.get(url)
        except:
            pass
        title = WebDriverWait(self.item_page_driver, \
                10).until(EC.presence_of_element_located((By.XPATH, \
                    '/html/body/section/div[1]/article/h1'))).text
        (item_name, price) = self.parse_title(title)
        item_description_list = WebDriverWait(self.item_page_driver, \
                10).until(EC.presence_of_all_elements_located((By.XPATH, \
                    '/html/body/section/div[1]/article/div[2]/p[@itemprop="description"]')))
        item_description = ''
        img_count = 0
        for description in item_description_list:
            try:
                img_element = description.find_element_by_tag_name('img')
                print img_element.get_attribute('src')
                img_count += 1
                urllib.urlretrieve(img_element.get_attribute('src'), "%s/%s/%d.jpg" % \
                        (os.getcwd(), item_id, img_count))
            except:
                pass
            item_description += description.text
        print item_id, item_name, price, item_description
        try:
            item_shopping_url = WebDriverWait(self.item_page_driver,
                    10).until(EC.presence_of_element_located((By.XPATH, \
                        '/html/body/section/div[1]/article/div[2]/div/div/a'))).get_attribute('href')
        except:
            sys.stderr.write('[ERROR] No shopping url in this item page: %s\n' % (url))
            return
        data = self.parse_shopping_page(item_shopping_url)
        if not data:
            sys.stderr.write('[ERROR] No shopping data in this shopping url: %s\n' % (item_shopping_url))
            return
        self.txt_file.write('%s\t%s\t%f\t%s\t%s\t%f\n' % (data['title'], item_id, data['price'], \
            data['description'], data['url'], data['price']))
        item_id = md5.new(data['url']).hexdigest()
        if not os.path.exists(item_id):
            os.mkdir(item_id)
        for img_index in range(len(data['img_src_list'])):
            print data['img_src_list'][img_index]
            urllib.urlretrieve(data['img_src_list'][img_index], "%s/%s/%d.jpg" % \
                    (os.getcwd(), item_id, img_index))
        self.c.execute("INSERT OR IGNORE INTO %s (url, title, description, recommanded_price, shopping_price, shopping_url )\
                VALUES ('%s', '%s', '%s', %f, %f, '%s')" %
                (self.webpage_database, data['url'], data['title'].encode('utf-8'), \
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
        price = -1
        self.shopping_page_driver.get(url)
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
            item_name += token
        return (item_name, price)


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
    smzdm_parser = SmzdmParser('webpage', 'smzdm.txt')
    for page_num in range(2, 13):
        smzdm_parser.parse_list_page('http://www.smzdm.com/fenlei/yingertuiche/youhui/p%d' % page_num)

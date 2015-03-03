#!/usr/bin/python
#-*- coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../../selenium/py')
sys.path.append('../../python-gflags')
sys.path.append('.')

import re
import gflags
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchFrameException
from urlparse import urlparse
import urllib
import time

class element_located_by_xpath_to_be_selected(object):
    def __init__(self, xpath):
        self.xpath = xpath

    def __call__(self, driver):
        return driver.find_element_by_xpath(self.xpath)

class frame_available(object):
    def __init__(self, frame_reference):
        self.frame_reference = frame_reference

    def __call__(self, driver):
        try:
            driver.switch_to.frame(self.frame_reference)
        except NoSuchFrameException:
            return False
        else:
            return True

class ShoppingPageParser(object):
    """ Html Parser for shopping page
    """
    def __init__(self, url_pattern_xpath_mapping_file_name):
        self.__url_pattern_xpath_dict = {}
        self.url_pattern_list = []
        self.data = {}
        for line in open(url_pattern_xpath_mapping_file_name):
            print line
            line = line.strip()
            tokens = line.split('\t')
            if len(tokens) != 6:
                sys.stderr.write('[ERROR] Shopping site data format error in line:\t%s\n' % line)
                continue
            url_pattern = re.compile(tokens[0])
            title_xpath = tokens[1]
            price_xpath = tokens[2]
            price_redudant_pattern = re.compile(tokens[3].decode('utf-8'))
            description_xpath = tokens[4]
            description_img_xpath = tokens[5]
            self.__url_pattern_xpath_dict[url_pattern] = (title_xpath, \
                    price_xpath, price_redudant_pattern, description_xpath, description_img_xpath)
            self.url_pattern_list.append(url_pattern)
        # self.__driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.__driver = webdriver.Chrome('../../chromedriver')

    def __del__(self):
        self.__driver.close()

    def parse_shopping_page(self, url):
        title = ''
        price = -1.0
        description = ''
        img_src_list = []
        # url = urllib.quote(url.encode('utf-8'), ':/?|=#')
        self.__driver.get(url)
        for url_pattern, (title_xpath, price_xpath, price_redudant_pattern, description_xpath, description_img_xpath) in self.__url_pattern_xpath_dict.items():
            if url_pattern.match(url):
                try:
                    title = WebDriverWait(self.__driver, 10) \
                          .until(EC.presence_of_element_located((By.XPATH, title_xpath))).text
                except:
                    sys.stderr.write('[ERROR] Title xpath is not found: %s\n' % url)
                try:
                    price_element = WebDriverWait(self.__driver, 10) \
                          .until(EC.presence_of_element_located((By.XPATH, price_xpath)))
                    price = price_element.text.decode('utf-8')
                    price = price_redudant_pattern.sub('', price)
                    print price
                    try:
                        price = float(price)
                    except:
                        price = -1.0
                        sys.stderr.write('[ERROR] This item is sold out\n')
                except:
                    sys.stderr.write('[ERROR] Price xpath is not found: %s\n' % url)
                if url_pattern.match('http://www.amazon.'):
                    try:
                        print 'switch frame in amazon'
                        WebDriverWait(self.__driver, 10) \
                            .until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="product-description-iframe"]')))
                    except:
                        sys.stderr.write('[ERROR] Frame in Amazon is not found: %s\n' % url)
                try:
                    description_element = WebDriverWait(self.__driver, 10) \
                          .until(EC.presence_of_element_located((By.XPATH, description_xpath)))
                except:
                    sys.stderr.write('[ERROR] Description xpath %s is not found: %s\n' % (description_xpath, url))
                    break
                # self.__driver.execute_script("arguments[0].scrollIntoView(true);", description_element);
                # self.__driver.execute_script("window.scrollTo(0, 10000);")
                try:
                    description_img_elements = WebDriverWait(self.__driver, 10) \
                          .until(EC.presence_of_all_elements_located((By.XPATH, description_img_xpath)))
                except:
                    sys.stderr.write('[ERROR] Description img xpath is not found: %s\n' % url)
                    break
                for img_element in description_img_elements:
                    self.__driver.execute_script("arguments[0].scrollIntoView(true);", img_element);
                    time.sleep(1)
                description_img_elements = WebDriverWait(self.__driver, 10) \
                      .until(EC.presence_of_all_elements_located((By.XPATH, description_img_xpath)))
                for img_element in description_img_elements:
                    img_src_list.append(img_element.get_attribute('src'))
                for element in description_element.find_elements_by_xpath('*'):
                    if element.text.strip():
                        description += element.text.strip() + '\t'
        self.data['title'] = title
        self.data['url'] = url
        self.data['price'] = price
        self.data['description'] = description
        self.data['img_src_list'] = img_src_list

if __name__ == '__main__':
    shopping_page_parser = ShoppingPageParser(sys.argv[1])
    # shopping_page_parser.parse_shopping_page('http://www.amazon.cn/dp/B006FEPBF4?t=joyo01y-23&m=A1AJ19PSB66TGU&tag=joyo01y-23')
    url = 'http://www.amazon.cn/GRACO-%E7%BE%8E%E5%9B%BD%E8%91%9B%E8%8E%B1%E5%A9%B4%E5%84%BF%E6%8E%A8%E8%BD%A66N92CJB3J-%E9%BB%91%E8%89%B2/dp/B006FEPBF4'
    url = 'http://www.amazon.cn/GRACO-美国葛莱婴儿推车6N92CJB3J-黑色/dp/B006FEPBF4'
    shopping_page_parser.parse_shopping_page(url)

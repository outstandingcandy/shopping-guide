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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchFrameException
from urlparse import urlparse
import urllib
import time
import ConfigParser
import socket

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

class vlog(object):
    def __init__(self, log_level):
        self.log_level = log_level

    def output(self, log_level, str):
        if log_level >= self.log_level:
            sys.stderr.write("%s\n" % (str))

class ShoppingPageParser(object):
    """ Html Parser for shopping page
    """
    def __init__(self, config_file_name):
        self.__url_pattern_xpath_dict = {}
        self.url_pattern_list = []
        self.data = {}
        self.vlog = vlog(2)
        
        config = ConfigParser.RawConfigParser()
        config.read(config_file_name)
        
        for section_name in config.sections():
            url_pattern = re.compile(config.get(section_name, "url_pattern").decode('utf8'))
            title_xpath = config.get(section_name, "title_xpath")
            price_xpath = config.get(section_name, "price_xpath")
            price_redudant_pattern = re.compile(config.get(section_name, "price_redudant_pattern").decode('utf8'))
            description_xpath = config.get(section_name, "description_xpath")
            description_img_xpath = config.get(section_name, "description_img_xpath")
            self.__url_pattern_xpath_dict[url_pattern] = (title_xpath, \
                    price_xpath, price_redudant_pattern, description_xpath, description_img_xpath)
            self.url_pattern_list.append(url_pattern)
        # self.__driver = webdriver.PhantomJS(executable_path='../phantomjs/bin/phantomjs')
        self.__driver = webdriver.Chrome('../../chromedriver')
        self.__driver.set_page_load_timeout(10) # seconds
        self.__driver.set_script_timeout(10)

    def __del__(self):
        self.__driver.close()

    def parse_shopping_page(self, url):
        title = ''
        price = -1.0
        description = ''
        img_src_list = []
        # url = urllib.quote(url.encode('utf-8'), ':/?|=#')
        try:
            self.__driver.get(url)
        except:
            pass
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
                    price = price_element.text
                    price = price_redudant_pattern.sub('', price)
                    try:
                        price = float(price)
                    except:
                        price = -1.0
                        sys.stderr.write('[ERROR] This item is sold out\n')
                except:
                    sys.stderr.write('[ERROR] Price xpath is not found: %s\n' % url)
                if url_pattern.match('http://www.amazon.'):
                    try:
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
                
                """ Run func with the given timeout. If func didn't finish running
                    within the timeout, raise TimeLimitExpired
                """
                import threading
                class GetImgSrcThread(threading.Thread):
                    def __init__(self, driver, elements):
                        threading.Thread.__init__(self)
                        self.__driver = driver
                        self.__elements = elements
            
                    def run(self):
                        for element in self.__elements:
                            self.__driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)
            
                it = GetImgSrcThread(self.__driver, description_img_elements)
                it.start()
                it.join(30)
                if it.isAlive():
                    break

#                 for img_element in description_img_elements:
#                     self.__driver.execute_script("arguments[0].scrollIntoView(true);", img_element);
#                     self.vlog.output(2, img_element.get_attribute('src'))
#                     time.sleep(1)

                description_img_elements = WebDriverWait(self.__driver, 10) \
                      .until(EC.presence_of_all_elements_located((By.XPATH, description_img_xpath)))
                for img_element in description_img_elements:
                    self.vlog.output(2, img_element.get_attribute('src'))
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
    shopping_page_parser = ShoppingPageParser("../configure/shopping_page.ini")
    # shopping_page_parser.parse_shopping_page('http://www.amazon.cn/dp/B006FEPBF4?t=joyo01y-23&m=A1AJ19PSB66TGU&tag=joyo01y-23')
    url = 'http://www.amazon.cn/GRACO-%E7%BE%8E%E5%9B%BD%E8%91%9B%E8%8E%B1%E5%A9%B4%E5%84%BF%E6%8E%A8%E8%BD%A66N92CJB3J-%E9%BB%91%E8%89%B2/dp/B006FEPBF4'
    url = 'http://www.amazon.cn/GRACO-美国葛莱婴儿推车6N92CJB3J-黑色/dp/B006FEPBF4'
    url = "http://www.amazon.com/gp/product/B00H8MQBBA/ref=s9_psimh_gw_p75_d0_i2?pf_rd_m=ATVPDKIKX0DER&pf_rd_s=desktop-1&pf_rd_r=13G2J8GFVSCW56GPTVHV&pf_rd_t=36701&pf_rd_p=1970559082&pf_rd_i=desktop"
    shopping_page_parser.parse_shopping_page(url)

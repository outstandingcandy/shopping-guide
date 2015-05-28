import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../../../selenium/py')
sys.path.append('../')
sys.path.append('../../')
sys.path.append('bbzdm')

import re
import json
import time
import sqlite3
import ConfigParser

from scrapy.http import Request, FormRequest, Headers
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy_webdriver.http import WebdriverRequest
from scrapy_webdriver.selector import WebdriverXPathSelector
from scrapy import log
import items

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class SmzdmSpider(CrawlSpider):
    name = "smzdm"
    allowed_domains = ["smzdm.com"]
    __url_pattern_xpath_dict = {}
    __smzdm_log_file = "../../../log/smzdm.log"
    __shopping_log_file = "../../../log/shopping.log"


        
    def start_requests(self):
        log.start(logfile=self.__smzdm_log_file, loglevel='INFO', logstdout=False)
        
        smzdm_config = ConfigParser.RawConfigParser()
        smzdm_config.read("configure/smzdm.ini")
        self.price_pattern = re.compile(smzdm_config.get("item_page", "price_pattern").decode("utf-8"))
        self.head_separator = smzdm_config.get("item_page", "head_separator_pattern").decode("utf-8")
        self.attachment_pattern = re.compile(smzdm_config.get("item_page", "attachment_pattern").decode("utf-8"))

        config_file_name = "configure/shopping_page.ini"
        shopping_config = ConfigParser.RawConfigParser()
        shopping_config.read(config_file_name)
        
        for section_name in shopping_config.sections():
            log.msg("Supported url pattern:\t%s" % shopping_config.get(section_name, "url_pattern").decode('utf8'), level=log.DEBUG, spider=SmzdmSpider)
            url_pattern = re.compile(shopping_config.get(section_name, "url_pattern").decode('utf8'))
            title_xpath = shopping_config.get(section_name, "title_xpath")
            price_xpath = shopping_config.get(section_name, "price_xpath")
            price_redudant_pattern = re.compile(shopping_config.get(section_name, "price_redudant_pattern").decode('utf8'))
            description_xpath = shopping_config.get(section_name, "description_xpath")
            description_img_xpath = shopping_config.get(section_name, "description_img_xpath")
            self.__url_pattern_xpath_dict[url_pattern] = (title_xpath, \
                    price_xpath, price_redudant_pattern, description_xpath, description_img_xpath)
                    
        CrawlSpider.start_requests(self)
        yield WebdriverRequest('http://www.smzdm.com/fenlei/yingertuiche/youhui/p1', callback=self.parse_smzdm_list_page)
        # for i in range(20):
        #    yield WebdriverRequest('http://www.smzdm.com/p/625341', callback=self.parse_smzdm_item_page)
        
    def parse_smzdm_list_page(self, response):
        sel = WebdriverXPathSelector(response)
        item_url_sel_list = sel.select("/html/body/section//div[@class='listTitle']/h3[@class='itemName']/a/@href")
        for item_url_sel in item_url_sel_list:
            item_url = item_url_sel.extract()
            yield WebdriverRequest(item_url, callback=self.parse_smzdm_item_page)
        next_page_xpath = "//li[@class='pagedown']/a/@href"
        next_page_url_sel_list = sel.select(next_page_xpath)
        for next_page_url_sel in next_page_url_sel_list:
            next_page_url = next_page_url_sel.extract()
            yield WebdriverRequest(next_page_url, callback=self.parse_smzdm_list_page)
            
    def parse_smzdm_item_page(self, response):
        sel = WebdriverXPathSelector(response)
        title_sel_list = sel.select('/html/body/section/div[1]/article/h1')
        attachment_sel_list = sel.select('/html/body/section/div[1]/article/h1/span')
        if len(title_sel_list):
            title = self.normalize_text(title_sel_list[0].extract())
            item_name = title
        else:
            log.msg("Smzdm title parse failed:\t[%s]" % (response.url) , level=log.ERROR, spider=SmzdmSpider)
            raise StopIteration
        all_attachment = ''
        for attachment_sel in attachment_sel_list:
            attachment = attachment_sel.extract()
            item_name = item_name.replace(attachment, '')
            all_attachment += attachment
        price = self.parse_price(all_attachment)
        item_shopping_url_sel_list = sel.select("/html/body/section/div[1]/article/div[2]/div/div/a/@href")
        if len(item_shopping_url_sel_list):
            item_shopping_url = item_shopping_url_sel_list[0].extract()
            yield WebdriverRequest(item_shopping_url, meta={'referer': response.url}, callback=self.parse_shopping_item_page)
        description_sel_list = sel.select('/html/body/section/div[1]/article/div[2]/p[@itemprop="description"]')
        description = ''
        img_src_list = []
        for description_sel in description_sel_list:
            description += self.normalize_text(description_sel.extract())
            img_src_sel_list = description_sel.select("img/@src")
            for img_src_sel in img_src_sel_list:
                img_src_list.append(img_src_sel.extract())

        worthy_vote = int(self.get_element_by_xpath(sel, "//span[@id='rating_worthy_num']/text()").extract().strip())
        unworthy_vote = int(self.get_element_by_xpath(sel, "//span[@id='rating_unworthy_num']/text()").extract().strip())
        favorite_count = int(self.get_element_by_xpath(sel, "//a[@class='fav']/em/text()").extract().strip())
        comment_count = int(self.get_element_by_xpath(sel, "//a[@class='comment']/em/text()").extract().strip())
        yield items.SmzdmItem(title=item_name, price=price, url=response.url, description=description, \
                              image_urls=img_src_list, worthy_vote=worthy_vote, unworthy_vote=unworthy_vote, \
                              favorite_count=favorite_count, comment_count=comment_count)

        
    def parse_shopping_item_page(self, response):
        sel = WebdriverXPathSelector(response)
        referer = response.meta["referer"]
        jd_jump_url_sel = sel.select("/html/body/div[5]/div/div/div[1]/div[2]/div[3]/a/@href")
        if jd_jump_url_sel:
            log.msg("JD jump url:\t[%s]" % (jd_jump_url_sel[0].extract()) , level=log.DEBUG, spider=SmzdmSpider)
            yield WebdriverRequest(jd_jump_url_sel[0].extract(), meta={'referer': referer}, callback=self.parse_shopping_item_page)
        else:
            img_src_list = []
            description = ""
            title = ""
            price = -1.0
            log.msg("Shopping url: %s" % (response.url), level=log.DEBUG, spider=SmzdmSpider)
            log.msg("Real shopping url: %s" % (response.webdriver.current_url), level=log.DEBUG, spider=SmzdmSpider)
            url = response.webdriver.current_url
            for url_pattern, (title_xpath, price_xpath, price_redudant_pattern, description_xpath, description_img_xpath) in self.__url_pattern_xpath_dict.items():
                if url_pattern.match(url):
                    log.msg("Shopping url pattern is found", level=log.DEBUG, spider=SmzdmSpider)
                    title_sel_list = sel.select(title_xpath)
                    if len(title_sel_list):
                        title = self.normalize_text(title_sel_list[0].extract())
                    else:
                        log.msg("Shopping page error:\ttitle is not found", level=log.ERROR, spider=SmzdmSpider)
                        raise StopIteration
                        continue
                    price_sel_list = sel.select(price_xpath)
                    if len(price_sel_list):
                        price_text = price_sel_list[0].extract()
                        price_text = price_redudant_pattern.sub('', price_text)
                        try:
                            price = float(price_text)
                        except:
                            log.msg("Shopping page error:\tThis item is sold out, the price is %s" % (price), level=log.WARNING, spider=SmzdmSpider)
                    else:
                        log.msg("Shopping page error:\tprice is not found", level=log.WARNING, spider=SmzdmSpider)
                    if url_pattern.match('http://www.amazon.'):
                        try:
                            WebDriverWait(response.webdriver, 10) \
                                .until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="product-description-iframe"]')))
                        except:
                            log.msg("Shopping page error:\tFrame in Amazon is not found", level=log.ERROR, spider=SmzdmSpider)
                    
                    description_sel_list = sel.select(description_xpath + "/*")
                    for description_sel in description_sel_list:
                        description_part = self.normalize_text(description_sel.extract())
                        if description_part:
                            description += description_part + '\t'

                    description_img_sel_list = sel.select(description_img_xpath)
                    """ Run func with the given timeout. If func didn't finish running
                        within the timeout, raise TimeLimitExpired
                    """
                    import threading
                    class GetImgSrcThread(threading.Thread):
                        def __init__(self, driver, sel_list):
                            threading.Thread.__init__(self)
                            self.__driver = driver
                            self.__sel_list = sel_list
                
                        def run(self):
                            for sel in self.__sel_list:
                                try:
                                    self.__driver.execute_script("arguments[0].scrollIntoView(true);", sel.element)
                                    time.sleep(1)
                                except:
                                    log.msg("Shopping page error:\tscrollIntoView failed", level=log.ERROR, spider=SmzdmSpider)
                                    img_src_sel_list = sel.select("./@src")
                                    for img_src_sel in img_src_sel_list:
                                        log.msg("Shopping page error:\timage %s is not found" % (img_src_sel.extract()), level=log.ERROR, spider=SmzdmSpider)
                                    continue
                    it = GetImgSrcThread(response.webdriver, description_img_sel_list)
                    it.start()
                    it.join(60)
                    if it.isAlive():
                        break
                    description_img_sel_list = sel.select(description_img_xpath + "/@src")
                    log.msg("Shopping description img list: %s[%d]" % (description_img_sel_list, len(description_img_sel_list)) , level=log.DEBUG, spider=SmzdmSpider)
                    for description_img_sel in description_img_sel_list:
                        img_src = description_img_sel.extract()
                        if img_src:
                            img_src_list.append(img_src)
            log.msg("Shopping item: [%s] [%s] [%s] [%s] [%s]" % (title, description, price, url, referer) , level=log.DEBUG, spider=SmzdmSpider)
            yield items.ShoppingItem(title=title, price=price, url=url, referer=referer, image_urls=img_src_list, description=description)
        
    def parse_price(self, attachment):
        price = 0.0
        tokens = attachment.split(' ')
        for token in tokens:
            price_match = self.price_pattern.match(token)
            if price_match:
                price = float(price_match.group(1))
                break
        return price
    
    def normalize_text(self, text):
        return text.strip().replace("\n", "").replace("\"", "")
    
    def get_element_by_xpath(self, sel, xpath):
        sel_list = sel.select(xpath)
        if len(sel_list):
            return sel_list[0]
        else:
            log.msg("Get element by xpath %s failed:\t[%s]" % (xpath) , level=log.ERROR, spider=SmzdmSpider)

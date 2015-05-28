#!/usr/bin/python
#-*- coding:utf-8

import sys
reload(sys)

import re
import os
import urllib
import sqlite3
import md5
from lxml import html
import requests
import cookielib
import pickle
import time
import ConfigParser

class SmzdmCrawler(object):

    header_info = {
                   'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36',
                   'Content-Type':'text/html;charset=utf-8',
                   'Access-Control-Allow-Credentials':'true',
                   'Refer':'http://www.smzdm.com/fenlei/yingertuiche/youhui/',
                   'Cookie':'smzdm_user_source=FB0041F3A80FE9127CAD79892EAC850F; __gads=ID=ccd3d8b652095fd7:T=1416807348:S=ALNI_MZgEU-E3LsjHkG9tUM3K3BqEEGXoQ; c0aed2c2987b59ebb30db214d5c448a39=gznsPEE%3D; bdshare_firstime=1416813838316; __utma=123313929.1035736915.1416807348.1417160933.1418190662.3; __utmz=123313929.1417160933.2.2.utmcsr=search.smzdm.com|utmccn=(referral)|utmcmd=referral|utmcct=/; 3thread-20150320183143=3; 3thread-20150320182719=3; 3thread-20150330094446=1; 3thread-20150216174551=8; 3thread-20150330094602=4; 3thread-20150402183807=1; 3thread-20150330100002=6; smzdm_user_view=33910265B3962F1C1770BF1625E66166; crtg_rta=; wt3_eid=%3B999768690672041%7C2142362523700629423%232142900771000087502; 2thread-20150403194411=2; 3thread-20150403194411=7; niuxamss30=40; __jsluid=33a79fe223974deb808fcfbf7d200a54; __jsl_clearance=1429066457.321|0|MQghBTulTbg3rNCXDuzemffoKYI%3d; _ga=GA1.2.1035736915.1416807348; _gat=1; Hm_lvt_9b7ac3d38f30fe89ff0b8a0546904e58=1428631650,1428897980,1428977868,1429066461; Hm_lpvt_9b7ac3d38f30fe89ff0b8a0546904e58=1429066461; AJSTAT_ok_pages=1; AJSTAT_ok_times=86; amvid=b38544510be087210e22717308f53e20; PHPSESSID=plqmu2i3bsfvpq1taprtb2qoj5'
                }

    def __init__(self, config_file_name):
        """Inits SmzdmParser"""
        config = ConfigParser.RawConfigParser()
        config.read(config_file_name)
        webpage_database_path = config.get("database", "path")
        self.conn = sqlite3.connect(webpage_database_path)
        self.webpage_database_name = webpage_database_path.split("/")[-1]
        self.c = self.conn.cursor()
        # Drop table
        # self.c.execute("DROP TABLE %s" % (self.webpage_database))
        # Create table
        self.c.execute('''CREATE TABLE IF NOT EXISTS %s (url text unique, page text, title text, description text, recommanded_price float, \
                                                        score float, worthy_vote int, unworthy_vote int, favorite int, comment int, \
                                                        shopping_price float, shopping_url text, item_name text)''' % (self.webpage_database_name))

    def parse_list_page(self, url):
        page = requests.get(url, headers=self.header_info)
        tree = html.fromstring(page.text)
        print url
        print page.text
        item_urls = tree.xpath("//div[@class='listTitle']/h3[@class='itemName']/a")
        for item_url in item_urls:
            print 'Items: ', item_url.get('href')
            self.parse_item_page(item_url)
            
    def parse_item_page(self, url):
        page = requests.get(url, headers=self.header_info)
        tree = html.fromstring(page.text)
        titles = tree.xpath("/html/body/section/div[1]/article/h1")
        for title in titles:
            print 'Items: ', title.text
        descriptions = tree.xpath('/html/body/section/div[1]/article/h1/span')
        for descripion in descriptions:
            print 'Description: ', descripion.text
        
if __name__ == '__main__':
    smzdm_crawler = SmzdmCrawler('../configure/smzdm.ini')
    for page_num in range(1,2):
        list_page_url = 'http://www.smzdm.com/fenlei/yingertuiche/youhui/p%d' % page_num
        smzdm_crawler.parse_list_page(list_page_url)
        time.sleep(1)
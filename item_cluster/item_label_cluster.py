#!/usr/bin/python
#-*- coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../../jieba/')

import re
import sqlite3
import json
import math
import jieba
import jieba.analyse
from urlparse import urlparse,urlunparse,parse_qs
import hashlib
import md5

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class LinkGraph(object):
    def __init__(self, graph):
        self.graph = graph
        self.cc_id = {}
        self.marked = set()
        self.count = 0

    def get_connected_component(self):
        for url in self.graph:
            if url not in self.marked:
                self.dfs(url)
                self.count += 1
        return self.cc_id

    def dfs(self, url):
        self.marked.add(url)
        if self.count not in self.cc_id:
            self.cc_id[self.count] = [url]
        else:
            self.cc_id[self.count].append(url)
        for adj_url in self.graph[url]:
            if adj_url not in self.marked:
                self.dfs(adj_url)

class ItemLabelCluster(object):
    """ Item Cluster
    """
    item_name_redundance_list = [re.compile('\S+福利：'.decode('utf8')),
                                 re.compile('^新低价：'.decode('utf8')),
                                 re.compile('^限\S+：'.decode('utf8')),
                                 re.compile('^再特价：'.decode('utf8')),
                                 re.compile('^再降价：'.decode('utf8')),
                                 re.compile('^比海淘划算：'.decode('utf8')),
                                 re.compile('^历史低价：'.decode('utf8')),
                                 re.compile('^移动端：'.decode('utf8')),
                                 re.compile('^神价格：'.decode('utf8')),
                                 re.compile('^\d+点\d+开始：'.decode('utf8')),
                                 re.compile('[\d\.]+元(:?包邮)?'.decode('utf8')),
                                 re.compile('\S+可选(?:\s+|$)'.decode('utf8')),
                                 re.compile('\S+色款(?:\s+|$)'.decode('utf8')),
                                 re.compile('\S+色(?:\s+|$)'.decode('utf8')),
                                 re.compile('(?:\(|（).+(?:\)|）)'.decode('utf8'))]
    
    def get_item_category(self, url):
        host = urlparse(url).hostname

    def normalize_item_name(self, item_name):
        normalized_item_name = item_name.lower()
        for item_name_redundance in self.item_name_redundance_list:
            normalized_item_name = item_name_redundance.sub('', normalized_item_name);
        return normalized_item_name.strip()

    def normalize_item_description(self, item_description):
        normalized_item_description = item_description.replace("\"", "")
        return normalized_item_description

    def normalize_url(self, url):
        url = url.lower()
        r = urlparse(url)
        if r.hostname == "detail.tmall.com" or r.hostname == "detail.ju.taobao.com" or \
                r.hostname == "login.taobao.com" or r.hostname == "www.aiyingshi.com" or \
                r.hostname == "smzdmguanfang.gouwuke.com" or r.hostname == "www.supuy.com":
            return url
        elif r.hostname == "www.amazon.cn" and r.path == "/mn/detailapp/ref=as_li_ss_tl":
            return "http://www.amazon.cn/gp/product/" + parse_qs(r.query)["asin"][0]
        tokens = list(r)
        tokens[4] = ""
        tokens[5] = ""
        return urlunparse(tokens)

    def __init__(self, webpage_database_path, item_database_path):
        self.item_list = []
        self.webpage_database_conn = sqlite3.connect(webpage_database_path)
        self.webpage_database_conn.row_factory = dict_factory
        self.webpage_database_c = self.webpage_database_conn.cursor()
        self.webpage_database_name = webpage_database_path.split("/")[-1]

        self.item_database_conn = sqlite3.connect(item_database_path)
        self.item_database_c = self.item_database_conn.cursor()
        self.item_database_name = item_database_path.split("/")[-1]
        self.item_database_c.execute("DROP TABLE %s" % (self.item_database_name))
        self.item_database_c.execute('CREATE TABLE IF NOT EXISTS %s (item_id unique, item_name unique, score float, category text, current_price float, recommended_price float, image_path text, \
                                            jd_url text, jd_title text, jd_description text, jd_price float, jd_score float, jd_image_path_list text, \
                                            amazon_cn_url text, amazon_cn_title text, amazon_cn_description text, amazon_cn_price float, amazon_cn_score float, amazon_cn_image_path_list text, \
                                            amazon_com_url text, amazon_com_title text, amazon_com_description text, amazon_com_price float, amazon_com_score float, amazon_com_image_path_list text, \
                                            amazon_jp_url text, amazon_jp_title text, amazon_jp_description text, amazon_jp_price float, amazon_jp_score float, amazon_jp_image_path_list text, \
                                            suning_url text, suning_title text, suning_description text, suning_price float, suning_score float, suning_image_path_list text, \
                                            smzdm_url text, smzdm_title text, smzdm_description text, smzdm_price float, smzdm_score float, smzdm_image_path_list text)' % (self.item_database_name))
        self.item_database_conn.commit()
        
        url_graph = {}
        item_info_dict = {}
        max_score = 0
        item_name_dict = {}
        
        # Get item information
        # self.webpage_database_c.execute('SELECT url, title, description, price, referer FROM %s' % (self.webpage_database_name))
        # for result in self.webpage_database_c.fetchall():

        # for line in open("../../shopping-guide/scrapy/tutorial/database/smzdm.json"):
        self.webpage_database_c.execute('SELECT url, json FROM %s' % (self.webpage_database_name))
        for result in self.webpage_database_c.fetchall():
            try:
                result = json.loads(result["json"])
            except:
                continue
            if "url" in result and "title" in result:
                url = self.normalize_url(result["url"])
                title = result["title"]
            else:
                continue
            if "referer" in result:
                referer = self.normalize_url(result["referer"])
            else:
                referer = ""
            if "description" in result:
                description = self.normalize_item_description(result["description"])
            else:
                description = ""
            if "favorite_count" in result:
                score = float(result["favorite_count"])
            else:
                score = 0
            item_info_dict[url] = result
            item_info_dict[url]["url"] = url
            item_info_dict[url]["referer"] = referer
            item_info_dict[url]["description"] = description
            item_info_dict[url]["score"] = score
            if "images" not in item_info_dict[url]:
                item_info_dict[url]["images"] = []
            
            # Get item name
            domain = urlparse(url).hostname
            if domain == 'haitao.smzdm.com' or domain == 'www.smzdm.com':
                item_name = self.normalize_item_name(title.decode("utf-8"))
                item_info_dict[url]["item_name"] = item_name
                if item_name in item_name_dict:
                    item_name_dict[item_name].append(url)
                else:
                    item_name_dict[item_name] = [url]
#                 if item_info_dict[url]["images"]:
#                     thumbnail = item_info_dict[url]["images"][0]["path"].split("/")[-1].split(".")[0]
#                 if thumbnail:
#                     item_info_dict[url]["thumbnail"] = thumbnail

            # Get link graph
            if referer:
                if url in url_graph:
                    url_graph[url].add(referer)
                else:
                    url_graph[url] = set([referer])
                if referer in url_graph:
                    url_graph[referer].add(url)
                else:
                    url_graph[referer] = set([url])

        # Add edge in url graph
        for url_list in item_name_dict.values():
            print url_list
            for i in range(len(url_list)):
                for j in range(i+1, len(url_list)):
                    if url_list[i] in url_graph:
                        url_graph[url_list[i]].add(url_list[j])
                    else:
                        url_graph[url_list[i]] = set([url_list[j]])
                    if url_list[j] in url_graph:
                        url_graph[url_list[j]].add(url_list[i])
                    else:
                        url_graph[url_list[j]] = set([url_list[i]])

        # Get item cluster
        link_graph = LinkGraph(url_graph)
        item_cluster_dict = {}
        for url_cluster in link_graph.get_connected_component().values():
            print url_cluster
            selected_item_name = "x" * 999999
            selected_image_path = ""
            selected_score = 0
            selected_current_price = -1
            selected_recommended_price = -1
            for url in url_cluster:
                if "item_name" in item_info_dict[url] and len(item_info_dict[url]["item_name"]) < len(selected_item_name):
                    selected_item_name = item_info_dict[url]["item_name"]
                host = urlparse(url).hostname
                if host == 'haitao.smzdm.com' or host == 'www.smzdm.com':
                    if selected_recommended_price < 0 or \
                            (item_info_dict[url]["price"] > 0 and selected_recommended_price > item_info_dict[url]["price"]):
                        selected_recommended_price = item_info_dict[url]["price"]
                    if item_info_dict[url]["image_urls"]:
                        selected_image_path = hashlib.sha1(item_info_dict[url]["image_urls"][0]).hexdigest()
                elif selected_current_price < 0 or \
                        (item_info_dict[url]["price"] > 0 and selected_current_price > item_info_dict[url]["price"]):
                    selected_current_price = item_info_dict[url]["price"]
                selected_score += item_info_dict[url]["score"]
            if max_score < selected_score:
                max_score = selected_score
            item_cluster_dict[selected_item_name] = {}
            item_cluster_dict[selected_item_name]["item_name"] = selected_item_name
            item_cluster_dict[selected_item_name]["item_id"] = md5.new(selected_item_name).hexdigest()
            item_cluster_dict[selected_item_name]["image_path"] = selected_image_path
            item_cluster_dict[selected_item_name]["score"] = math.pow(selected_score / max_score, 0.2)
            item_cluster_dict[selected_item_name]["recommended_price"] = selected_recommended_price
            item_cluster_dict[selected_item_name]["current_price"] = selected_current_price
            item_cluster_dict[selected_item_name]["webpage"] = {}
            for url in url_cluster:
                item_cluster_dict[selected_item_name]["webpage"][url] = item_info_dict[url]
                print item_cluster_dict[selected_item_name]["item_name"].encode("utf-8"), url, item_cluster_dict[selected_item_name]["webpage"][url]["title"], item_cluster_dict[selected_item_name]["score"], max_score
            print "xxxxxxxxxxxxxxxx"

        # import to database
        for item_cluster in item_cluster_dict.values():
            self.insert_cluster(item_cluster)
            for item_info in item_cluster["webpage"].values():
                image_path_list = ""
                for image_url in item_info["image_urls"]:
                    image_path_list += hashlib.sha1(image_url).hexdigest() + "\t"
                image_path_list = image_path_list.strip()
                item_info["image_path_list"] = image_path_list
                item_info["item_name"] = item_cluster["item_name"]
                item_info["item_id"] = md5.new(item_cluster["item_name"]).hexdigest()
                site_name = urlparse(item_info["url"]).hostname
                if site_name == 'item.jd.com':
                    self.insert_item('jd', item_info)
                elif site_name == 'www.amazon.cn':
                    self.insert_item('amazon_cn', item_info)
                elif site_name == 'www.amazon.com':
                    self.insert_item('amazon_com', item_info)
                elif site_name == 'www.amazon.co.jp':
                    self.insert_item('amazon_jp', item_info)
                elif site_name == 'product.suning.com':
                    self.insert_item('suning', item_info)
                elif (site_name == 'www.smzdm.com' or domain == 'haitao.smzdm.com') and item_info["image_path_list"]:
                    self.insert_item('smzdm', item_info)

        self.item_database_conn.commit()

    def insert_cluster(self, item_cluster):
        recommended_price = item_cluster["recommended_price"]
        current_price = item_cluster["current_price"]
        score = item_cluster["score"]
        item_name = item_cluster["item_name"]
        item_id = item_cluster["item_id"]
        image_path = item_cluster["image_path"]
        self.item_database_c.execute("INSERT OR IGNORE INTO %s (item_id, item_name, recommended_price, current_price, score, image_path) \
                VALUES(?, ?, ?, ?, ?, ?)"  % (self.item_database_name), (item_id, item_name, recommended_price, current_price, score, image_path))

    def insert_item(self, site_name, item_info):
        url = item_info["url"]
        title = item_info["title"]
        description = item_info["description"]
        price = item_info["price"]
        score = item_info["score"]
        item_name = item_info["item_name"]
        item_id = item_info["item_id"]
        image_path_list = item_info["image_path_list"]
        self.item_database_c.execute("INSERT OR IGNORE INTO %s (item_id, item_name, %s_url, %s_title, %s_description, %s_price, %s_score, %s_image_path_list) \
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)" % (self.item_database_name, site_name, site_name, site_name, site_name, site_name, site_name), \
                (item_id, item_name, url, title, description, price, score, image_path_list))
        self.item_database_c.execute('UPDATE %s SET %s_url="%s", %s_title="%s", %s_description="%s", %s_price=%s, %s_score=%s, %s_image_path_list="%s" WHERE item_name="%s"' \
                                     % (self.item_database_name, site_name, url, site_name, title, site_name, description, site_name, price, site_name, score, site_name, image_path_list, item_name))

if __name__ == '__main__':
    item_cluster = ItemLabelCluster('../../data/smzdm', '../../data/item')

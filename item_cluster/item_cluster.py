#!/usr/bin/python
#-*- coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../cluster-1.2.2/')
sys.path.append('../jieba/')

import sqlite3
import jieba
import jieba.analyse
from cluster import KMeansClustering
import Orange

class ItemCluster(object):
    """ Item Cluster
    """
    def __init__(self, webpage_database):
        self.item_list = []
        conn = sqlite3.connect(webpage_database)
        c = conn.cursor()

        for row in c.execute('SELECT * FROM %s ORDER BY recommanded_price' % (webpage_database)):
            name = row[1]
            description = row[2]
            name_seg_list = jieba.cut(name)  # 默认是精确模式
            description_seg_list = jieba.cut(description)  # 默认是精确模式
            tags = jieba.analyse.extract_tags(description, topK=20, withWeight=True)
            self.item_list.append((name, description))

    def cut_setence(self, text):
        return jieba.cut(text)

    def extract_tags(self, text):
        return jieba.analyse.extract_tags(text, topK=20, withWeight=False)

    def statistic_term(self, tag_list, term_dict):
        term_count = len(term_dict)
        for tag in tag_list:
            if tag not in term_dict:
                term_dict[tag] = term_count
                term_count += 1

    def generate_features(self, feature_file_name):
        term_dict = {}
        item_info_list = []
        for (name, description) in self.item_list:
            name = name.replace('\n', ' ')
            name_tag_list = self.extract_tags(name)
            description_tag_list = self.extract_tags(description)
            item_info_list.append((name, name_tag_list, description_tag_list))
            self.statistic_term(name_tag_list, term_dict)
            self.statistic_term(description_tag_list, term_dict)
        feature_num = len(term_dict)
        print term_dict
        count = 0
        feature_names_line = ''
        feature_types_line = ''
        meta_line = ''
        feature_file = open(feature_file_name, 'w')
        for term in term_dict:
            feature_names_line += '%s\t' % term
            feature_types_line += 'continuous\t'
            meta_line += '\t'
            term_dict[term] = count
            count += 1
        feature_names_line += 'item_name\n'
        feature_types_line += 'string\n'
        meta_line += 'class\n'
        feature_file.write(feature_names_line)
        feature_file.write(feature_types_line)
        feature_file.write(meta_line)
        for item_name, item_name_tag_list, item_description_tag_list in item_info_list:
            item_feature_list = [0] * feature_num
            for item_name_tag in item_name_tag_list:
                item_feature_list[term_dict[item_name_tag]] += 1
            for item_description_tag in item_description_tag_list:
                item_feature_list[term_dict[item_description_tag]] += 1
            value_line = ''
            for item_feature in item_feature_list:
                value_line += '%d\t' % item_feature
            value_line += '%s\n' % item_name
            feature_file.write(value_line)
        feature_file.close()

    def cluster_item(self):
        cl = KMeansClustering(self.item_feature_list)
        clusters = cl.getclusters(2)
        print clusters
        for cluster in clusters:
            print cluster

if __name__ == '__main__':
    item_cluster = ItemCluster('webpage')
    item_cluster.generate_features('item.tab')
    item = Orange.data.Table("item.tab")
    km = Orange.clustering.kmeans.Clustering(item, 100)
    for i in range(100):
        print km.clusters[i], item[i].get_class()


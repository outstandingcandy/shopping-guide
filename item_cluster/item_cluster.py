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

class ItemCluster(object):
    """ Item Cluster
    """
    def __init__(self, webpage_database_path):
        self.item_list = []
        conn = sqlite3.connect(webpage_database_path)
        c = conn.cursor()
        webpage_database = webpage_database_path.split("/")[-1]
        for row in c.execute('SELECT * FROM %s ORDER BY recommanded_price' % (webpage_database)):
            url = row[0]
            print url
            name = row[1]
            print name.replace('\n', ' ')
            description = row[2]
            name_seg_list = jieba.cut(name)  # 默认是精确模式
            description_seg_list = jieba.cut(description)  # 默认是精确模式
            tags = jieba.analyse.extract_tags(description, topK=20, withWeight=True)
            if name:
                self.item_list.append((name, description))

    def cut_setence(self, text):
        return list(jieba.cut(text))

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
            name_tag_list = self.cut_setence(name)
            description_tag_list = self.cut_setence(description)
            item_info_list.append((name, name_tag_list, description_tag_list))
            self.statistic_term(name_tag_list, term_dict)
            # self.statistic_term(description_tag_list, term_dict)
        feature_num = len(term_dict)
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
            # for item_description_tag in item_description_tag_list:
            #    item_feature_list[term_dict[item_description_tag]] += 1
            value_line = ''
            for item_feature in item_feature_list:
                value_line += '%d\t' % item_feature
            value_line += '%s\n' % item_name
            feature_file.write(value_line)
        feature_file.close()

if __name__ == '__main__':
    item_cluster = ItemCluster('../../data/webpage')
    item_cluster.generate_features('item.tab')
    items = Orange.data.Table("item.tab")
    #km = Orange.clustering.kmeans.Clustering(item, 10)
    #for i in range(len(item)):
    #    print km.clusters[i], item[i].get_class()

    import Orange

    root = Orange.clustering.hierarchical.clustering(items, \
                                                     distance_constructor=Orange.distance.Euclidean, \
                                                     linkage=Orange.clustering.hierarchical.AVERAGE)
    topmost = sorted(Orange.clustering.hierarchical.top_clusters(root, 50), key=len)
    for n, cluster in enumerate(topmost):
        print "\n\n Cluster %i \n" % n
        for instance in cluster:
            print items[instance].get_class()
    labels = [str(item.get_class()) for item in items]
    Orange.clustering.hierarchical.dendrogram_draw("hclust-dendrogram.png", root, labels=labels) 


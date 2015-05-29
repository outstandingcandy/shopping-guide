#!/usr/bin/python
#-*- coding:utf-8

from flask import Flask, render_template, request
import sqlite3
import md5
import json
import os
from flask.testsuite import catch_stderr

import sys  
from flask.helpers import url_for
reload(sys)  
sys.setdefaultencoding('utf8')  

app = Flask(__name__)

# controllers
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def reconstruct_item(result):
    item_detail_url = url_for(".item_detail", item_id=result["item_id"])
    item = {'recommended':[], 'shopping':[], 'item_name':result["item_name"], 'item_id':result["item_id"], 'detail_url':item_detail_url, 'star':0}
    for site_name in ['smzdm']:
        if result["%s_url" % site_name]:
            url_md5 = md5.new(result["%s_url" % site_name]).hexdigest()
            img_path_list = result["%s_image_path_list" % site_name].split("\t")
            if img_path_list:
                item['img'] = img_path_list[0]
            item['recommended'].append({"site":site_name, \
                                               "url":result["%s_url" % site_name], \
                                               "url_md5" : url_md5, \
                                               "img_list" : img_path_list, \
                                               "title":result["%s_title" % site_name], \
                                               "price":result["%s_price" % site_name], \
                                               "description":result["%s_description" % site_name], \
                                               "score":result["%s_score" % site_name]})
            item['recommended_score'] = result["%s_score" % site_name]
            item['lowest_price'] = result["%s_price" % site_name]
            item['star'] = int(result["%s_score" % site_name] * 5)
    for site_name in ['jd', 'amazon_cn', 'amazon_com', 'amazon_jp', 'suning']:
        if result["%s_url" % site_name]:
            url_md5 = md5.new(result["%s_url" % site_name]).hexdigest()
            img_path_list = []
            for img_path in result["%s_image_path_list" % site_name].split("\t"):
                img_path_list.append(img_path)
            item['shopping'].append({"site":site_name, \
                                              "url":result["%s_url" % site_name], \
                                              "url_md5" : url_md5, \
                                              "img_list" : img_path_list, \
                                              "title":result["%s_title" % site_name], \
                                              "price":result["%s_price" % site_name], \
                                              "description":result["%s_description" % site_name]})
            item['current_price'] = result["%s_price" % site_name]
    return item

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
def index():
    webpage_database_path = "../../data/webpage"
    conn = sqlite3.connect(webpage_database_path)
    c = conn.cursor()
    webpage_database = webpage_database_path.split("/")[-1]
    items = []
    for row in c.execute('SELECT * FROM %s ORDER BY recommanded_price DESC' % (webpage_database)):
        url = row[0]
        item_id = md5.new(url).hexdigest()
        name = row[1]
        description = row[2]
        price = row[3]
        real_price = row[4]
        shopping_url = row[5]
        items.append({'id':item_id, 'name':name, 'description':description, \
                'price':price, 'real_price':real_price, 'shopping_url':shopping_url})
    return render_template('index.html', items=items)

@app.route("/search")
def search():
    count = request.args.get('count')
    if not count:
        count = 10
    else:
        count = int(count)
    webpage_database_path = "../../data/webpage"
    conn = sqlite3.connect(webpage_database_path)
    c = conn.cursor()
    webpage_database = webpage_database_path.split("/")[-1]
    items = []
    for row in c.execute('SELECT * FROM %s ORDER BY recommanded_price DESC LIMIT %d' % (webpage_database, count)):
        item = {}
        item["url"] = row[0]
        item["item_id"] = md5.new(row[0]).hexdigest()
        item["name"] = row[1]
        item["description"] = row[2]
        item["price"] = row[3]
        item["real_price"] = row[4]
        item["shopping_url"] = row[5]
        items.append(item)
    return json.dumps(items)

@app.route("/operator", methods=['POST', 'GET'])
def operator():
    category = request.args.get('category')
    if not category:
        category = "joggler"
    webpage_database_path = "../../data/webpage"
    conn = sqlite3.connect(webpage_database_path)
    c = conn.cursor()
    webpage_database = webpage_database_path.split("/")[-1]
    items = {}
    for row in c.execute('SELECT * FROM %s ORDER BY recommanded_price DESC' % (webpage_database)):
        url = row[0]
        item_id = md5.new(url).hexdigest()
        title = row[1]
        description = row[2]
        price = row[3]
        real_price = row[4]
        shopping_url = row[5]
        item_name = row[6]
        items[item_id] = ({'id':item_id, 'name':item_name, 'description':description, \
                'price':price, 'real_price':real_price, 'shopping_url':shopping_url, 'title':title})
    item_database_path = "../../data/item"
    conn = sqlite3.connect(item_database_path)
    item_database_name = item_database_path.split("/")[-1]
    c = conn.cursor()
    new_items = {}
    for row in c.execute('SELECT * FROM %s ORDER BY smzdm_price DESC' % (item_database_name)):
        item_name = row[0]
        try:
            item_id = md5.new(item_name).hexdigest()
        except Exception, e:
            print e
            continue
        
        name = row[1]
        description = row[2]
        price = row[3]
        real_price = row[4]
        shopping_url = row[5]
        new_items[item_id] = ({'id':item_id, 'name':item_name, 'description':description, \
                'price':price, 'real_price':real_price, 'shopping_url':shopping_url})
    return render_template('operate.html', items=items, new_items=new_items)

@app.route("/update_item_info", methods=['POST'])
def update_item_info():
    return request.form["real_name"]

@app.route("/list_item", methods=['POST', 'GET'])
def list_item():
    item_database_path = "../../data/item"
    con = sqlite3.connect(item_database_path)
    con.row_factory = dict_factory
    item_database_name = item_database_path.split("/")[-1]
    cur = con.cursor()
    cur.execute('SELECT * FROM %s ORDER BY smzdm_score DESC' % (item_database_name))
    items = []
    for result in cur.fetchall():
        items.append(reconstruct_item(result))
    return render_template('item_list.html', items=items)

@app.route("/item_detail/<item_id>", methods=['POST', 'GET'])
def item_detail(item_id):
    item_database_path = "../../data/item"
    con = sqlite3.connect(item_database_path)
    con.row_factory = dict_factory
    item_database_name = item_database_path.split("/")[-1]
    cur = con.cursor()
    cur.execute('SELECT * FROM %s WHERE item_id="%s"' % (item_database_name, item_id))
    result = cur.fetchone()
    return render_template('item_detail.html', item=reconstruct_item(result))

if __name__ == '__main__':
    app.run(debug=True,  host='0.0.0.0')


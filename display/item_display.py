#!/usr/bin/python
#-*- coding:utf-8

from flask import Flask, render_template
import sqlite3
import md5

app = Flask(__name__)

# controllers

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
def index():
    webpage_database_path = "../data/webpage"
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

if __name__ == '__main__':
    app.run()


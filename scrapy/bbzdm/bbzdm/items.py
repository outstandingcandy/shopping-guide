# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class SmzdmItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    referer = scrapy.Field()
    price = scrapy.Field()
    image_urls = scrapy.Field()
    title_image_url = scrapy.Field()
    images = scrapy.Field()
    worthy_vote = scrapy.Field()
    unworthy_vote = scrapy.Field()
    favorite_count = scrapy.Field()
    comment_count = scrapy.Field()
    category = scrapy.Field()
    currency = scrapy.Field()

class ShoppingItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    referer = scrapy.Field()
    price = scrapy.Field()
    image_urls = scrapy.Field()
    title_image_url = scrapy.Field()
    images = scrapy.Field()
    currency = scrapy.Field()

class SmzdmPostItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    referer = scrapy.Field()
    outer_link_list = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()

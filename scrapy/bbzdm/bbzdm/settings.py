# -*- coding: utf-8 -*-

# Scrapy settings for bbzdm project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import os
print os.getcwd()
BOT_NAME = 'bbzdm'

SPIDER_MODULES = ['bbzdm.spiders']
NEWSPIDER_MODULE = 'bbzdm.spiders'
COOKIES_ENABLED = True

DOWNLOAD_TIMEOUT = 60
RETRY_ENABLED = False
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'bbzdm (+http://www.yourdomain.com)'

# DOWNLOAD_HANDLERS = {'http': 'bbzdm.handler.mydownloader.MyDownloadHandler'}
IMAGES_STORE = '../../../image'
IMAGES_THUMBS = {
    'small': (50, 50),
    'big': (270, 270),
}

DOWNLOAD_HANDLERS = {
    'http': 'scrapy_webdriver.download.WebdriverDownloadHandler',
    'https': 'scrapy_webdriver.download.WebdriverDownloadHandler',
}

SPIDER_MIDDLEWARES = {
    'scrapy_webdriver.middlewares.WebdriverSpiderMiddleware': 543,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy_webdriver.downloader_middlewares.WebdriverDownloaderMiddleware': 400,
}

ITEM_PIPELINES = {
    'bbzdm.pipelines.SmzdmPipeline': 300,
    'scrapy.contrib.pipeline.images.ImagesPipeline': 301,
}

WEBDRIVER_BROWSER = 'Chrome'  # Or any other from selenium.webdriver
                                 # or 'your_package.CustomWebdriverClass'
                                 # or an actual class instead of a string.
# Optional passing of parameters to the webdriver
WEBDRIVER_OPTIONS = {
    'service_args': ['--debug=true', '--load-images=false', '--webdriver-loglevel=debug'],
    # 'executable_path': '../../../chromedriver.exe'
    'executable_path': '../../../chromedriver'
}



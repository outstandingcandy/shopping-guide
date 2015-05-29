from scrapy.exceptions import IgnoreRequest, NotConfigured

from .http import WebdriverActionRequest, WebdriverRequest
from .manager import WebdriverManager


class WebdriverDownloaderMiddleware(object):
    def process_exception(self, request, exception, spider):
        return request

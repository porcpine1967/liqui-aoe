#!/usr/bin/env python3
""" Gets data from appropriate source."""
import time
from bs4 import BeautifulSoup
import requests
import vcr
THROTTLE = 30

class HttpsLoader:
    """ Object for downloading date from liquipedia."""
    def __init__(self):
        self.last_call = 0
        self._headers = {"User-Agent": "liqui-aoe/0.1 (feroc.felix@gmail.com)","Accept-Encoding": "gzip"}
        self._base_url = "https://liquipedia.net/ageofempires/api.php?redirects=true&action=parse&format=json&page={}"

    @property
    def throttle(self):
        return THROTTLE

    def soup(self, path):
        # Per liquipedia api terms of use, parse requires 30 second throttle
        if self.last_call + self.throttle > time.time():
            time.sleep(self.last_call + self.throttle - time.time())
        _, _, tail = path.split("/", 2)
        url = self._base_url.format(tail)
        response = self.fetch_response(url, tail)
        self.last_call = time.time()
        if response.status_code == 200:
            try:
                page_html = response.json()['parse']['text']['*']
                return BeautifulSoup(page_html, "html.parser")
            except KeyError:
                raise RequestsException(response.text, response.status_code)    
        else:
            raise RequestsException(response.text, response.status_code)

    def fetch_response(self, url, _):
        return requests.get(url, headers=self._headers)

class VcrLoader(HttpsLoader):
    """Object for fetching test data from cassettes."""
    def fetch_response(self, url, tail):
        with vcr.use_cassette("tests/vcr_cassettes/{}".format(tail)):
            return requests.get(url, headers=self._headers)

    @property
    def throttle(self):
        return 0

class RequestsException(Exception):

    def init(self, message, code=500):
        super(RequestsException, self).init(message)
        self.code = code

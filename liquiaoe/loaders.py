#!/usr/bin/env python3
""" Gets data from appropriate source."""
import os
import pathlib
import time
from bs4 import BeautifulSoup
import requests
import vcr
THROTTLE = 32
CASSETTE_DIR = "{}/tests/vcr_cassettes".format(pathlib.Path(__file__).parent.parent.resolve())

def tail(path):
    """ Expects /ageofempires/(tail)"""
    return path.split("/", 2)[-1]

def cassette(path):
    cassette_path = "{}/{}".format(CASSETTE_DIR, tail(path))
    if os.path.isdir(cassette_path):
        return cassette(path + "/index")
    return cassette_path

class HttpsLoader:
    """ Object for downloading date from liquipedia."""
    def __init__(self):
        self.last_call = 0
        self._headers = {"User-Agent": "liqui-aoe/0.1 (feroc.felix@gmail.com)","Accept-Encoding": "gzip"}
        self._base_url = "https://liquipedia.net/ageofempires/api.php?redirects=true&action=parse&format=json&page={}"

    def throttle(self, _):
        return THROTTLE

    def available(self, tail):
        return True

    def soup(self, path):
        # Per liquipedia api terms of use, parse requires 30 second throttle
        print("CALLING: {}".format(path))
        if self.last_call + self.throttle(path) > time.time():
            time.sleep(self.last_call + self.throttle(path) - time.time())
        url = self._base_url.format(tail(path))
        response = self.fetch_response(url, path)
        self.last_call = time.time()
        if response.status_code == 200:
            info = response.json()
            try:
                page_html = info['parse']['text']['*']
                return BeautifulSoup(page_html, "html.parser")
            except KeyError:
                try:
                    if info["error"]["code"] == "missingtitle":
                        raise RequestsException(response.text, 404)
                except KeyError:
                    pass
                raise RequestsException(response.text, response.status_code)    
        else:
            raise RequestsException(response.text, response.status_code)

    def fetch_response(self, url, _):
        return requests.get(url, headers=self._headers)

class VcrLoader(HttpsLoader):
    """Object for fetching test data from cassettes."""

    def fetch_response(self, url, path):
        with vcr.use_cassette(cassette(path)):
            return requests.get(url, headers=self._headers)

    def available(self, path):
        return os.path.exists(cassette(path))

    def throttle(self, path):
        if self.available(path):
            return 0
        else:
            return THROTTLE

class RequestsException(Exception):

    def __init__(self, message, code=500):
        self.code = code
        super().__init__(message)

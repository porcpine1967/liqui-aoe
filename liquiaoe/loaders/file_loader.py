#!/usr/bin/env python3
""" Gets html file data from test directory."""

from bs4 import BeautifulSoup


class Loader:
    """Object for fetching information."""

    def soup(self, url):
        """Returns soup object for object at file location."""
        file_name = url.split("/")[-1]
        with open("tests/data/{}".format(file_name)) as fp:
            return BeautifulSoup(fp, "html.parser")

#!/usr/bin/env python3
""" Gets data from appropriate source."""

from bs4 import BeautifulSoup


class FileLoader:
    """Object for fetching test data from file system."""

    def soup(self, url):
        """Returns soup object for object at file location."""
        file_name = url.split("/", 2)[-1]
        with open("tests/data/{}".format(file_name)) as fp:
            return BeautifulSoup(fp, "html.parser")

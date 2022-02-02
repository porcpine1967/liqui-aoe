#!/usr/bin/env python3
""" Tests loaders"""
import time

import vcr
import pytest

from liquiaoe.loaders import HttpsLoader, VcrLoader, THROTTLE

@pytest.fixture
def availability_urls():
    return (
        ("/ageofempires/Wrang_of_Fire/3", True,),
        ("/ageofempires/N4C/1/Qualifier/2", False,),
    )

def test_https_loader():
    """ To test the connection/reload the cassete, change record_mode to "all" """
    loader = HttpsLoader()
    with vcr.use_cassette('tests/vcr_cassettes/Ayre_Masters_Series/2', record_mode="once"):
        loader.soup("/ageofempires/Ayre_Masters_Series/2")

@pytest.mark.skip(reason="Only test occasionally as takes 30 seconds by definition")
@pytest.mark.timeout(32)
def test_throttle():
    loader = HttpsLoader()
    loader.soup("/ageofempires/Ayre_Masters_Series/2")
    first_call = int(time.time())
    loader.soup("/ageofempires/Ayre_Masters_Series/2")
    assert first_call + THROTTLE <= time.time()

def test_https_available(availability_urls):
    loader = HttpsLoader()
    for url, _ in availability_urls:
        assert loader.available(url)

def test_vcr_available(availability_urls):
    loader = VcrLoader()
    for url, available in availability_urls:
        assert loader.available(url) == available

def test_debugging_removed():
    assert THROTTLE == 32
    with open("liquiaoe/loaders.py") as f:
        for l in f:
            assert "print(" not in l
    with open("liquiaoe/managers.py") as f:
        for l in f:
            assert "print(" not in l

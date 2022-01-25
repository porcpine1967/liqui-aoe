#!/usr/bin/env python3
""" Tests loaders"""
import time

import vcr
import pytest

from liquiaoe.loaders import HttpsLoader, THROTTLE

def test_https_loader():
    """ To test the connection/reload the cassete, change record_mode to "all" """
    loader = HttpsLoader()
    with vcr.use_cassette('tests/vcr_cassettes/ayre_masters_series_2.yaml', record_mode="once"):
        loader.soup("/ageofempires/Ayre_Masters_Series/2")

@pytest.mark.skip(reason="Only test occasionally as takes 30 seconds by definition")
@pytest.mark.timeout(32)
def test_throttle():
    loader = HttpsLoader()
    loader.soup("/ageofempires/Ayre_Masters_Series/2")
    first_call = int(time.time())
    loader.soup("/ageofempires/Ayre_Masters_Series/2")
    assert first_call + THROTTLE <= time.time()

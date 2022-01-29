#!/usr/bin/env python3

from datetime import date
import pytest
from liquiaoe.managers.player_manager import PlayerManager
from liquiaoe.loaders import VcrLoader

@pytest.fixture
def player_manager():
    return PlayerManager(VcrLoader())

def test_viper(player_manager):
    """ Tests the viper's page."""
    viper_url = "/ageofempires/TheViper"
    tournaments = player_manager.tournaments(viper_url)
    assert len(tournaments) == 214

def test_trundo(player_manager):
    trundo_url = "/ageofempires/index.php?title=Trundo&action=edit&redlink=1"
    
    tournaments = player_manager.tournaments(trundo_url)
    assert len(tournaments) == 0

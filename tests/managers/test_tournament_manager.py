#!/usr/bin/env python3
from datetime import datetime

import pytest

from liquiaoe.managers.tournament_manager import TournamentManager
from liquiaoe.loaders.file_loader import Loader


@pytest.fixture
def loader():
    return Loader()


def test_tournaments(loader):
    """Make sure tournament manager loads tournaments correctly."""
    tournament_manager = TournamentManager(loader)
    assert len(tournament_manager.all()) == 60
    tournaments = tournament_manager.all()
    tournament = tournaments[0]
    assert tournament.tier == "B-Tier"
    assert tournament.game == "Age of Empires II"
    assert tournament.name == "Ayre Masters Series 2: Arabia"
    assert tournament.url == "/ageofempires/Ayre_Masters_Series/2"
    assert tournament.start == datetime(2022, 4, 29)
    assert tournament.end == datetime(2022, 5, 1)
    assert tournament.prize == "$500"
    assert tournament.participant_count == 8

    assert not tournament.cancelled

    assert tournaments[3].end == datetime(2022, 3, 27)
    assert tournaments[11].start == datetime(2021, 12, 13)
    assert tournaments[11].end == datetime(2022, 2, 20)
    assert tournaments[16].start == tournaments[16].end == datetime(2022, 2, 8)

    assert tournaments[-1].cancelled

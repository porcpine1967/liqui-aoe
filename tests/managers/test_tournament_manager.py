#!/usr/bin/env python3
from datetime import datetime

import pytest

from liquiaoe.managers.tournament_manager import TournamentManager
from liquiaoe.loaders import FileLoader


@pytest.fixture
def loader():
    return FileLoader()


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
    assert tournament.first_place == "TBD"
    assert tournament.second_place == "TBD"

    assert tournaments[1].series == "Torneo Nacional Español 2021"

    assert tournaments[3].end == datetime(2022, 3, 27)
    assert tournaments[11].start == datetime(2021, 12, 13)
    assert tournaments[11].end == datetime(2022, 2, 20)
    assert tournaments[16].start == tournaments[16].end == datetime(2022, 2, 8)

    assert tournaments[-1].cancelled

    assert tournaments[-2].first_place == "Leenock"
    assert tournaments[-2].first_place_url == "/ageofempires/Leenock"
    assert tournaments[-2].second_place == "duckdeok"

    assert tournaments[-4].first_place == "speed + dark"
    assert tournaments[-4].first_place_url == None

    
def test_team_tournament(loader):
    tournament_manager = TournamentManager(loader)
    tournaments = tournament_manager.all()
    tournament = tournaments[34]
    assert tournament.name == "Samedo's Civilization Cup 2021"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.description == "Samedo's Civilization Cup 2021 is an Age of Empires II 2v2 tournament organized by Samedo-sama."
    assert len(tournament.organizers) == 1
    assert tournament.organizers[0] == "Samedo-sama"
    assert tournament.game_mode == "Random Map"
    assert tournament.format_style == "2v2, Single Elimination"
    assert tournament.team
    assert len(tournament.runners_up) == 2
    assert tournament.runners_up[0] == "Sommos & Lacrima"
    assert tournament.runners_up[1] == "Target331 & Kloerb"


def test_simple_tournament(loader):
    tournament_manager = TournamentManager(loader)
    tournaments = tournament_manager.all()
    
    tournament = tournaments[37]

    assert tournament.name == "King of the African Clearing"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.description == "The King of the African Clearing is an Age of Empires II 1v1 tournament for hispanic players exclusively, hosted by Landon."
    assert len(tournament.organizers) == 1
    assert tournament.organizers[0] == "Landon"
    assert len(tournament.sponsors) == 1
    assert tournament.sponsors[0] == "Landon community"
    assert tournament.game_mode == "Random Map"
    assert tournament.format_style == "1v1, Single Elimination"
    assert not tournament.team
    assert len(tournament.runners_up) == 1
    assert tournament.runners_up == ["Bl4ck|Redlash"]
    

def test_single_fourth_place(loader):
    
    tournament_manager = TournamentManager(loader)
    tournaments = tournament_manager.all()
    tournament = tournaments[55]
    assert tournament.name == "PinG Communities"
    tournament.load_advanced(tournament_manager.loader)
    assert not tournament.team
    assert len(tournament.runners_up) == 2
    assert tournament.runners_up == ["Good_Game","Vitolio"]

def test_series_tournament(loader):
    """ TODO """

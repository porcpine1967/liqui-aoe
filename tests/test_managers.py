#!/usr/bin/env python3
from datetime import date
import pytest
from liquiaoe.managers import TournamentManager, PlayerManager
from liquiaoe.loaders import VcrLoader


@pytest.fixture
def tournament_manager():
    return TournamentManager(VcrLoader())

@pytest.fixture
def player_manager():
    return PlayerManager(VcrLoader())

def print_info(tournamentdict):
    for game, tournaments in tournamentdict.items():
        print("*"*25)
        print(game)
        print("*"*25)
        for tournament in tournaments:
            print("{:25}: {} - {}".format(tournament.name,
                                      tournament.start,
                                      tournament.end))

def test_advanced_from_player(player_manager):
    viper_url = "/ageofempires/TheViper"
    tournaments = player_manager.tournaments(viper_url)
    tournament = tournaments[1]
    tournament.load_advanced(player_manager.loader)
    assert tournament.name == "Winter Championship"
    assert tournament.tier == "S-Tier"
    assert tournament.game == "Age of Empires IV"
    assert tournament.url == "/ageofempires/Winter_Championship"
    assert tournament.end == date(2022, 1, 23)
    assert tournament.prize == "$20,000\xa0USD"
    assert not tournament.cancelled
    assert tournament.first_place == "Hera"
    assert tournament.first_place_url == "/ageofempires/Hera"
    assert tournament.second_place == "MarineLorD"
    assert tournament.runners_up[0] == "TheViper - Wam01"


def test_viper(player_manager):
    """ Tests the viper's page."""
    viper_url = "/ageofempires/TheViper"
    tournaments = player_manager.tournaments(viper_url)
    assert len(tournaments) == 214
    tournament = tournaments[0]
                             
    assert tournament.name == "GamerLegion vs White Wolf Palace (6)"
    assert tournament.end == date(2022, 1, 24)
    assert tournament.tier == "Show\xa0M."
    assert tournament.loader_prize == "$80"
    assert tournament.team
    assert tournament.game == "Age of Empires II"
    assert tournament.url == "/ageofempires/GamerLegion_vs_White_Wolf_Palace/6"
    assert tournament.loader_place == "2nd"
    
    tournament = tournaments[1]
                             
    assert tournament.name == "Winter Championship"
    assert tournament.end == date(2022, 1, 23)
    assert tournament.tier == "S-Tier"
    assert tournament.loader_prize == "$1,500"
    assert not tournament.team
    assert tournament.game == "Age of Empires IV"
    assert tournament.url == "/ageofempires/Winter_Championship"
    assert tournament.loader_place == "3\xa0-\xa04th"
    
def test_trundo(player_manager):
    trundo_url = "/ageofempires/index.php?title=Trundo&action=edit&redlink=1"
    
    tournaments = player_manager.tournaments(trundo_url)
    assert len(tournaments) == 0

def test_completed(tournament_manager):
    """ Tests tournament filter."""
    timebox = (date(2022, 1, 26), date(2022, 2, 1),)
    completed_tournaments = tournament_manager.completed(timebox)
    assert len(completed_tournaments["Age of Empires II"]) == 5
    assert len(completed_tournaments["Age of Empires IV"]) == 5
    assert len(completed_tournaments["Age of Empires Online"]) == 1
    assert len(completed_tournaments["Age of Mythology"]) == 1

def test_starting(tournament_manager):
    """ Tests tournament filter."""
    timebox = (date(2022, 1, 26), date(2022, 2, 1),)
    starting_tournaments = tournament_manager.starting(timebox)
    assert len(starting_tournaments["Age of Empires II"]) == 2
    assert len(starting_tournaments["Age of Empires IV"]) == 3
    assert len(starting_tournaments["Age of Empires Online"]) == 1
    assert len(starting_tournaments["Age of Mythology"]) == 1

def test_ongoing(tournament_manager):
    """ Tests tournament filter."""
    timebox = (date(2022, 1, 26), date(2022, 2, 1),)
    ongoing_tournaments = tournament_manager.ongoing(timebox)
    assert len(ongoing_tournaments["Age of Empires II"]) == 6
    assert len(ongoing_tournaments["Age of Empires IV"]) == 1
    assert len(ongoing_tournaments["Age of Empires Online"]) == 0
    assert len(ongoing_tournaments["Age of Mythology"]) == 2

def test_tournaments(tournament_manager):
    """Make sure tournament manager loads tournaments correctly."""
    assert len(tournament_manager.all()) == 60
    tournaments = tournament_manager.all()
    tournament = tournaments[0]
    assert tournament.tier == "B-Tier"
    assert tournament.game == "Age of Empires II"
    assert tournament.name == "Ayre Masters Series II: Arabia"
    assert tournament.url == "/ageofempires/Ayre_Masters_Series/2"
    assert tournament.start == date(2022, 4, 29)
    assert tournament.end == date(2022, 5, 1)
    assert tournament.prize == "$500"
    assert tournament.participant_count == 8
    assert not tournament.cancelled
    assert tournament.first_place == None
    assert tournament.second_place == None

    assert tournaments[3].end == date(2022, 3, 27)
    assert tournaments[13].start == date(2021, 12, 13)
    assert tournaments[13].end == date(2022, 2, 20)
    assert tournaments[18].start == tournaments[18].end == date(2022, 2, 8)

    assert tournaments[56].first_place == "Garnath"
    assert tournaments[56].first_place_url == "/ageofempires/Garnath"
    assert tournaments[56].second_place == "hhh_"

    assert tournaments[58].first_place == "speed + dark"
    assert tournaments[58].first_place_url == None


def test_team_tournament(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[36]
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


def test_simple_tournament(tournament_manager):
    tournaments = tournament_manager.all()

    tournament = tournaments[39]

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
    assert tournament.runners_up == ["Bl4ck - Redlash"]


def test_single_fourth_place(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[57]
    assert tournament.name == "PinG Communities"
    tournament.load_advanced(tournament_manager.loader)
    assert not tournament.team
    assert len(tournament.runners_up) == 2
    assert tournament.runners_up == ["Good_Game","Vitolio"]

def test_series_tournament(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[0]
    assert tournament.name == "Ayre Masters Series II: Arabia"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.description == "The Ayre Masters Series II: Arabia is an Age of Empires II 1v1 tournament hosted by Ayre Esports. It is the third event of the Ayre Pro Tour."
    assert tournament.series == "Ayre Pro Tour"

def test_multiple_organizers(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[13]
    assert tournament.name == "Master of HyperRandom"
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.organizers) == 2
    assert tournament.organizers == ["Zetnus", "Huehuecoyotl22",]

def test_multiple_organizers_no_links(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[1]
    assert tournament.name == "Torneo Nacional Español 2021"
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.organizers) == 4

def test_second_third_place(tournament_manager):
    tournaments = tournament_manager.all()

    tournament = tournaments[30]
    assert tournament.name == "Wrang of Fire 3"
    # Set because easier than messing with vcr
    tournament.first_place = "Trundo"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.second_place == "Enzberg - Joey the Bonqueror"

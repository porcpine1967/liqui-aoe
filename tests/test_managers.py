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

def print_info(tournaments):
    for idx, tournament in enumerate(tournaments):
        print("{:2}. {} (https://liquipedia.net{})".format(idx, tournament.name,
                                                           tournament.url))

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

def test_load_from_player_main_page(player_manager):
    kongensgade_url = "/ageofempires/Kongensgade"
    tournaments = player_manager.tournaments(kongensgade_url)
    assert len(tournaments) == 10
    tournament = tournaments[-1]
    assert tournament.name == "The Medieval Wars 2013"
    assert tournament.loader_place == "17\xa0-\xa032nd"

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
    timestamp = date(2022, 1, 26)
    ongoing_tournaments = tournament_manager.ongoing(timestamp)
    assert len(ongoing_tournaments["Age of Empires II"]) == 11
    assert len(ongoing_tournaments["Age of Empires IV"]) == 4
    assert len(ongoing_tournaments["Age of Empires Online"]) == 0
    assert len(ongoing_tournaments["Age of Mythology"]) == 2

def test_tournaments(tournament_manager):
    """Make sure tournament manager loads tournaments correctly."""
    assert len(tournament_manager.all()) == 60
    tournaments = tournament_manager.all()
    print_info(tournaments)
    tournament = tournaments[3]
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

    assert tournaments[6].end == date(2022, 3, 27)
    assert tournaments[16].start == date(2021, 12, 13)
    assert tournaments[16].end == date(2022, 2, 20)
    assert tournaments[21].start == tournaments[21].end == date(2022, 2, 8)

    assert tournaments[56].first_place == "Garnath"
    assert tournaments[56].first_place_url == "/ageofempires/Garnath"
    assert tournaments[56].second_place == "hhh_"

    assert tournaments[58].first_place == "speed + dark"
    assert tournaments[58].first_place_url == None


def test_team_tournament(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[1]
    assert tournament.name == "Samedo's Civilization Cup 2021"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.description == "Samedo's Civilization Cup 2021 is an Age of Empires II 2v2 tournament organized by Samedo-sama."
    assert len(tournament.organizers) == 1
    assert tournament.organizers[0] == "Samedo-sama"
    assert tournament.game_mode == "Random Map"
    assert tournament.format_style == "2v2, Single Elimination"
    assert tournament.team
    assert tournament.first_place == "oSetinhas & OMurchu (oSetinhas, OMurchu)"
    assert tournament.second_place == "Andorin & TheRenano (Andorin, TheRenano)"
    assert len(tournament.runners_up) == 2
    assert tournament.runners_up[0] == "Sommos & Lacrima"
    assert tournament.runners_up[1] == "Target331 & Kloerb"

def test_other_team_tournament(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[40]
    assert tournament.name == "AoE4 Pro League"
    tournament.load_advanced(tournament_manager.loader)
    print(tournament.first_place)

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
    tournament = tournaments[3]
    assert tournament.name == "Ayre Masters Series II: Arabia"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.description == "The Ayre Masters Series II: Arabia is an Age of Empires II 1v1 tournament hosted by Ayre Esports. It is the third event of the Ayre Pro Tour."
    assert tournament.series == "Ayre Pro Tour"

def test_multiple_organizers(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[16]
    assert tournament.name == "Master of HyperRandom"
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.organizers) == 2
    assert tournament.organizers == ["Zetnus", "Huehuecoyotl22",]

def test_multiple_organizers_no_links(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[4]
    assert tournament.name == "Torneo Nacional Español 2021"
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.organizers) == 4

def test_second_third_place(tournament_manager):
    tournaments = tournament_manager.all()

    tournament = tournaments[33]
    assert tournament.name == "Wrang of Fire 3"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.second_place == "Enzberg - Joey the Bonqueror"

def test_load_alternate_portal():
    tournament_manager = TournamentManager(VcrLoader(), "/ageofempires/Age_of_Empires_IV/Tournaments")
    tournaments = tournament_manager.all()
    assert len(tournaments) == 91
    assert tournaments[44].name == "Secret Invitational"
    assert tournaments[44].cancelled

def test_index_out_of_range():
    tournament_manager = TournamentManager(VcrLoader(), "/ageofempires/Age_of_Empires_II/Tournaments/Pre_2020")
    tournaments = tournament_manager.all()
    tests = (
        (94, "Rusaoc Cup 30"),
        (111, "King of the Hippo 7"),
        (126, "EscapeTV Launch Event"),
    )
    for idx, name in tests:
        tournament = tournaments[idx]
        assert tournament.name == name
        tournament.load_advanced(tournament_manager.loader)

def test_participants(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[25]
    assert tournament.name == "Wandering Warriors Cup"
    tournament.load_advanced(tournament_manager.loader)

    assert len(tournament.participants) == 64
    assert tournament.participants[0] == ("ACCM", "/ageofempires/ACCM", True)
    assert tournament.participants[5] == ("Capoch", "/ageofempires/Capoch", False)
    assert tournament.participants[-1] == ("_Tomate", None, True)

def test_participants_placed(tournament_manager):
    tournaments = tournament_manager.all()

    tournament = tournaments[33]
    assert tournament.name == "Wrang of Fire 3"
    
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.participants[0] == ("ACCM", "/ageofempires/ACCM", False)
    assert tournament.participants[7] == ("Enzberg", None, True)
    assert tournament.participants[15] == ("Modri", "/ageofempires/Modri", True)

def test_brackets(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[25]
    assert tournament.name == "Wandering Warriors Cup"
    tournament.load_advanced(tournament_manager.loader)

    assert len(tournament.rounds) == 6

    assert len(tournament.rounds[0]) == 32

    match = tournament.rounds[0][5]
    assert match["played"]
    assert match["winner"] == "The_Dragonstar"
    assert match["loser"] == "Faraday"
    assert match["winner_url"] == "/ageofempires/The_Dragonstar"
    assert match["loser_url"] == "/ageofempires/Faraday"

    match = tournament.rounds[0][6]
    assert not match["played"]
    assert match["winner"] == "Liereyy"
    assert match["loser"] == "_Tomate"
    assert match["winner_url"] == "/ageofempires/Liereyy"
    assert match["loser_url"] == None


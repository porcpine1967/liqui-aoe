#!/usr/bin/env python3
from datetime import date
import pytest
from liquiaoe.managers import Tournament, TournamentManager, PlayerManager, TransferManager, MatchResultsManager
from liquiaoe.loaders import VcrLoader


@pytest.fixture
def loader():
    return VcrLoader()

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
    assert tournament.loader_prize == ""

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
    tournament = tournaments[3]

    assert tournament.tier == "B-Tier"
    assert tournament.game == "Age of Empires II"
    assert tournament.name == "Ayre Masters Series II: Arabia"
    assert tournament.url == "/ageofempires/Ayre_Masters_Series/2"
    assert tournament.start == date(2022, 4, 29)
    assert tournament.end == date(2022, 5, 1)
    assert tournament.prize == "$500"
    assert tournament.participant_count == 8
    assert not tournament.team
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
    assert not tournaments[56].team

    assert tournaments[58].first_place == "speed + dark"
    assert tournaments[58].first_place_url == None

def test_team_tournament(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[1]
    assert tournament.name == "Samedo's Civilization Cup 2021"
    assert tournament.team
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
    assert tournament.runners_up[0] == "Sommos & Lacrima (Sommos, Lacrima)"
    assert tournament.runners_up[1] == "Target331 & Kloerb (Target331, Kloerb)"
    assert len(tournament.teams) == 12
    for team in tournament.teams.values():
        assert len(team['members']) == 2

def test_other_team_tournament(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[40]
    assert tournament.name == "AoE4 Pro League"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.team
    assert tournament.rounds[0][0]['winner'] == 'Beasty_and_the_STRAELBORAAAAAS'
    assert tournament.rounds[1][0]['winner'] == 'Beasty_and_the_STRAELBORAAAAAS'
    assert tournament.rounds[2][0]['loser'] == 'Beasty_and_the_STRAELBORAAAAAS'
    assert tournament.rounds[0][1]['winner'] == 'White_Wolf_Palace'
    assert tournament.rounds[0][1]['winner_url'] == '/ageofempires/White_Wolf_Palace'
    assert tournament.rounds[0][3]['loser'] == 'Vietnam_Legends'
    assert tournament.rounds[0][3]['loser_url'] == '/ageofempires/Vietnam_Legends'

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
    assert tournament.placements["Bl4ck"][0] == "3rd-4th"
    assert tournament.placements["Redlash"][0] == "3rd-4th"
    assert tournament.placements["Monoz"][0] == "5th-8th"
    assert tournament.placements["Marty"][0] == "9th-16th"


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

def test_load_alternate_portal(loader):
    tournament_manager = TournamentManager(loader, "/ageofempires/Age_of_Empires_IV/Tournaments")
    tournaments = tournament_manager.all()
    assert len(tournaments) == 91
    assert tournaments[44].name == "Secret Invitational"
    assert tournaments[44].cancelled

def test_index_out_of_range(loader):
    tournament_manager = TournamentManager(loader, "/ageofempires/Age_of_Empires_II/Tournaments/Pre_2020")
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

def test_participants_wwc(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[25]
    assert tournament.name == "Wandering Warriors Cup"
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.first_place
    assert len(tournament.participants) == 64
    assert tournament.participants[0] == ("ACCM", "/ageofempires/ACCM", '9th-16th', '$500',)
    assert tournament.participants[5] == ("Capoch", "/ageofempires/Capoch", '5th-8th', '$812.50',)
    assert tournament.participants[-1] == ("Tomate", None, '33rd-64th', '',)
    for name, url, _, _ in tournament.participants:
        try:
            url_name = url.split('/')[-1]
            assert url_name == name
        except AttributeError:
            pass

def test_participants_placed(tournament_manager):
    tournaments = tournament_manager.all()

    tournament = tournaments[33]
    assert tournament.name == "Wrang of Fire 3"

    tournament.load_advanced(tournament_manager.loader)
    assert tournament.participants[0] == ("ACCM", "/ageofempires/ACCM", False, '')
    assert tournament.participants[7] == ("Enzberg", None, '2nd-3rd', '$750',)
    assert tournament.participants[15] == ("Modri", "/ageofempires/Modri", '4th-9th', '$200',)

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
    assert match["loser"] == "Tomate"
    assert match["winner_url"] == "/ageofempires/Liereyy"
    assert match["loser_url"] == None

    match = tournament.rounds[1][0]
    assert match["played"]
    assert match["winner"] == "Villese"
    assert match["loser"] == "Overtaken"
    assert match["winner_url"] == "/ageofempires/Villese"
    assert match["loser_url"] == "/ageofempires/Overtaken"

    start = 32
    for round_ in tournament.rounds:
        assert len(round_) == start
        start = start / 2

def test_from_page(loader):
    tournament = Tournament("/ageofempires/Wandering_Warriors_Cup")
    tournament.load_advanced(loader)

    assert tournament.start == date(2022, 1, 8)
    assert tournament.end == date(2022, 2, 6)

    tournament = Tournament("/ageofempires/Aorus_League/3")
    tournament.load_advanced(loader)

def test_second_third_bracket(loader):
    tournament = Tournament('/ageofempires/History_Hit_Open')
    tournament.load_advanced(loader)
    start = 32
    for round_ in tournament.rounds:
        assert len(round_) == start
        start = start / 2
def test_kotd_brackets(loader):
    tournament = Tournament('/ageofempires/King_of_the_Desert/4')
    tournament.load_advanced(loader)
    assert len(tournament.rounds) == 3

def test_transfers(loader):
    manager = TransferManager(loader)
    assert len(manager.transfers) == 30
    transfer = manager.transfers[0]
    assert transfer.date == date(2022, 1, 31)
    assert len(transfer.players) == 1
    assert transfer.players[0] == ('Deimos', None,)
    assert transfer.old == None
    assert transfer.new == 'Genesis Gaming'
    assert transfer.ref == 'https://twitter.com/xGenesisGamingx/status/1488098840146333698'
    transfer = manager.transfers[0]
    assert transfer.date == date(2022, 1, 31)
    player = transfer.players[0]
    assert player == ('Deimos', None,)
    assert transfer.old == None
    assert transfer.new == 'Genesis Gaming'
    assert transfer.ref == 'https://twitter.com/xGenesisGamingx/status/1488098840146333698'
    # multiple players
    transfer = manager.transfers[9]
    assert len(transfer.players) == 5
    player = transfer.players[0]
    assert player == ('Bee', '/ageofempires/Bee',)
    assert transfer.ref == 'https://twitter.com/3Dclanru/status/1475845997037297669'
    # transfer to-from
    transfer = manager.transfers[11]
    assert len(transfer.players) == 1
    assert transfer.players[0][0] == 'Snapy'
    assert transfer.old == 'RoxStyle'
    assert transfer.new == 'ORUX'
    assert transfer.ref == None
    # transfer from
    transfer = manager.transfers[2]
    assert len(transfer.players) == 1
    assert transfer.players[0][0] == 'The_Dragonstar'
    assert transfer.old == 'Dark Empire'
    assert transfer.new == None

def test_recent_transfers(loader):
    manager = TransferManager(loader)
    assert len(manager.recent_transfers()) == 0
    transfers = manager.recent_transfers(date(2022, 1, 13))
    assert len(transfers) == 3
    expected = ('HG Canopy', 'The_Dragonstar', 'Kasva',)
    for idx, transfer in enumerate(transfers):
        assert len(transfer.players) == 1
        assert transfer.players[0][0] == expected[idx]

def test_wtv(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[27]
    assert tournament.name == 'New Year – Cup'
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.participants) == 32

def test_missing_prizepool_table(loader):
    tournament = Tournament("/ageofempires/Regicide_Rumble/4")
    tournament.load_advanced(loader)

def test_no_category_url(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = tournaments[29]
    assert tournament.url == "/ageofempires/HunLeague:_Gold"
    assert not tournament.first_place_url
    tournament.load_advanced(tournament_manager.loader)
    assert not tournament.first_place_url

def test_no_start(loader):
    tournament = Tournament('/ageofempires/Rusaoc_Cup/77')
    tournament.load_advanced(loader)
    assert tournament.start

def test_participant_link(loader):
    tournament = Tournament('/ageofempires/Only_Land_French_Cup')
    tournament.load_advanced(loader)
    assert tournament.start

def test_dnp(loader):
    tournament = Tournament('/ageofempires/Empire_Wars_Duo/2')
    tournament.load_advanced(loader)
    team = tournament.teams['GamerLegion_B']
    assert len(team['members']) == 2

def test_match_results(loader):
    manager = MatchResultsManager(loader)
    assert len(manager.match_results) == 50
    result = manager.match_results[0]
    assert result.winner == 'JorDan_AoE'
    assert result.loser == 'Daniel'
    assert result.date == date(2022, 3, 16)
    assert result.tournament == '/ageofempires/Deep_Waters_Gaming/Pro_League/2'

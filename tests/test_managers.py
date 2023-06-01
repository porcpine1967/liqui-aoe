#!/usr/bin/env python3
from collections import Counter
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
    tournament = tournaments[68]
    tournament.load_advanced(player_manager.loader)
    assert tournament.name == "Winter Championship"
    assert tournament.tier == "S-Tier"
    assert tournament.game == "Age of Empires IV"
    assert tournament.url == "/ageofempires/Winter_Championship/AoE4/2022"
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
    assert len(tournaments) == 286
    tournament = tournaments[67]

    assert tournament.name == "GamerLegion vs White Wolf Palace (6)"
    assert tournament.end == date(2022, 1, 24)
    assert tournament.tier == "Showmatch"
    assert tournament.loader_prize == "$320"
    assert tournament.team
    assert tournament.game == "Age of Empires II"
    assert tournament.url == "/ageofempires/GamerLegion_vs_White_Wolf_Palace/6"
    assert tournament.loader_place == "2nd"

    tournament = tournaments[68]

    assert tournament.name == "Winter Championship"
    assert tournament.end == date(2022, 1, 23)
    assert tournament.tier == "S-Tier"
    assert tournament.loader_prize == "$1,500"
    assert not tournament.team
    assert tournament.game == "Age of Empires IV"
    assert tournament.url == "/ageofempires/Winter_Championship/AoE4/2022"
    assert tournament.loader_place == "3rd\xa0-\xa04th"

def test_trundo(player_manager):
    trundo_url = "/ageofempires/index.php?title=Trundo&action=edit&redlink=1"

    tournaments = player_manager.tournaments(trundo_url)
    assert len(tournaments) == 0

def test_load_from_player_main_page(player_manager):
    kongensgade_url = "/ageofempires/Kongensgade"
    tournaments = player_manager.tournaments(kongensgade_url)
    assert len(tournaments) == 45
    tournament = tournaments[-1]
    assert tournament.name == "The Medieval Wars 2013"
    assert tournament.loader_place == "17th\xa0-\xa032nd"
    assert tournament.loader_prize == ""

def test_completed(tournament_manager):
    """ Tests tournament filter."""
    timebox = (date(2023, 5, 25), date(2023, 5, 31),)
    completed_tournaments = tournament_manager.completed(timebox)
    assert len(completed_tournaments["Age of Empires II"]) == 3
    assert len(completed_tournaments["Age of Empires IV"]) == 5
    assert len(completed_tournaments["Age of Empires I"]) == 1
    assert len(completed_tournaments["Age of Mythology"]) == 1

def test_starting(tournament_manager):
    """ Tests tournament filter."""
    timebox = (date(2023, 5, 25), date(2023, 5, 31),)
    starting_tournaments = tournament_manager.starting(timebox)
    assert len(starting_tournaments["Age of Empires II"]) == 5
    assert len(starting_tournaments["Age of Empires IV"]) == 5
    assert len(starting_tournaments["Age of Empires I"]) == 1
    assert len(starting_tournaments["Age of Mythology"]) == 2

def test_ending(tournament_manager):
    """ Tests tournament filter."""
    timebox = (date(2023, 5, 25), date(2023, 5, 31),)
    ending_tournaments = tournament_manager.ending(timebox)
    assert len(ending_tournaments["Age of Empires II"]) == 2
    assert len(ending_tournaments["Age of Empires IV"]) == 2
    assert len(ending_tournaments["Age of Empires I"]) == 0
    assert len(ending_tournaments["Age of Mythology"]) == 1

def test_ongoing(tournament_manager):
    """ Tests tournament filter."""
    timebox = (date(2023, 5, 25), date(2023, 5, 31),)
    ongoing_tournaments = tournament_manager.ongoing(timebox)

    ctr = Counter()
    assert len(ongoing_tournaments["Age of Empires II"]) == 10
    assert len(ongoing_tournaments["Age of Empires IV"]) == 0
    assert len(ongoing_tournaments["Age of Empires I"]) == 2
    assert len(ongoing_tournaments["Age of Mythology"]) == 2

def test_tournaments(tournament_manager):
    """Make sure tournament manager loads tournaments correctly."""
    assert len(tournament_manager.all()) == 75
    tournaments = tournament_manager.all()
    tournament = tournaments[5]

    assert tournament.tier == "B-Tier"
    assert tournament.game == "Age of Mythology"
    assert tournament.name == "AoM EE DM Revival Cup #1"
    assert tournament.url == "/ageofempires/Meta_Plays/Age_of_Mythology/DM_Revival_Cup/1"
    assert tournament.start == date(2023, 5, 26)
    assert tournament.end == date(2023, 8, 7)
    assert tournament.prize == "$100"
    assert tournament.participant_count == 18
    assert not tournament.team
    assert not tournament.cancelled
    assert tournament.first_place == None
    assert tournament.second_place == None

    assert tournaments[6].end == date(2023, 7, 30)
    # no cross-year tournaments available to test
    # assert tournaments[16].start == date(2021, 12, 13)
    # assert tournaments[16].end == date(2022, 2, 20)
    assert tournaments[9].start == tournaments[9].end == date(2023, 7, 22)

    assert tournaments[51].first_place == "OLADUSHEK"
    assert tournaments[51].first_place_url == "/ageofempires/OLADUSHEK"
    assert tournaments[51].second_place == "element00"
    assert not tournaments[51].team

    assert tournaments[43].first_place == "Fenix"
    assert tournaments[43].first_place_url == None

def test_team_tournament(tournament_manager):
    tournament = Tournament("/ageofempires/Samedo%27s_Civilization_Cup_2021")
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.description == "Samedo's Civilization Cup 2021 is an Age of Empires II 2v2 tournament organized by SAMEDO."
    assert len(tournament.organizers) == 1
    assert tournament.organizers[0] == "SAMEDO"
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
    tournament = Tournament("ageofempires/AoE4_Pro_League")
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.team
    assert tournament.rounds[0][0].winner == 'Beasty_and_the_STRAELBORAAAAAS'
    assert tournament.rounds[1][0].winner == 'Beasty_and_the_STRAELBORAAAAAS'
    assert tournament.rounds[2][0].loser == 'Beasty_and_the_STRAELBORAAAAAS'
    assert tournament.rounds[0][1].winner == 'White_Wolf_Palace'
    assert tournament.rounds[0][1].winner_url == '/ageofempires/White_Wolf_Palace'
    assert tournament.rounds[0][3].loser == 'Vietnam_Legends'
    assert tournament.rounds[0][3].loser_url == '/ageofempires/Vietnam_Legends'

def test_simple_tournament(tournament_manager):
    tournament = Tournament("/ageofempires/King_of_the_African_Clearing")
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
    tournament = Tournament("/ageofempires/PinG_Communities")
    tournament.load_advanced(tournament_manager.loader)
    assert not tournament.team
    assert len(tournament.runners_up) == 2
    assert tournament.runners_up == ["Good_Game","Vitolio"]

def test_series_tournament(tournament_manager):
    tournament = Tournament("/ageofempires/Ayre_Masters_Series/2")
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.description == "The Ayre Masters Series II: Arabia is an Age of Empires II 1v1 tournament hosted by Ayre Esports. It is the third event of the Ayre Pro Tour."
    assert tournament.series == "Ayre Pro Tour"

def test_multiple_organizers(tournament_manager):
    tournament = Tournament("/ageofempires/Master_of_HyperRandom")
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.organizers) == 2
    assert tournament.organizers == ["Zetnus", "Huehuecoyotl22",]

def test_multiple_organizers_no_links(tournament_manager):
    tournaments = tournament_manager.all()
    tournament = Tournament("/ageofempires/Torneo_Nacional_Espa%C3%B1ol/2021")
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.organizers) == 4

def test_second_third_place(tournament_manager):
    tournament = Tournament("/ageofempires/Wrang_of_Fire/3")
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.second_place == "Enzberg - Joey the Bonqueror"

def test_load_alternate_portal(loader):
    tournament_manager = TournamentManager(loader, "/ageofempires/Age_of_Empires_IV/Tournaments")
    tournaments = tournament_manager.all()
    assert len(tournaments) == 366
    assert tournaments[11].name == "Rising Empires League - Promotion Play-in"
    assert tournaments[11].cancelled

def test_index_out_of_range(loader):
    tournament_manager = TournamentManager(loader, "/ageofempires/Age_of_Empires_II/Tournaments/Pre_2020")
    tournaments = tournament_manager.all()
    tests = (
        (98, "Rusaoc Cup 30"),
        (115, "King of the Hippo 7"),
        (129, "EscapeTV Launch Event"),
    )
    for idx, name in tests:
        tournament = tournaments[idx]
        assert tournament.name == name
        tournament.load_advanced(tournament_manager.loader)

def test_participants_wwc(tournament_manager):
    tournament = Tournament("/ageofempires/Wandering_Warriors_Cup")
    tournament.load_advanced(tournament_manager.loader)
    assert tournament.first_place
    assert len(tournament.participants) == 64
    assert tournament.participants[0] == ("ACCM", "/ageofempires/ACCM", '9th-16th', '$500',)
    assert tournament.participants[5] == ("Capoch", "/ageofempires/Capoch", '5th-8th', '$812.50',)
    assert tournament.participants[24] == ("GodOfTheGodless", None, '33rd-64th', '',)
    for name, url, _, _ in tournament.participants:
        try:
            url_name = url.split('/')[-1]
            assert url_name == name
        except AttributeError:
            pass

def test_participants_placed(tournament_manager):
    tournament = Tournament("/ageofempires/Wrang_of_Fire/3")

    tournament.load_advanced(tournament_manager.loader)
    
    assert tournament.participants[0] == ("ACCM", "/ageofempires/ACCM", False, '')
    assert tournament.participants[8] == ("Enzberg", None, '2nd-3rd', '$750',)
    assert tournament.participants[16] == ("Modri", "/ageofempires/Modri", '4th-9th', '$200',)

def test_brackets(tournament_manager):
    tournament = Tournament("/ageofempires/Wandering_Warriors_Cup")
    tournament.load_advanced(tournament_manager.loader)

    assert len(tournament.rounds) == 6

    assert len(tournament.rounds[0]) == 32

    match = tournament.rounds[0][5]
    assert match.played
    assert match.winner == "The_Dragonstar"
    assert match.loser == "Faraday"
    assert match.winner_url == "/ageofempires/The_Dragonstar"
    assert match.loser_url == "/ageofempires/Faraday"

    match = tournament.rounds[0][6]
    assert not match.played
    assert match.winner == "Liereyy"
    assert match.loser == "Tomate"
    assert match.winner_url == "/ageofempires/Liereyy"
    assert match.loser_url == "/ageofempires/Tomate"

    match = tournament.rounds[0][11]
    assert match.played
    assert match.winner == "Dark"
    assert match.loser == "GodOfTheGodless"
    assert match.winner_url == "/ageofempires/Dark"
    assert match.loser_url == None

    match = tournament.rounds[1][0]
    assert match.played
    assert match.winner == "Villese"
    assert match.loser == "Overtaken"
    assert match.winner_url == "/ageofempires/Villese"
    assert match.loser_url == "/ageofempires/Overtaken"

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
    # transfer from
    manager = TransferManager(loader)
    assert len(manager.transfers) == 30
    transfer = manager.transfers[0]
    assert transfer.date == date(2023, 5, 26)
    assert len(transfer.players) == 1
    assert transfer.players[0] == ('Tcherno', None,)
    assert transfer.old == 'Fox'
    assert transfer.new == None
    assert transfer.ref == None
    # multiple players
    transfer = manager.transfers[8]
    assert len(transfer.players) == 4
    player = transfer.players[0]
    assert player == ('Cyclops', '/ageofempires/Cyclops',)
    assert transfer.ref == None
    # transfer to-from
    transfer = manager.transfers[14]
    assert len(transfer.players) == 1
    assert transfer.players[0][0] == 'U98'
    assert transfer.old == 'Team EGO'
    assert transfer.new == 'Vitamin Coolmate'
    assert transfer.ref == 'https://chimsedinang.com/don-vi-dung-sau-clan-moi-cua-aoe-viet-la-ai/'
    # transfer to
    transfer = manager.transfers[12]
    assert len(transfer.players) == 1
    assert transfer.players[0] == ('Kondor', None,)
    assert transfer.old == None
    assert transfer.new == 'HOWL Esports'

def test_recent_transfers(loader):
    manager = TransferManager(loader)
    transfers = manager.recent_transfers(date(2023, 4, 21))
    assert len(transfers) == 3
    expected = ('BL4CK', 'FlyLikeDjango', 'Lucho',)
    for idx, transfer in enumerate(transfers):
        assert len(transfer.players) == 1
        assert transfer.players[0][0] == expected[idx]

def test_wtv(tournament_manager):
    tournament = Tournament('/ageofempires/New_Year_%E2%80%93_Cup')
    tournament.load_advanced(tournament_manager.loader)
    assert len(tournament.participants) == 32

def test_missing_prizepool_table(loader):
    tournament = Tournament("/ageofempires/Regicide_Rumble/4")
    tournament.load_advanced(loader)

def test_no_category_url(tournament_manager):
    tournament = Tournament("/ageofempires/House_of_Cancer")
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
    team = tournament.teams['GamerLegion B']
    assert len(team['members']) == 2

def test_match_results(loader):
    manager = MatchResultsManager(loader)
    assert len(manager.match_results) == 49
    result = manager.match_results[0]
    assert result.winner == 'JorDan_AoE'
    assert result.loser == 'Prydz'
    assert result.date == date(2023, 5, 31)
    assert result.tournament == '/ageofempires/Masters_of_Arena/7/Qualifier'

    result = manager.match_results[2]
    assert result.winner == 'Yo'
    assert result.loser == 'Kelar'

    result = manager.match_results[3]
    assert result.loser == 'Chirris'

def test_team_node(loader):
    tournament = Tournament('/ageofempires/Copa_Wallace')
    tournament.load_advanced(loader)
    assert len(tournament.teams) == 8

def test_double_elimination(loader):
    tournament = Tournament("/ageofempires/Master_of_HyperRandom")
    tournament.load_advanced(loader)
    assert len(tournament.matches) == 78
    matches = tournament.matches
    assert matches[0].winner == 'Villese'
    assert matches[0].loser == 'Rey_Fer'
    assert matches[0].date == date(2021, 12, 22)
    assert matches[-1].winner == 'Villese'
    assert matches[-1].loser == 'TaToH'
    assert matches[-1].date == date(2022, 2, 17)

def test_group(loader):
    tournament = Tournament("/ageofempires/The_Resurgence")
    tournament.load_advanced(loader)
    assert len(tournament.matches) == 27
    match = tournament.matches[7]
    assert match.winner == 'Yo'
    assert match.winner_url == '/ageofempires/Yo'
    assert match.loser == 'Miguel'
    assert match.loser_url == '/ageofempires/Miguel'
    assert match.date == date(2022, 5, 7)

def test_no_infobox_tournament(loader):
    tournament = Tournament('/ageofempires/Golden_League/Round/1')
    tournament.load_advanced(loader)

def test_subtournament_yaml(loader):
    manager = TournamentManager(loader)
    manager.load_extra('tests/data/subtournament.yaml')
    assert len(manager.all()) == 76
    tournament = manager.all()[-1]
    assert tournament.url == '/ageofempires/MFO_AOC_Tourney'
    assert tournament.extra
    tournament.load_advanced(loader)
    assert tournament.sponsors[0] == "Almojo"

def test_team_tbd(loader):
    tournament = Tournament('/ageofempires/Terra_Nova_Duos')
    tournament.load_advanced(loader)
    assert len(tournament.teams) == 24

def test_winner_name(loader):
    bracket_offset = 16
    expected_winners = (
        'TaToH',
        'Capoch',
        'TaToH',
        'BadBoy',
        'Capoch',
        'Hera',
        'The_Dragonstar',
        'Hera',
        'Vivi',
        'Vivi',
        'Yo',
    )
    tournament = Tournament('/ageofempires/Only_Land_Cup')
    tournament.load_advanced(loader)
    for idx, winner in enumerate(expected_winners):
        assert tournament.matches[idx + bracket_offset].winner == winner

def test_match_score(loader):
    tournament = Tournament('/ageofempires/Only_Land_Cup')
    tournament.load_advanced(loader)
    match = tournament.matches[17]
    assert match.winner == 'Capoch'
    assert match.loser == 'BadBoy'
    assert match.score == '2-1'

    tournament = Tournament('/ageofempires/Aorus_League/3')
    tournament.load_advanced(loader)
    match = tournament.matches[0]
    assert match.winner == 'Nicov'
    assert match.loser == 'Monoz'
    assert match.score == '2-0'

    match = tournament.matches[6]
    assert match.winner == 'TaToH'
    assert match.loser == 'Nicov'
    assert match.score == 'Forfeit'

def test_participants_JMB(loader):
    tournament = Tournament('/ageofempires/JorDan%27s_Medieval_Brawl/Season_1/Finals')
    tournament.load_advanced(loader)
    assert len(tournament.participants) == 8

def test_golden_league_finals(loader):
    tournament = Tournament('/ageofempires/Golden_League/1')
    tournament.load_advanced(loader)
    assert len(tournament.participants) == 64
    for name, url, placement, prize in tournament.participants:
        if name == 'MarineLorD':
            assert placement == '1st'
            assert prize == '$36,250'

def test_match_date(loader):
    tournament = Tournament('/ageofempires/T90_Titans_League/1/Gold_League')
    tournament.load_advanced(loader)
    for match in tournament.matches:
        if match.winner and match.loser:
            assert match.date or match.score == 'Forfeit'

def test_player_matches(loader):
    manager = PlayerManager(loader)
    matches = manager.matches('/ageofempires/JorDan_AoE')
    match = matches[58]
    assert match.end == date(2022, 7, 29)
    assert match.tier == 'S-Tier'
    assert match.game == 'Age of Empires II'
    assert match.tournament_name == 'T90 Titans League: Platinum League'
    assert match.tournament_url == '/ageofempires/T90_Titans_League/1/Platinum_League'
    assert match.played
    match = matches[116]
    assert match.end == date(2022, 1, 4)
    assert match.tier == 'A-Tier'
    assert match.game == 'Age of Empires IV'
    assert match.tournament_name == 'Winter Series 2'
    assert match.tournament_url == '/ageofempires/Winter_Series/2'
    assert not match.played
    assert not matches[270].played

def test_prize_pool_div(loader):
    tournament = Tournament('/ageofempires/Death_Match_World_Cup/5/Qualifier')
    tournament.load_advanced(loader)
    assert len(tournament.matches) == 24


def test_exclude_tbd_from_multiple_participants(loader):
    # just no null pointer
    tournament = Tournament('/ageofempires/AoE2_Admirals_League/2')
    tournament.load_advanced(loader)
    placed = [x for x in tournament.placements.values() if x]
    assert len(placed) == 9


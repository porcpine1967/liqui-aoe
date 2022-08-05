#!/usr/bin/env python3
""" Everything you want to know about Age of Empires Tournaments."""
from collections import defaultdict
from datetime import date, datetime, timedelta
import re

import bs4
import yaml

PARTICIPANTS = re.compile(r"([0-9]+)")
TEAM_PATTERN = re.compile(r"(2v2|3v3|4v4)")
INTEGER = re.compile(r"^[0-9]+$")

from liquiaoe.loaders import RequestsException


class TournamentManager:
    def __init__(self, loader, url="/ageofempires/Portal:Tournaments"):
        self._tournaments = []
        self.url = url
        self.loader = loader
        self.load()

    def completed(self, timebox):
        """Makes sure the end_date is between the dates (inclusive)."""
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if timebox[0] <= tournament.end <= timebox[1]:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def ending(self, timebox):
        """Makes sure the tournament starts before (exclusive) and ends within (inclusive) timebox."""
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if tournament.start < timebox[0] <= tournament.end <= timebox[1]:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def ongoing(self, timebox):
        """Makes sure the tournament starts before and ends after timebox (exclusive)."""
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if tournament.start < timebox[0] and tournament.end > timebox[1]:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def starting(self, timebox):
        """Makes sure the start date is between the dates (inclusive)."""
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if timebox[0] <= tournament.start <= timebox[1]:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def all(self):
        """Returns information on all tournaments."""
        return self._tournaments

    def load(self):
        """Parses information in loader and adds to _tournaments."""
        data = self.loader.soup(self.url)

        start = node_from_class(data, "tournament-card")
        loaded = set()
        while start:
            if not class_in_node("tournament-card", start):
                start = start.next_sibling
                continue

            rows = start.find_all("div")
            for row in rows:
                if class_in_node("divRow", row):
                    tournament = Tournament()
                    tournament.load_from_portal(row)
                    if tournament.url in loaded:
                        continue
                    loaded.add(tournament.url)
                    if not tournament.tier:
                        break
                    self._tournaments.append(tournament)
            start = start.next_sibling
    def load_extra(self, filepath):
        """ load yaml from filepath and add extra tournaments to manager"""
        with open(filepath) as f:
            data = yaml.safe_load(f)
        for tournament_data in data:
            tournament = Tournament(tournament_data['url'], extra=True)
            tournament.name = tournament_data['name']
            tournament.start = tournament_data['start']
            tournament.end = tournament_data['end']
            tournament.game = tournament_data['game']
            tournament.tier = tournament_data['tier']
            tournament.prize = str(tournament_data['prize'])
            self._tournaments.append(tournament)

def class_in_node(css_class, node):
    try:
        return css_class in node.attrs["class"]
    except (AttributeError, KeyError):
        return False


def class_starts_with(css_class, node):
    try:
        for attr in node.attrs["class"]:
            if attr.startswith(css_class):
                return True
    except (AttributeError, KeyError):
        pass
    return False


def liquipedia_key(anchor_tag):
    """returns key name for player used in path or as title for missing page"""
    href = anchor_tag.attrs["href"]
    if "redlink" in href:
        _, attrs = href.split("?")
        for attr_pair in attrs.split("&"):
            if attr_pair.startswith("title="):
                return attr_pair[6:]
    else:
        return href.split("/")[-1]


def valid_href(anchor_tag):
    href = anchor_tag.attrs["href"]
    return None if "redlink" in href else href


def node_from_class(ancestor, class_attribute):
    for node in ancestor.descendants:
        if class_in_node(class_attribute, node):
            return node
    raise ParserError("{} missing".format(class_attribute))


def text_from_tag(parent, tag):
    divs = parent.find_all(tag)
    return divs[-1].text.strip()


def div_attributes(parent):
    divs = parent.find_all("div")
    attributes = list()

    for div in divs[1:]:
        for string in div.stripped_strings:
            attributes.append(string)
    return attributes


def next_tag(first_tag):
    sibling = first_tag.next_sibling
    while sibling:
        if isinstance(sibling, bs4.element.Tag):
            return sibling
        sibling = sibling.next_sibling
    return None


class Tournament:
    def __init__(self, url="", extra=False):
        self.url = url
        self.extra = extra
        # Basic attributes (loaded from tournaments page)
        self.name = self.game = self.tier = self.prize = self.loader_prize = ""
        self.start = (
            self.end
        ) = self.first_place = self.first_place_url = self.second_place = None
        self.loader_place = None
        self.participant_count = -1
        self.cancelled = False
        self.series = None
        # Advanced (loaded from tournament page)
        self.loaded = False
        self.participant_lookup = {}
        self.organizers = []
        self.sponsors = []
        self.game_mode = None
        self.format_style = None
        self.description = None
        self.team = False
        self.runners_up = []
        self.rounds = []
        self.teams = {}
        self.placements = defaultdict(str)
        self.matches = []

    def __str__(self):
        return self.name

    @property
    def participants(self):
        return sorted(self.participant_lookup.values())
    def load_from_player(self, row):
        """Adds attributes from player_row."""
        tds = row.find_all("td")
        self.end = datetime.strptime(tds[0].text, "%Y-%m-%d").date()
        self.loader_place = tds[1].font.text
        self.tier = tds[2].a.text
        self.team = tds[3].text.lower() == "team"
        self.game = tds[4].span.a.attrs["title"]
        self.name = tds[5].text
        self.url = tds[6].a.attrs["href"]
        self.loader_prize = tds[10].text.strip()

    def load_advanced(self, loader):
        """Call the loader for self.url and parse."""
        if self.loaded:
            return
        self.loaded = True
        soup = loader.soup(self.url)
        main = node_from_class(soup, "mw-parser-output")
        if not main:
            raise ParserError("No mw-parser-output in soup")
        try:
            self.description = main.p.text.strip()
        except AttributeError:
            self.description = ""
        try:
            self.load_info_box(node_from_class(main, "fo-nttax-infobox"))
        except ParserError:
            pass
        try:
            for prize_table in soup.find_all('table', {'class': 'prizepooltable'}):
                try:
                    node_from_class(prize_table, 'background-color-first-place')
                    break
                except ParserError:
                    continue
            else:
                return
            self.load_participants(main, prize_table)
            self.load_matches(main)
            brackets = []
            for div in main.find_all("div"):
                if class_in_node("bracket", div):
                    brackets.append(div)
            if brackets:
                self.load_bracket(brackets[-1])
        except ParserError:
            pass

    def load_matches(self, page):
        for match_node in page.find_all("div", recursive=True):
            if class_in_node("bracket-game", match_node):
                match = MatchResult(match_node, self)
                if match.winner and match.loser:
                    self.matches.append(match)

        for table_node in page.find_all("table", recursive=True):
            if class_in_node("matchlist", table_node):
                for match_node in table_node.find_all("tr"):
                    if class_in_node("match-row", match_node):
                        match = MatchResult(match_node, self)
                        if match.winner and match.loser:
                            self.matches.append(match)

    def load_bracket(self, node):
        for bracket_round in node.find_all("div"):
            if class_in_node("bracket-column-matches", bracket_round):
                self.load_round(bracket_round)
        try:
            if len(self.rounds[-1]) == len(self.rounds[-2]):
                self.rounds[-1].pop()
        except IndexError:
            pass

    def load_round(self, node):
        matches = []
        for match in node.find_all("div"):
            if class_in_node("bracket-game", match):
                matches.append(MatchResult(match, self))
        self.rounds.append(matches)

    def load_participants(self, node, prize_table):
        for h2 in node.find_all("h2", recursive=True):
            if "Participants" in h2.text:
                break
        else:
            return
        participant_node = h2
        while participant_node.name != "div":
            participant_node = next_tag(participant_node)

        if self.team:
            team_nodes = next_tag(participant_node)
            for node in team_nodes.find_all("div"):
                if class_in_node("template-box", node):
                    team_info = self.team_info(node)
                    if team_info:
                        self.teams[team_info["name"]] = team_info

        if not self.placements:
            self.load_all_places(prize_table)
        if self.team:
            return
        player_row = None
        while participant_node and not player_row:
            try:
                player_row = node_from_class(participant_node, "player-row")
            except ParserError:
                participant_node = next_tag(participant_node)                
        while player_row:
            for td in player_row.find_all("td"):
                if not td.text or not td.span or "TBD" in td.text:
                    continue
                span = td.find_all("span")[1]
                name = liquipedia_key(span.a)
                href = valid_href(span.a)
                data = self.placements[name] or (
                    False,
                    "",
                )
                self.participant_lookup[span.a.text] = (name, href, *data)
            player_row = next_tag(player_row)

    def team_name_from_node(self, node, column_index):
        columns = node.find_all("td")
        links = columns[column_index].find_all("a")
        team_name = links[-1].text
        try:
            team = self.teams[team_name]
            members = [x[0] for x in team["members"]]
            return "{} ({})".format(team["name"], ", ".join(members))
        except (IndexError, ParserError, KeyError):
            return team_name

    def team_info(self, node):
        team_node = node_from_class(node, "teamcard")
        team_dict = dict()
        team_dict["name"] = team_node.center.text
        if team_dict['name'] == 'TBD':
            return
        team_dict["url"] = liquipedia_key(team_node.center.a)
        team_dict["members"] = []
        for div in team_node.find_all('div'):
            if div.table:
                member_row = div.table.tr
                break
        while member_row:
            td = member_row.find_all("td")[-1]
            if not "DNP" in td.text:
                last_a = td.find_all("a")[-1]
                team_dict["members"].append(
                    (
                        td.text.strip(),
                        valid_href(last_a),
                    )
                )
            member_row = member_row.next_sibling
        return team_dict

    def load_all_places(self, prize_table):
        """Loads all places."""
        idx = self.name_column_index(prize_table)
        current_place = ""
        current_prize = ""
        places = defaultdict(list)
        for row in prize_table.find_all("tr"):
            tds = row.find_all("td")
            if not tds:
                continue
            name_idx = 0
            if "rowspan" in tds[0].attrs:
                current_place = tds[0].text.strip()
                current_prize = tds[1].text.strip()
                current_prize = "" if current_prize == "-" else current_prize
                name_idx = idx
            if "TBD" in tds[name_idx].text:
                continue
            links = tds[name_idx].find_all("a")
            if not links:
                continue
            name = links[-1].text.strip()
            if self.team:
                name = self.team_name_from_node(row, name_idx)
            self.placements[liquipedia_key(links[-1])] = (
                current_place,
                current_prize,
            )
            if current_place.startswith("1st"):
                places[1] = [
                    name,
                    valid_href(links[-1]),
                ]
            elif current_place.startswith("2nd"):
                places[2].append(name)
            elif current_place.startswith("3rd"):
                places[3].append(name)
            elif current_place == "4th":
                places[4].append(name)
        if places[1]:
            self.first_place, self.first_place_url = places[1]
        if places[2]:
            self.second_place = " - ".join(places[2])
        for place in (
            3,
            4,
        ):
            if places[place]:
                self.runners_up.append(" - ".join(places[place]))

    def name_column_index(self, node):
        """Looks at the headers to find the approiate index for the name"""
        column_header = "Team" if self.team else "Player"
        ths = node.find_all("th", recursive=True)
        for idx, th in enumerate(ths):
            if column_header in th.text:
                return idx
        # Try the other
        column_header = "Team" if not self.team else "Player"
        for idx, th in enumerate(ths):
            if column_header in th.text:
                return idx

    def load_info_box(self, info_box):
        """Parse information from info box"""
        for div in info_box.find_all("div"):
            try:
                if not self.prize and div.div.text == "Prize pool:":
                    self.prize = text_from_tag(div, "div")
                if div.div.text == "Series:":
                    self.series = text_from_tag(div, "div")
                if div.div.text in (
                    "Organizer:",
                    "Organizers:",
                ):
                    self.organizers = div_attributes(div)
                if div.div.text == "Game Mode:":
                    self.game_mode = text_from_tag(div, "div")
                if div.div.text == "Format:":
                    self.format_style = text_from_tag(div, "div")
                    if "FFA" or "1v1" in self.format_style:
                        self.team = False
                    if TEAM_PATTERN.search(self.format_style):
                        self.team = True
                if div.div.text == "Sponsor(s):":
                    self.sponsors = div_attributes(div)
                if div.div.text == "Start Date:":
                    self.start = date.fromisoformat(text_from_tag(div, "div"))
                if div.div.text == "End Date:":
                    self.end = date.fromisoformat(text_from_tag(div, "div"))
                if div.div.text == "Date:":
                    self.start = date.fromisoformat(text_from_tag(div, "div"))
                    self.end = date.fromisoformat(text_from_tag(div, "div"))
            except AttributeError:
                pass

    def load_from_portal(self, row):
        divs = row.find_all("div")
        self.load_header(divs[0])
        self.load_dates(divs[1].text)
        self.prize = divs[2].text.strip()
        self.load_participant_count(divs[3].text)
        self.first_place = self.first_place_url = self.second_place = None
        self.load_first_place_from_row(divs[5])
        if self.first_place:
            self.load_second_place(divs[6])

    def load_header(self, row):
        """Load the first five attributes."""
        self.tier = row.a.text.strip()
        spans = row.find_all("span")
        self.game = spans[0].a.attrs["title"]
        self.url = row.b.a.attrs["href"]
        self.name = row.b.text.strip()

    def load_dates(self, text):
        if " - " in text:
            start, end = text.split(" - ")
            if "," not in start:
                start += end[-6:]
            if len(end) < 9:
                end = start[:3] + " " + end
            self.start = datetime.strptime(start.strip(), "%b %d, %Y").date()
            self.end = datetime.strptime(end.strip(), "%b %d, %Y").date()
        else:
            self.start = datetime.strptime(text.strip(), "%b %d, %Y").date()
            self.end = self.start

    def load_participant_count(self, text):
        match = PARTICIPANTS.match(text)
        if match:
            self.participant_count = int(match.group(1))

    def load_first_place_from_row(self, div):
        if div.text == "Cancelled":
            self.cancelled = True
            return
        spans = div.find_all("span")
        try:
            first_place = spans[-1].text.strip()
            if not first_place or first_place == "TBD":
                return
            if class_starts_with("team", spans[-1]):
                self.team = True
            self.first_place = first_place
            self.first_place_url = valid_href(spans[-1].a)
        except (AttributeError, IndexError):
            pass

    def load_second_place(self, div):
        if div.text == "Cancelled":
            self.cancelled = True
            return
        spans = div.find_all("span")
        try:
            second_place = spans[-1].text.strip()
            if second_place and second_place != "TBD":
                self.second_place = second_place
        except (AttributeError, IndexError):
            pass


class PlayerMatch:
    def __init__(self, row):
        tds = row.find_all("td")
        self.end = datetime.strptime(tds[0].text, "%Y-%m-%d").date()
        self.tier = tds[2].a.text
        self.game = tds[3].span.a.attrs["title"]
        self.tournament_name = tds[5].text
        self.tournament_url = tds[5].a.attrs["href"]
        self.played = 'W' not in (tds[6].text, tds[8].text)
        
class PlayerManager:
    def __init__(self, loader):
        self.loader = loader

    def matches(self, player_url):
        player_matches = []
        if "index" in player_url:
            return player_matches
        url = "{}/Matches".format(player_url)
        try:
            data = self.loader.soup(url)
        except (RequestsException) as ex:
            if ex.code == 404:
                data = self.loader.soup(player_url)
            else:
                raise
        results_table = node_from_class(data, "wikitable")
        for node in results_table.descendants:
            if node.name == "tr" and len(node.find_all("td")) == 11:
                player_matches.append(PlayerMatch(node))
        
        return player_matches
        

    def tournaments(self, player_url):
        player_tournaments = []
        if "index" in player_url:
            return player_tournaments
        url = "{}/Results".format(player_url)
        try:
            data = self.loader.soup(url)
        except (RequestsException) as ex:
            if ex.code == 404:
                data = self.loader.soup(player_url)
            else:
                raise
        results_table = node_from_class(data, "wikitable")
        for node in results_table.descendants:
            if node.name == "tr" and len(node.find_all("td")) == 11:
                tournament = Tournament()
                tournament.load_from_player(node)
                player_tournaments.append(tournament)
        return player_tournaments


class TransferManager:
    PORTAL = "/ageofempires/Portal:Transfers"

    def __init__(self, loader):
        self.loader = loader
        self._transfers = []

    @property
    def transfers(self):
        if not self._transfers:
            data = self.loader.soup(self.PORTAL)
            for node in data.find_all("div"):
                if class_in_node("divRow", node):
                    self._transfers.append(Transfer(node))
        return self._transfers

    def recent_transfers(self, now=None):
        """Transfers in the past week.
        'now' for testing."""
        recent = []
        now = now or datetime.now().date()
        cutoff = now - timedelta(days=8)
        for transfer in self.transfers:
            if cutoff < transfer.date <= now:
                recent.append(transfer)
        return recent


class Transfer:
    def __init__(self, row):
        self.date = self.old = self.new = self.ref = None
        self.players = []
        self.load(row)

    def load(self, row):
        for div in row.find_all("div"):
            if class_in_node("Date", div):
                self.date = date.fromisoformat(div.text)
            if class_in_node("Name", div):
                for a in div.find_all("a"):
                    if a.text:
                        player = (
                            a.text,
                            valid_href(a),
                        )
                        self.players.append(player)
            if class_in_node("OldTeam", div):
                for a in div.find_all("a"):
                    if "title" in a.attrs:
                        self.old = a.attrs["title"]
                        break
            if class_in_node("NewTeam", div):
                for a in div.find_all("a"):
                    if "title" in a.attrs:
                        self.new = a.attrs["title"]
                        break
            if class_in_node("Ref", div):
                try:
                    self.ref = div.a.attrs["href"]
                except AttributeError:
                    pass


class MatchResultsManager:
    PORTAL = "/ageofempires/Liquipedia:Upcoming_and_ongoing_matches"

    def __init__(self, loader):
        self.loader = loader
        self._match_results = []

    @property
    def match_results(self):
        if not self._match_results:
            data = self.loader.soup(self.PORTAL)
            for node in data.find_all("table"):
                if class_in_node("infobox_matches_content", node):
                    result = MatchResult(node)
                    if result.played:
                        self._match_results.append(MatchResult(node))
        return self._match_results


class MatchResult:
    def __init__(self, node, tournament=None):
        self.winner = None
        self.loser = None
        self.winner_url = None
        self.loser_url = None
        self.date = None
        self.tournament = None
        self.played = True
        self.score = ''
        self.game = None
        if node.name == 'table':
            self._build_from_table(node)
        elif node.name == 'tr':
            self._build_from_row(node, tournament)
        else:
            self._build_from_bracket(node, tournament)
        if not self.winner:
            self.played = False

    def _build_from_row(self, node, tournament):
        """ From round-robin/swiss brackets """
        self.tournament = tournament.url
        lookup = {}
        scores = []
        for td in node.find_all('td'):
            if class_in_node('matchlistslot', td):
                if class_in_node('bg-win', td):
                    winner = td.text.strip()
                    try:
                        self.winner = tournament.participant_lookup[winner][0]
                        self.winner_url = tournament.participant_lookup[winner][1]
                    except KeyError:
                        self.winner = winner
                else:
                    loser = td.text.strip()
                    try:
                        self.loser = tournament.participant_lookup[loser][0]
                        self.loser_url = tournament.participant_lookup[loser][1]
                    except KeyError:
                        self.loser = loser
            else:
                for div in td.find_all('div'):
                    if class_in_node("bracket-popup-body-time", div):
                        self._date_from_node(div)
                try:
                    if INTEGER.match(td.contents[0]):
                        scores.append(int(td.contents[0]))
                    elif td.contents[0] in ("W", "FF"):
                        self.played = False
                        self.score = 'Forfeit'

                except AttributeError:
                    pass

        if len(scores) == 2:
            self.score = '{}-{}'.format(*sorted(scores, reverse=True))

    def _date_from_node(self, div):
        date_str = div.text.split('-')[0].strip()
        try:
            self.date = datetime.strptime(date_str, '%B %d, %Y').date()
        except ValueError:
            pass

    def _build_from_bracket(self, node, tournament):
        self.tournament = tournament.url
        scores = []
        for div in node.find_all("div"):
            if class_starts_with("bracket-cell-r", div):
                key = ""
                if tournament.team:
                    try:
                        key = div.span.attrs['data-highlightingclass']
                    except (AttributeError, KeyError):
                        continue
                else:
                    for string in div.stripped_strings:
                        key = string
                        break
                if not key or key == 'TBD':
                    continue
                try:
                    if class_in_node('bracket-player-middle', div.div):
                        continue
                    if tournament.team:
                        team = tournament.teams[key]
                        name = team['url']
                        url = "/ageofempires/{}".format(team['url'])
                    else:
                        player = tournament.participant_lookup[key]
                        name = player[0]
                        url = player[1]
                    if "font-weight:bold" == div.attrs.get("style"):
                        self.winner = name
                        self.winner_url = url
                    else:
                        self.loser = name
                        self.loser_url = url
                except KeyError:
                    if "font-weight:bold" == div.attrs.get("style"):
                        winner = key
                    else:
                        loser = key
            if class_in_node("bracket-popup-body-time", div):
                self._date_from_node(div)

            if class_in_node("bracket-score", div):
                if div.text in ("W", "FF"):
                    self.played = False
                    self.score = 'Forfeit'
                else:
                    try:
                        scores.append(int(div.text))
                    except ValueError:
                        pass
        if len(scores) == 2:
            self.score = '{}-{}'.format(*sorted(scores, reverse=True))

    def _build_from_table(self, table):
        """ From ongoing matches table"""
        rows = table.find_all("tr")
        for idx, td in enumerate(rows[0].find_all("td")):
            style = td.attrs.get("style")
            css_class = td.attrs.get("class")
            anchors = td.find_all("a")
            if not anchors:
                continue
            if idx == 0:
                name = liquipedia_key(anchors[0])
            else:
                name = liquipedia_key(anchors[-1])
            if style == "font-weight:bold;":
                self.winner = name
            else:
                self.loser = name

        match = rows[1].td
        date_str = match.span.text.split("-")[0].strip()
        self.date = datetime.strptime(date_str, "%B %d, %Y").date()
        self.tournament = valid_href(match.div.div.a)

    def __repr__(self):
        return "{} beat {} at {} at {}".format(self.winner, self.loser, self.tournament, self.date)

class ParserError(Exception):
    """What to throw if something critical missing from soup."""

#!/usr/bin/env python3
""" Everything you want to know about Age of Empires Tournaments."""
from collections import defaultdict
from datetime import date, datetime, timedelta
import re

import bs4

PARTICIPANTS = re.compile(r"([0-9]+)")

from liquiaoe.loaders import RequestsException

class TournamentManager:
    def __init__(self, loader, url="/ageofempires/Portal:Tournaments"):
        self._tournaments = []
        self.url = url
        self.loader = loader
        self.load()

    def completed(self, timebox):
        """ Makes sure the end_date is between the dates."""
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if  timebox[0] <= tournament.end <= timebox[1]:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def ongoing(self, timestamp):
        """ Makes sure the tournament starts before and ends after timestamp."""
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if  tournament.start <= timestamp <= tournament.end:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def starting(self, timebox):
        """ Makes sure the start date is between the dates."""
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if  timebox[0] <= tournament.start <= timebox[1]:
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
    """ returns key name for player used in path or as title for missing page"""
    href = anchor_tag.attrs["href"]
    if "redlink" in href:
        _, attrs = href.split('?')
        for attr_pair in attrs.split('&'):
            if attr_pair.startswith('title='):
                return attr_pair[6:]
    else:
        return href.split('/')[-1]

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
    def __init__(self, url=""):
        self.url = url
        # Basic attributes (loaded from tournaments page)
        self.name = self.game = self.tier = self.prize = self.loader_prize = ""
        self.start = self.end = self.first_place = self.first_place_url = self.second_place = None
        self.loader_place = None
        self.participant_count = -1
        self.cancelled = False
        self.series = None
        # Advanced (loaded from tournament page)
        self.participants = []
        self.organizers = []
        self.sponsors = []
        self.game_mode = None
        self.format_style = None
        self.description = None
        self.team = False
        self.runners_up = []
        self.rounds = []
        self.placements = defaultdict(str)

    def __str__(self):
        return self.name

    def load_from_player(self, row):
        """ Adds attributes from player_row."""
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
        """ Call the loader for self.url and parse."""
        soup = loader.soup(self.url)
        main = node_from_class(soup, "mw-parser-output")
        if not main:
            raise ParserError("No mw-parser-output in soup")
        try:
            self.description = main.p.text.strip()
        except AttributeError:
            self.description = ""
        self.load_info_box(node_from_class(main, "fo-nttax-infobox"))
        try:
            prize_table = node_from_class(main, "prizepooltable")
            self.load_participants(main, prize_table)
            brackets = []
            for div in main.find_all('div'):
                if class_in_node('bracket', div):
                    brackets.append(div)
            if brackets:
                self.load_bracket(brackets[-1])
        except ParserError:
            pass

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
                matches.append(self.load_match(match))
        self.rounds.append(matches)

    def load_match(self, node):
        match = {"played": True, "winner": None, "loser": None,
                 "winner_url": None, "loser_url": None,}
        players = {}
        urls = {}
        winner = ''
        loser = ''
        for div in node.find_all("div"):
            if class_starts_with("bracket-cell-r", div):
                name = ''
                for string in div.stripped_strings:
                    name = string
                    break
                if "font-weight:bold" == div.attrs.get("style"):
                    winner = name
                else:
                    loser = name
            if class_in_node("bracket-popup-header-vs-child", div):
                for a in div.find_all("a"):
                    if a.text:
                        players[a.text] = liquipedia_key(a)
                        urls[a.text] = valid_href(a)
            if class_in_node("bracket-score", div):
                if div.text in ("W", "FF"):
                    match["played"] = False
        match["winner"] = players.get(winner)
        match["loser"] = players.get(loser)
        match["winner_url"] = urls.get(winner)
        match["loser_url"] = urls.get(loser)
        return match

    def load_participants(self, node, prize_table):
        if not self.placements:
            self.load_all_places(prize_table)
        if self.team:
            return
        for h2 in node.find_all("h2", recursive=True):
            if "Participants" in h2.text:
                break
        else:
            return
        participant_node = h2
        while participant_node.name != 'div':
            participant_node = next_tag(participant_node)
        try:
            player_row = node_from_class(participant_node, "player-row")
        except ParserError:
            # nbd, just nothing there
            return
        while player_row:
            for td in player_row.find_all("td"):
                if not td.text or not td.span or 'TBD' in td.text:
                    continue
                span = td.find_all("span")[1]
                name = liquipedia_key(span.a)
                href = valid_href(span.a)
                data = self.placements[name] or (False, '',)
                self.participants.append((name, href, *data))
            player_row = next_tag(player_row)



    def team_name_from_node(self, node, column_index):
            columns = node.find_all("td")
            links = columns[column_index].find_all("a")
            team_name = links[-1].text.strip()
            try:
                members = self.team_members(team_name, node.parent.parent)
                return "{} ({})".format(team_name,
                                        ", ".join(members))
            except (IndexError, ParserError):
                return team_name

    def team_members(self, team_name, node):
        team_column = node_from_class(node.parent.parent, "template-box")

        while team_column:
            team = node_from_class(team_column, "template-box")
            while team:
                team_dict = self.team_info(team)
                if team_dict["name"] == team_name:
                    return team_dict["members"]
                team = team.next_sibling
            team_column = team_column.next_sibling
        return []

    def team_info(self, node):
        team_node = node_from_class(node, "teamcard")
        team_dict = dict()
        team_dict["name"] = team_node.center.text
        team_dict["members"] = []
        member_row = team_node.div.table.tr
        while member_row:
            tds = member_row.find_all("td")
            team_dict["members"].append(tds[-1].text.strip())
            member_row = member_row.next_sibling
        return team_dict

    def load_all_places(self, prize_table):
        """ Loads all places."""
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
                current_prize = '' if current_prize == '-' else current_prize
                name_idx = idx
            if 'TBD' in tds[name_idx].text:
                continue
            links = tds[name_idx].find_all("a")
            if not links:
                continue
            name = links[-1].text.strip()
            if self.team:
                name = self.team_name_from_node(row, name_idx)
            self.placements[liquipedia_key(links[-1])] = (current_place, current_prize,)
            if current_place.startswith('1st'):
                places[1] = [name, valid_href(links[-1]),]
            elif current_place.startswith('2nd'):
                places[2].append(name)
            elif current_place.startswith('3rd'):
                places[3].append(name)
            elif current_place == '4th':
                places[4].append(name)
        if places[1]:
            self.first_place, self.first_place_url = places[1]
        if places[2]:
            self.second_place = " - ".join(places[2])
        for place in (3,4,):
            if places[place]:
                self.runners_up.append(" - ".join(places[place]))

    def name_column_index(self, node):
        """ Looks at the headers to find the approiate index for the name"""
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
        """ Parse information from info box"""
        for div in info_box.find_all("div"):
            try:
                if not self.prize and div.div.text == "Prize pool:":
                    self.prize = text_from_tag(div, "div")
                if div.div.text == "Series:":
                    self.series = text_from_tag(div, "div")
                if div.div.text in ("Organizer:", "Organizers:",):
                    self.organizers = div_attributes(div)
                if div.div.text == "Game Mode:":
                    self.game_mode = text_from_tag(div, "div")
                if div.div.text == "Format:":
                    self.format_style = text_from_tag(div, "div")
                    if 'FFA' or '1v1' in self.format_style:
                        self.team = False
                    if "2v2" in self.format_style:
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

class PlayerManager:
    def __init__(self, loader):
        self.loader = loader

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
    PORTAL = '/ageofempires/Portal:Transfers'
    def __init__(self, loader):
        self.loader = loader
        self._transfers = []

    @property
    def transfers(self):
        if not self._transfers:
            data = self.loader.soup(self.PORTAL)
            for node in data.find_all('div'):
                if class_in_node('divRow', node):
                    self._transfers.append(Transfer(node))
        return self._transfers

    def recent_transfers(self, now=None):
        """ Transfers in the past week.
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
        for div in row.find_all('div'):
            if class_in_node('Date', div):
                self.date = date.fromisoformat(div.text)
            if class_in_node('Name', div):
                for a in div.find_all('a'):
                    if a.text:
                        player = (a.text, valid_href(a),)
                        self.players.append(player)
            if class_in_node('OldTeam', div):
                for a in div.find_all('a'):
                    if 'title' in a.attrs:
                        self.old = a.attrs['title']
                        break
            if class_in_node('NewTeam', div):
                for a in div.find_all('a'):
                    if 'title' in a.attrs:
                        self.new = a.attrs['title']
                        break
            if class_in_node('Ref', div):
                try:
                    self.ref = div.a.attrs['href']
                except AttributeError:
                    pass

class ParserError(Exception):
    """ What to throw if something critical missing from soup."""

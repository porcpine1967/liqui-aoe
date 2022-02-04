#!/usr/bin/env python3
""" Everything you want to know about Age of Empires Tournaments."""
from collections import defaultdict
from datetime import date, datetime
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
    def __init__(self):
        # Basic attributes (loaded from tournaments page)
        self.name = self.url = self.game = self.tier = self.prize = self.loader_prize = ""
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
        self.loader_prize = tds[10].text

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
        prize_table = node_from_class(main, "prizepooltable")
        if not self.first_place or self.team:
            self.load_all_places(prize_table)
        else:
            self.load_runners_up(prize_table)
        if self.first_place and not self.second_place:
            self.load_second_third(prize_table)
        self.load_participants(main, prize_table)
        try:
            self.load_bracket(node_from_class(main, "bracket"))
        except ParserError:
            pass

    def load_bracket(self, node):
        for bracket_round in node.find_all("div"):
            if class_in_node("bracket-column-matches", bracket_round):
                self.load_round(bracket_round)

    def load_round(self, node):
        matches = []
        for match in node.find_all("div"):
            if class_in_node("bracket-game", match):
                matches.append(self.load_match(match))
        self.rounds.append(matches)
        
    def load_match(self, node):
        match = {"played": True, "winner": None, "loser": None,
                 "winner_url": None, "loser_url": None,}
        urls = defaultdict(lambda: None)
        for div in node.find_all("div"):
            if class_in_node("bracket-cell-r1", div):
                key = "winner" if "font-weight:bold" == div.attrs["style"] else "loser"
                for string in div.stripped_strings:
                    match[key] = string
                    break
            if class_in_node("bracket-popup-header-vs-child", div):
                for a in div.find_all("a"):
                    urls[a.text] = valid_href(a)
            if class_in_node("bracket-score", div):
                if div.text in ("W", "FF"):
                    match["played"] = False

        match["winner_url"] = urls[match["winner"]]
        match["loser_url"] = urls[match["loser"]]
        return match
    def load_participants(self, node, prize_table):
        placers = prize_table.text
        if self.team:
            return
        found = False
        for h2 in node.find_all("h2", recursive=True):
            if "Participants" in h2.text:
                found = True
                break
        if not found:
            return
        participant_node = next_tag(h2)
        try:
            player_row = node_from_class(participant_node, "player-row")
        except ParserError:
            # nbd, just nothing there
            return
        while player_row:
            for td in player_row.find_all("td"):
                if not td.text:
                    continue
                span = td.find_all("span")[1]
                name = span.a.text
                href = valid_href(span.a)
                self.participants.append((name, href, name in placers))
            player_row = next_tag(player_row)

    def load_all_places(self, prize_table):
        idx = self.name_column_index(prize_table)
        first = node_from_class(prize_table, "background-color-first-place")
        if "TBD" in first.text:
            """ Don't bother if the results aren't in."""
            return
        first_columns = first.find_all("td")
        links = first_columns[idx].find_all("a")
        if self.team:
            first_place = links[-1].text.strip()
            self.first_place = self.team_name_from_node(first, idx)
            try:
                second = node_from_class(prize_table, "background-color-second-place")
                self.second_place = self.team_name_from_node(second, idx)
            except (IndexError, ParserError):
                pass

        else:
            self.first_place = links[-1].text.strip()
            self.first_place_url = valid_href(links[-1])
            self.load_second_third(prize_table)
        self.load_runners_up(prize_table)

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

    def load_second_third(self, prize_table):
        idx = self.name_column_index(prize_table)
        try:
            second = node_from_class(prize_table, "background-color-second-place")
        except ParserError:
            return
        if "TBD" in second.text:
            """ Don't bother if the results aren't in."""
            return
        second_columns = second.find_all("td")
        links = second_columns[idx].find_all("a")
        self.second_place = links[-1].text.strip()
        if "2nd-3rd" in second_columns[0].text:
            third = next_tag(second)
            third_columns = third.find_all("td")
            links = third_columns[0].find_all("a")
            self.second_place = "{} - {}".format(self.second_place, links[-1].text.strip())


    def load_runners_up(self, prize_table):
        """ Loads runners up."""
        try:
            # Might not have a third place (Wrang of Fire 3)
            third = node_from_class(prize_table, "background-color-third-place")
        except ParserError:
            return
        if "TBD" in third.text:
            """ Don't bother if the results aren't in."""
            return
        idx = self.name_column_index(prize_table)
        third_columns = third.find_all("td")
        links = third_columns[idx].find_all("a")
        self.runners_up.append(links[-1].text.strip())
        fourth = next_tag(third)
        if not fourth:
            return
        fourth_columns = fourth.find_all("td")
        if "3rd-4th" in third_columns[0].text or len(fourth_columns) <= idx:
            links = fourth_columns[0].find_all("a")
            self.runners_up[0] = "{} - {}".format(self.runners_up[0], links[-1].text.strip())
        else:
            links = fourth_columns[idx].find_all("a")
            try:
                self.runners_up.append(links[-1].text.strip())
            except IndexError:
                pass

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

class ParserError(Exception):
    """ What to throw if something critical missing from soup."""

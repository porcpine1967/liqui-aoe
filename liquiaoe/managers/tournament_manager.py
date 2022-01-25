#!/usr/bin/env python3
""" Everything you want to know about Age of Empires Tournaments."""
from collections import defaultdict
from datetime import datetime
import re

import bs4

PARTICIPANTS = re.compile(r"([0-9]+)")


class TournamentManager:
    def __init__(self, loader):
        self._tournaments = []
        self.url = "/ageofempires/Portal:Tournaments"
        self.loader = loader
        self.load()

    def completed(self, timebox):
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if  timebox[0] <= tournament.end <= timebox[1]:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def ongoing(self, timebox):
        tournaments = defaultdict(list)
        for tournament in self._tournaments:
            if  timebox[0] <= tournament.start and tournament.end >= timebox[1]:
                tournaments[tournament.game].append(tournament)
        return tournaments

    def starting(self, timebox):
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
        start = None
        for h3 in data.find_all("h3"):
            if "S-Tier" in h3.text:
                start = h3
        rows = None
        while not rows:
            start = start.next_sibling
            try:
                if "tournament-card" in start.attrs["class"]:
                    rows = start.find_all("div")
            except AttributeError:
                pass
        for row in rows:
            if "divRow" in row.attrs["class"]:
                self._tournaments.append(Tournament(row))

def node_from_class(ancestor, class_attribute):
    for node in ancestor.descendants:
        try:
            if class_attribute in node.attrs["class"]:
                return node
        except (AttributeError, KeyError):
            pass
    raise ParserError("{} missing".format(class_attribute))

def text_from_tag(parent, tag):
    divs = parent.find_all(tag)
    return divs[-1].text.strip()

def div_attributes(parent):
    divs = parent.find_all("div")
    return [div.text.strip() for div in divs[1:]]

def next_tag(first_tag):
    sibling = first_tag.next_sibling
    while True:
        if isinstance(sibling, bs4.element.Tag):
            return sibling
        sibling = sibling.next_sibling
    return None

class Tournament:
    def __init__(self, row):
        # Basic attributes (loaded from tournaments page)
        self.cancelled = False
        self.load_basic(row)
        # Advanced (loaded from tournament page)
        self.organizers = []
        self.sponsors = []
        self.game_mode = None
        self.format_style = None
        self.description = None
        self.team = False
        self.runners_up = []

    def load_advanced(self, loader):
        """ Call the loader for self.url and parse."""
        soup = loader.soup(self.url)
        main = node_from_class(soup, "mw-parser-output")
        if not main:
            raise ParserError("No mw-parser-output in soup")
        self.description = main.p.text.strip()
        self.load_info_box(node_from_class(main, "fo-nttax-infobox"))
        self.load_runners_up(node_from_class(main, "prizepooltable"))

    def load_runners_up(self, pool_table):
        """ Loads runners up."""
        third = node_from_class(pool_table, "background-color-third-place")
        if "TBD" in third.text:
            """ Don't bother if the results aren't in."""
            return
        fourth = next_tag(third)
        column_header = "Team" if self.team else "Player"
        ths = pool_table.find_all("th", recursive=True)
        for idx, th in enumerate(ths):
            if column_header in th.text:
                break

        third_columns = third.find_all("td")
        links = third_columns[idx].find_all("a")
        self.runners_up.append(links[-1].text.strip())

        fourth_columns = fourth.find_all("td")
        if "3rd-4th" in third_columns[0].text:
            links = fourth_columns[0].find_all("a")
            self.runners_up[0] += "|{}".format(links[-1].text.strip())
        else:
            links = fourth_columns[idx].find_all("a")
            self.runners_up.append(links[-1].text.strip())

    def load_info_box(self, info_box):
        """ Parse information from info box"""
        for div in info_box.find_all("div"):
            try:
                if div.div.text == "Series:":
                    self.series = text_from_tag(div, "div")
                if div.div.text == "Organizer:":
                    self.organizers = div_attributes(div)
                if div.div.text == "Game Mode:":
                    self.game_mode = text_from_tag(div, "div")
                if div.div.text == "Format:":
                    self.format_style = text_from_tag(div, "div")
                    self.team = "1v1" not in self.format_style
                if div.div.text == "Sponsor(s):":
                    self.sponsors = div_attributes(div)
            except AttributeError:
                pass

    def load_basic(self, row):
        divs = row.find_all("div")
        self.load_header(divs[0])
        self.load_dates(divs[1].text)
        self.prize = divs[2].text.strip()
        self.load_participants(divs[3].text)
        self.first_place = self.first_place_url = self.second_place = None
        self.load_first_place(divs[5])
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
            self.start = datetime.strptime(start.strip(), "%b %d, %Y")
            self.end = datetime.strptime(end.strip(), "%b %d, %Y")
        else:
            self.start = datetime.strptime(text.strip(), "%b %d, %Y")
            self.end = self.start

    def load_participants(self, text):
        match = PARTICIPANTS.match(text)
        if match:
            self.participant_count = int(match.group(1))
        else:
            self.participant_count = -1

    def load_first_place(self, div):
        if div.text == "Cancelled":
            self.cancelled = True
            return
        spans = div.find_all("span")
        try:
            self.first_place = spans[-1].text.strip()
            url = spans[-1].a.attrs["href"]
            if "redlink" not in url:
                self.first_place_url = url
        except (AttributeError, IndexError):
            pass

    def load_second_place(self, div):
        if div.text == "Cancelled":
            self.cancelled = True
            return
        spans = div.find_all("span")
        try:
            self.second_place = spans[-1].text.strip()
        except (AttributeError, IndexError):
            pass

class ParserError(Exception):
    """ What to throw if something critical missing from soup."""

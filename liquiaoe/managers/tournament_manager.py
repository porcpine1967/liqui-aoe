#!/usr/bin/env python3
""" Everything you want to know about Age of Empires Tournaments."""
from datetime import datetime
import re

PARTICIPANTS = re.compile(r"([0-9]+)")


class TournamentManager:
    def __init__(self, loader):
        self._tournaments = []
        self.url = "ageofempires/Portal:Tournaments"
        self.loader = loader
        self.load()

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
                    rows = start.children
            except AttributeError:
                pass
        for row in rows:
            if "divRow" in row.attrs["class"]:
                self._tournaments.append(Tournament(row))


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

    def load_basic(self, row):
        divs = row.find_all("div")
        self.load_header(divs[0])
        self.load_dates(divs[1].text)
        self.prize = divs[2].text
        self.load_participants(divs[3].text)
        self.load_first_place(divs[4])
        self.load_second_place(divs[5])

    def load_header(self, row):
        """Load the first five attributes."""
        self.tier = row.a.text
        spans = row.find_all("span")
        self.game = spans[0].a.attrs["title"]
        self.series = None
        self.url = row.b.a.attrs["href"]
        self.name = row.b.a.text

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
            self.first_place = spans[-1].a.text
        except AttributeError:
            print("First: {}".format(self.name))

    def load_second_place(self, div):
        if div.text == "Cancelled":
            self.cancelled = True
            return
        spans = div.find_all("span")
        try:
            self.second_place = spans[-1].a.text
        except AttributeError:
            print("SECOND: {}".format(self.name))

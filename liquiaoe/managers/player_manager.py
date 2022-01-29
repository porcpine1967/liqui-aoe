#!/usr/bin/env python3
""" Everything you want to know about Age of Empires Players."""

from datetime import date, datetime

import bs4

from liquiaoe.managers.tournament_manager import node_from_class, Tournament

class PlayerManager:
    def __init__(self, loader):
        self.loader = loader

    def tournaments(self, player_url):
        player_tournaments = []
        if "index" in player_url:
            return player_tournaments
        url = "{}/Results".format(player_url)
        data = self.loader.soup(url)
        results_table = node_from_class(data, "wikitable")
        for node in results_table.descendants:
            if node.name == "tr" and len(node.find_all("td")) == 11:
                tournament = Tournament()
                tournament.load_from_player(node)
                player_tournaments.append(tournament)
        return player_tournaments

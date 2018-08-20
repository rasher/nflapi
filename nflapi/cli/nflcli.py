#!/usr/bin/env python

from nflapi import NFL
import logging
import sys


def main():
    logging.basicConfig(level=logging.DEBUG)
    nfl = NFL(ua=('Mozilla/5.0 (X11; CrOS x86_64 10895.10.0) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/69.0.3497.21 Safari/537.36'))

    cw = nfl.schedule.current_week()
    print("{w.season} {w.seasonType} {w.week}".format(w=cw))

    games = nfl.game.week(cw)
    for game in games:
        print(("{g.gameTime:%Y-%m-%d %H:%M %Z} "
               "{g.visitorTeam.abbr} {g.visitorTeamScore.pointsTotal} "
               "@ "
               "{g.homeTeamScore.pointsTotal} {g.homeTeam.abbr}").format(
                   g=game))

    teams, _ = nfl.standings.current()
    for team in teams:
        print(("{team.fullName} - "
               "{s.overallWins}-{s.overallLosses}-{s.overallTies}").format(
                   team=team, s=team.standings[0]))

#!/usr/bin/env python
import logging
from functools import update_wrapper

import click
import pendulum

from nflapi import NFL
from nflapi.__version__ import __version__ as VERSION

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def nflobj(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        ctx.invoke(f, ctx.obj['nfl'], *args, **kwargs)

    return update_wrapper(new_func, f)


@click.version_option(version=VERSION)
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--verbose/--quiet', default=False)
@click.pass_context
def nflcli(ctx, verbose):
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.WARN
    logging.basicConfig(level=level)
    ctx.obj['nfl'] = NFL(ua=('Mozilla/5.0 (X11; CrOS x86_64 10895.10.0) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/69.0.3497.21 Safari/537.36'))


@nflcli.command(short_help="Display the current week")
@nflobj
def current_week(nfl):
    cw = nfl.schedule.current_week()
    logging.debug("Current week: %r", cw)
    print("{w.season} {w.seasonType} {w.week}".format(w=cw))


@nflcli.command(short_help="Show schedule for a given week")
@nflobj
def schedule(nfl):
    cw = nfl.schedule.current_week()
    print("{w.season} {w.seasonType} {w.week}".format(w=cw))

    games = nfl.game.week(cw)
    tz = pendulum.tz.local_timezone()
    for game in sorted(games, key=lambda g: g.gameTime.pt):
        localtime = game.gameTime.astimezone(tz)
        print(("{t:%Y-%m-%d %H:%M %Z} "
               "{g.visitorTeam.abbr:3s} {g.visitorTeamScore.pointsTotal:2d} "
               "@ "
               "{g.homeTeamScore.pointsTotal:2d} {g.homeTeam.abbr:3s}").format(
            g=game, t=localtime))


@nflcli.command(short_help="List standings")
@nflobj
def standings(nfl):
    teams, _ = nfl.standings.current()

    groups = {}
    warned = False
    for team in teams:
        group = team.division
        rank = team.standings[0].divisionRank
        if rank is None:
            if not warned:
                logging.warn("No rank in data. Sorting by winpct+name")
                warned = True
            rank = (-team.standings[0].overallWinPct, team.fullName)
        if group not in groups:
            groups[group] = []
        groups[group].append((rank, team))
    for group, teams in sorted(groups.items(), key=lambda g: g[0].abbr):
        print(group.fullName + "\n" + ("=" * len(group.fullName)))
        print("Team        W  L  T  PCT")
        for rank, team in sorted(teams, key=lambda t: t[0]):
            print(("{t.nickName:10} {s.overallWins:2d} {s.overallLosses:2d} "
                   "{s.overallTies:2d}  {s.overallWinPct:1.3f}")
                  .format(t=team, s=team.standings[0]))
        print()


@nflcli.command(short_help="Team info")
@click.argument('abbr')
@nflobj
def team(nfl, abbr):
    team = nfl.team.get(abbr)
    print(team.fullName)
    print(team.conference.fullName)
    print(team.division.fullName)
    print(team.venue.name)


def main():
    nflcli(obj={})


if __name__ == "__main__":
    main()

#!/usr/bin/env python
import csv
import logging
import sys
from functools import update_wrapper
from pprint import pprint

import click
import pendulum
from sgqlc.operation import Operation

from nflapi import NFL
from nflapi import shield
from nflapi.__version__ import __version__ as VERSION
from nflapi.const import DIVISION_NAMES
from nflapi.shield import WeekType, Team, FranchiseState, FranchiseConnection, Franchise

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def nflobj(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        ctx.invoke(f, *args, nfl=ctx.obj['nfl'], date=ctx.obj['date'], **kwargs)

    return update_wrapper(new_func, f)


@click.version_option(version=VERSION)
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--verbose/--quiet', default=False)
@click.option('--date', default=None, type=click.DateTime())
@click.pass_context
def nflcli(ctx, verbose, date):
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.WARN
    logging.basicConfig(level=level)
    if date is None:
        date = pendulum.now()
    else:
        date = pendulum.instance(date)
    logging.debug("Using date %s", date)
    ctx.obj['date'] = date
    ctx.obj['nfl'] = NFL(ua=('nflapi cli'))


def print_week(w):
    logging.debug("Week: %r", w)
    if w.week_type in (WeekType.PRE, WeekType.REG):
        print("{w.season_value} {w.season_type} {w.week_value}".format(w=w))
    else:
        print("{w.season_value} {w.week_type}".format(w=w))


@nflcli.command(short_help="Display the current week")
@nflobj
def current_week(nfl: NFL, date: pendulum.DateTime, *args, **kwargs):
    w = nfl.schedule.current_week(date)
    print_week(w)


@nflcli.command(short_help="Show schedule for a given week")
@nflobj
def schedule(nfl: NFL, date: pendulum.DateTime, *args, **kwargs):
    w = nfl.schedule.current_week(date)
    print_week(w)

    games = nfl.game.week_games(w.week_value, w.season_type,
                                w.season_value)
    tz = pendulum.tz.local_timezone()
    for game in sorted(games, key=lambda g: g.time):
        localtime = pendulum.parse(game.time).astimezone(tz)
        print(("{t:%Y-%m-%d %H:%M %Z} "
               "{g.away_team.full_name} "
               "@ "
               "{g.home_team.full_name} id={g.id}").format(
            g=game, t=localtime))


@nflcli.command(short_help="List standings")
@nflobj
def standings(nfl: NFL, date: pendulum.DateTime, *args, **kwargs):
    team_records = nfl.standings.current(date)

    groups = {}
    for team, team_record in team_records:
        group = team.division
        if group not in groups:
            groups[group] = []
        groups[group].append((team, team_record))
    for group, teams in sorted(groups.items(), key=lambda g: g[0]):
        group_name = DIVISION_NAMES.get(group, group)
        print(group_name + "\n" + ("=" * len(group_name)))
        print("Team            W  L  T  PCT")
        for team, team_record in sorted(teams, key=lambda t: t[1].division_rank):
            print(("{t.nick_name:14} {tr.overall_win:2d} {tr.overall_loss:2d} "
                   "{tr.overall_tie:2d}  {tr.overall_pct:1.3f}")
                  .format(t=team, tr=team_record))
        print()


@nflcli.command()
@nflobj
def teams(nfl: NFL, **kwargs):
    # nfl.football.teams_by_season(2021)

    def add(t: Team):
        t.id()
        t.full_name()
        t.conference()
        t.division()
        t.venues()

    for t in sorted(nfl.team.get_all(select_fun=add), key=lambda t: t.full_name):
        print("{t.full_name}\n  Id:    {t.id}\n  Conf.: {t.conference}\n  Div.:  {t.division}".format(t=t))
        for v in t.venues:
            print("  Venue: {v.full_name}".format(v=v))


@nflcli.command(short_help="Team info")
@click.argument('abbr')
@nflobj
def team(nfl: NFL, abbr, *args, **kwargs):
    def selector(team):
        team.full_name()
        team.venues().display_name()
        team.division()
        team.conference()

    team = nfl.team.lookup(abbr, select_fun=selector)
    print(team.full_name)
    print(team.conference)
    print(team.division)
    print(team.venues[0].display_name)


@nflcli.command(short_help="Game state")
@click.argument('id')
@nflobj
def game(nfl: NFL, id, *args, **kwargs):
    game = nfl.game.by_id(id)
    pprint(game.raw)


@nflcli.command(short_help="Combine")
@click.argument('year')
@nflobj
def combine(nfl: NFL, year: int, *args, **kwargs):
    participants = nfl.combine.participants(year)
    writer = csv.DictWriter(sys.stdout, ['firstName', 'lastName', 'position', 'college', 'homestate', 'homeTown', 'height', 'weight', 'handSize', 'armLength', '20YardShuttle', '3ConeDrill', '40YardDash', '60YardShuttle', 'benchPress', 'broadJump', 'verticalJump', 'expertGrade'])
    writer.writeheader()
    for p in participants.combine_profiles:
        if p.person.hometown:
            homestate, homeTown = p.person.hometown.split(",", 1)
        else:
            homestate, homeTown = '', ''
        writer.writerow({
            'firstName': p.person.first_name,
            'lastName': p.person.last_name,
            'position': p.position,
            'college': p.person.college_names[0],
            'homestate': homestate.strip(),
            'homeTown': homeTown.strip(),
            'height': p.height,
            'weight': p.weight,
            'handSize': p.hand_size,
            'armLength': p.arm_length,
            '20YardShuttle': p.twenty_yard_shuttle.seconds if p.twenty_yard_shuttle else '',
            '3ConeDrill': p.three_cone_drill.seconds if p.three_cone_drill else '',
            '40YardDash': p.forty_yard_dash.seconds if p.forty_yard_dash else '',
            '60YardShuttle': p.sixty_yard_shuttle.seconds if p.sixty_yard_shuttle else '',
            'benchPress': p.bench_press.repetitions if p.bench_press else '',
            'broadJump': p.broad_jump.inches if p.broad_jump else '',
            'verticalJump': p.vertical_jump.inches if p.vertical_jump else '',
            'expertGrade': p.draft_grade,
        })


@nflcli.command(short_help="Franchises")
@nflobj
def test(nfl: NFL, *args, **kwargs):
    op = Operation(shield.Viewer)
    franchises: FranchiseConnection = op.viewer.franchises(first=40, state=FranchiseState.ACTIVE)
    f: Franchise = franchises.edges.node
    f.id()
    t = f.current_team()
    t.abbreviation()
    pprint([e.node for e in nfl.query(op).viewer.franchises.edges])


def main():
    nflcli(obj={})


if __name__ == "__main__":
    main()

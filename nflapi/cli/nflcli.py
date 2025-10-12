#!/usr/bin/env python
import csv
import logging
import sys
from functools import update_wrapper

import click
import pendulum

from nflapi import NFL
from nflapi.__version__ import __version__ as VERSION
from nflapi.const import DIVISION_NAMES

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
    logging.debug("Week: %r", w.raw)
    if w.week_type in ('PRE', 'REG'):
        print("{w.season} {w.season_type} {w.week}".format(w=w))
    else:
        print("{w.season} {w.week_type}".format(w=w))


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
        group = team.division_full_name
        if group not in groups:
            groups[group] = []
        groups[group].append((team, team_record))
    for group, teams in sorted(groups.items(), key=lambda g: g[0]):
        group_name = DIVISION_NAMES.get(group, group)
        print(group_name + "\n" + ("=" * len(group_name)))
        print("Team            W  L  T  PCT")
        for team, team_record in sorted(teams, key=lambda t: t[1].division.rank):
            print(("{t.nick_name:14} {tr.overall.wins:2d} {tr.overall.losses:2d} "
                   "{tr.overall.ties:2d}  {tr.overall.win_pct:1.3f}")
                  .format(t=team, tr=team_record))
        print()


@nflcli.command()
@nflobj
def teams(nfl: NFL, date: pendulum.DateTime, **kwargs):
    if date is None:
        all_teams = nfl.team.get_all()
    else:
        season = nfl.schedule.current_week().season
        all_teams = nfl.team.get_all(season)
    logging.debug("All teams", all_teams)
    for t in sorted(all_teams, key=lambda t: t.full_name):
        print("{t.full_name}\n  Id:    {t.id}\n  Conf.: {t.conference_abbr}\n  Div.:  {t.division_full_name}".format(
            t=t))
        for v in t.venues:
            print("  Venue: {v.name}".format(v=v))


@nflcli.command(short_help="Team info")
@click.argument('abbr')
@nflobj
def team(nfl: NFL, abbr, date: pendulum.DateTime, *args, **kwargs):
    logging.debug("date %s", date)
    if date is None:
        team = nfl.team.lookup(abbr)
    else:
        season = nfl.schedule.week(date).season
        team = nfl.team.lookup(abbr, season)
    logging.debug("Team result %r", team)
    if team:
        print(team.full_name)
        print(team.conference_abbr)
        print(team.division_full_name)
        print(team.venues[0].name)
    else:
        print("No results for %s" % abbr)


@nflcli.command(short_help="Game state")
@click.argument('id')
@nflobj
def game(nfl: NFL, id, *args, **kwargs):
    from pprint import pprint
    pprint(nfl.game.by_id(id))


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


@nflcli.command(short_help="Draft")
@nflobj
def draft(nfl: NFL, date: pendulum.DateTime, *args, **kwargs):
    picks_data = nfl.draft.picks(date.year)
    teams = {t.id: t for t in nfl.football.teams_by_season(date.year).teams}
    profiles = {p.person.id: p for p in nfl.combine.participants(date.year).combine_profiles}
    for pick in picks_data.picks:
        if pick.person_id:
            c = profiles.get(pick.person_id)
            print("{p.draft_round}.{p.draft_position:<2d} {t.nick_name:<10s} {c.person.display_name}".format(p=pick,
                                                                                               t=teams[pick.team_id],
                                                                                   c=c))


@nflcli.command(short_help="Roster")
@click.argument('abbr')
@nflobj
def roster(nfl: NFL, abbr: str, date: pendulum.DateTime, *args, **kwargs):
    if date is None:
        season = nfl.schedule.current_week().season
    else:
        season = nfl.schedule.week(date).season
    logging.debug("Season %s", season)

    team = nfl.team.lookup(abbr, season)
    logging.debug("Team %s", team)

    roster = nfl.roster.lookup(abbr, season)

    print("{0.full_name}".format(team))
    for player in sorted(roster, key=lambda p: (p.position_group, p.display_name)):
        jersey_number = '' if player.jersey_number is None else player.jersey_number
        print("  {1: >2} {0.display_name} ({0.position})".format(player, jersey_number))


@nflcli.command(short_help="Live")
@nflobj
def live(nfl: NFL, date: pendulum.DateTime, *args, **kwargs):
    week = nfl.football.week_by_date(date)
    print_week(week)
    teams = {t.id: t for t in nfl.football.teams_by_season(date.year).teams}
    games = nfl.football.game_summaries_by_week(week.season, week.season_type, week.week)
    for game in games:
        home_team = teams.get(game.home_team.team_id, None)
        away_team = teams.get(game.away_team.team_id, None)
        print("{game.phase:6} {away.abbreviation:3} {game.away_team.score.total:2} @"
              " {game.home_team.score.total:2} {home.abbreviation:3}".format(game=game, home=home_team, away=away_team))


def main():
    nflcli(obj={})


if __name__ == "__main__":
    main()

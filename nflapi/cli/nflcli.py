#!/usr/bin/env python
import csv
import logging
import sys
from functools import update_wrapper

import click
import pendulum
from rich.containers import Renderables
from rich.pretty import Pretty

from rich_pyfiglet import RichFiglet
from rich import box

from rich.console import Console
from rich.table import Table

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


def format_week(w) -> str:
    logging.debug("Week: %r", w.raw)
    if w.week_type in ('PRE', 'REG'):
        return "{w.season} {w.season_type} {w.week}".format(w=w)
    else:
        return "{w.season} {w.week_type}".format(w=w)


def print_week(w):
    print(format_week(w))


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
    week = nfl.schedule.current_week(date)
    all_teams = {t.id: t for t in nfl.team.get_all(week.season)}

    console = Console()
    grid = Table.grid()

    groups = {}
    for team, team_record in team_records:
        group = team.division_full_name
        if group not in groups:
            groups[group] = []
        groups[group].append((team, team_record))

    def division_table(groups: dict, group: str) -> Table:
        group_name = DIVISION_NAMES.get(group, group)
        teams = groups[group_name]
        div_table = Table(title=group_name, title_style='bold ' + ('bright_red' if group_name.startswith('AFC') else
                                                                   'bright_blue'))
        div_table.add_column('Team', width=20)
        div_table.add_column('W', justify='right')
        div_table.add_column('L', justify='right')
        div_table.add_column('T', justify='right')
        div_table.add_column('PCT', justify='right')
        for team, team_record in sorted(teams, key=lambda t: t[1].division.rank):
            ovr = team_record.overall
            td = all_teams[team.id]
            style = "{td.primary_color} on {td.secondary_color}".format(td=td)
            div_table.add_row('[bold]%s[/]' % team.nick_name, str(ovr.wins), str(ovr.losses),
                              str(ovr.ties), "%1.3f" % ovr.win_pct, style=style)
        return div_table

    for division in ('NORTH', 'SOUTH', 'EAST', 'WEST'):
        grid.add_row(division_table(groups, 'AFC_' + division),
                     division_table(groups, 'NFC_' + division))
    console.print(grid)


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
    gd = nfl.game.game_detail(id, include_drive_chart=True)

    teams = nfl.team.by_ids([gd.home_team.id, gd.away_team.id])
    home = teams[gd.home_team.id]
    away = teams[gd.away_team.id]

    print("{0.full_name} @ {1.full_name}".format(away, home))
    print("{0}".format(pendulum.parse(gd.time).astimezone(pendulum.tz.local_timezone())))

    box_score = Table(title="Box score", box=box.ROUNDED, header_style="")

    if gd.summary.phase == 'INGAME':
        box_score.add_column(gd.summary.clock)
    elif gd.summary.phase in ('HALFTIME',):
        box_score.add_column(gd.summary.phase.capitalize())
    else:
        box_score.add_column()
    box_score.add_column('Q1', justify="right")
    box_score.add_column('Q2', justify="right", header_style="bold")
    box_score.add_column('Q3', justify="right")
    box_score.add_column('Q4', justify="right")
    box_score.add_column('OT', justify="right")
    box_score.add_column('Total', justify="right")

    for (t, b) in [(away, gd.summary.away_team.score),
                     (home, gd.summary.home_team.score)]:
        box_score.add_row(*list(map(str, [t.abbreviation, b.q1, b.q2, b.q3, b.q4, b.ot, b.total])))

    console = Console()
    console.print(box_score)

    scoring = Table(title="Scoring Summary", box=box.ROUNDED)
    scoring.add_column('Team')
    scoring.add_column('Time')
    scoring.add_column('Score')
    for ss in gd.drive_chart.scoring_summaries:
        team = teams.get(ss.scoring_team_id)
        scoring.add_row(team.abbreviation, "Q{0.quarter} {0.clock_time}".format(ss), ss.play_description)

    console.print(scoring)

    stats = {}
    for play in gd.drive_chart.plays:
        for stat in play.stats:
            if stat.person_id not in stats:
                stats[stat.person_id] = {
                    'name': stat.gsis_player_name,
                    'stats': {},
                }
            if stat.stat_type not in stats[stat.person_id]['stats']:
                stats[stat.person_id]['stats'][stat.stat_type] = 0
            if stat.yards is not None:
                stats[stat.person_id]['stats'][stat.stat_type] += stat.yards
            else:
                stats[stat.person_id]['stats'][stat.stat_type] += 1


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
    teams = {t.id: t for t in nfl.api.teams_by_season(date.year).teams}
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
    week = nfl.api.week_by_date(date)
    week_str = format_week(week)

    week_header = RichFiglet(week_str, font="ansi_regular", colors=["bright_red", "bright_blue"], horizontal=False)

    gt = Table()
    gt.add_column('State')
    gt.add_column('Away')
    gt.add_column('', justify="right")
    gt.add_column('')
    gt.add_column('', justify="right")
    gt.add_column('Home')

    teams = {t.id: t for t in nfl.api.teams_by_season(date.year).teams}
    games = nfl.api.game_summaries_by_week(week.season, week.season_type, week.week)
    for game in sorted(games, key=lambda g: g.start_time):
        home_team = teams.get(game.home_team.team_id, None)
        away_team = teams.get(game.away_team.team_id, None)
        hscore = game.away_team.score.total
        ascore = game.home_team.score.total
        if hscore > ascore:
            hscore = '[green]%s[green]' % hscore
        if ascore > game.away_team.score.total:
            ascore = '[green]%s[green]' % ascore
        if game.phase == 'INGAME':
            phase = "{game.quarter} {game.clock}".format(game=game)
        else:
            phase = game.phase
        gt.add_row(
            phase,
            away_team.abbreviation,
            str(hscore),
            '@',
            str(ascore),
            home_team.abbreviation
        )

    console = Console()
    console.print(week_header)
    console.print(gt)


def main():
    nflcli(obj={})


if __name__ == "__main__":
    main()

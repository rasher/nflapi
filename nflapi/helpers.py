import datetime
import logging
from typing import Callable, List

import pendulum
from sgqlc.operation import Operation
from sgqlc import types

from .shield import shield, GameOrderBy, OrderByDirection

DEFAULT_FIELDS = {
    shield.Game: ['id', 'game_time', 'slug', 'game_detail_id'],
    shield.GameDetail: ['id', 'game_time', 'phase', 'period', 'game_clock'],
    shield.Team: ['id', 'abbreviation', 'full_name', 'nick_name'],
    shield.TeamRecord: ['overall_win', 'overall_loss', 'overall_tie', 'overall_pct', 'team_id', 'division_rank',
                        'conference_rank'],
    shield.CurrentClubRoster: ['display_name', 'first_name', 'jersey_number', 'last_name', 'nfl_experience',
                                'person_id', 'position', 'status'],
    shield.Player: ['id', 'position', 'jersey_number', 'nfl_experience', 'status', 'person', 'current_team'],
    shield.PlayerPerson: ['id', 'display_name', 'first_name', 'last_name'],
}


class Helper:
    def __init__(self, nfl):
        self.nfl = nfl

    def query(self, op: Operation):
        return self.nfl.shield.query(op)

    @staticmethod
    def _standard_fields(obj: shield.AbstractEntity, type_):
        obj.__fields__(*DEFAULT_FIELDS.get(type_))


def apply_selector(obj, type_, select_fun: Callable[[types.Type], None] = None):
    if select_fun:
        select_fun(obj)
    else:
        Helper._standard_fields(obj, type_)


class ScheduleHelper(Helper):
    def current_week(self, date: datetime.datetime = None) -> shield.Week:
        op = Operation(shield.Viewer)
        if date is None:
            week: shield.Week = op.viewer.league.current.week()
        else:
            date = date.astimezone(pendulum.UTC)
            week: shield.Week = op.viewer.league.current(date=date).week()
        week.season_value()
        week.season_type()
        week.week_order()
        week.week_type()
        week.week_value()
        return self.query(op).viewer.league.current.week

    def week(self, date: datetime.datetime):
        return self.current_week(date)


class GameHelper(Helper):

    def week_games(self, week=None, season_type=None, season=None):
        if week is None or season_type is None or season is None:
            current_week = self.nfl.schedule.current_week()
        week = week if week is not None else current_week.week_value
        season_type = season_type or current_week.season_type
        season = season or current_week.season_value

        games = self.nfl.football.games_by_week(season, season_type=season_type, week=week)
        return games

    def by_id(self, game_id: str):
        return self.nfl.football.game_by_id(game_id)

    def game_detail_id_for_id(self, game_id: str):
        return self.nfl.football.game_detail_id_for_id(game_id)


class GameDetailHelper(Helper):
    def by_id(self, id, select_fun: Callable[[shield.GameDetail], None] = None):
        op = Operation(shield.Viewer)
        game_detail = op.viewer.game_detail(id=id)
        apply_selector(game_detail, shield.GameDetail, select_fun)
        game_detail = self.query(op).viewer.game_detail
        return game_detail

    def by_ids(self, ids, select_fun: Callable[[shield.GameDetail], None] = None):
        op = Operation(shield.Viewer)
        game_details = op.viewer.game_details_by_ids(ids=ids)
        apply_selector(game_details, shield.GameDetail, select_fun)
        return self.query(op).viewer.game_details_by_ids


class StandingsHelper(Helper):
    def get(self, week, season_type, season=0):
        logging.debug("Getting week %s, type %s, season %s", week, season_type, season)
        op = Operation(shield.Viewer)
        standings = op.viewer.standings(first=40, week_season_value=season, week_season_type=season_type,
                                        week_week_value=week)
        standing = standings.edges.node
        record = standing.team_records
        self._standard_fields(record, shield.TeamRecord)
        standings = self.query(op)
        if len(standings.viewer.standings.edges) == 0:
            return []
        team_records = standings.viewer.standings.edges[0].node.team_records
        team_ids = [tr.team_id for tr in team_records]

        def with_div_con(team):
            team.id()
            team.full_name()
            team.nick_name()
            team.division()
            team.conference()

        teams = {t.id: t for t in self.nfl.team.by_ids(team_ids, select_fun=with_div_con)}
        return [(teams[team_record['team_id']], team_record) for team_record in team_records]

    def current(self, date=None):
        current_week = self.nfl.schedule.current_week(date)
        week = current_week.week_value
        season_type = current_week.season_type
        season = current_week.season_value
        return self.get(week, season_type, season)


class TeamHelper(Helper):
    def get_all(self, season_value=0, select_fun: Callable[[shield.Team], None] = None) -> List[shield.Team]:
        op = Operation(shield.Viewer)
        teams = op.viewer.teams(first=100, season_value=season_value)
        team = teams.edges.node()
        apply_selector(team, shield.Team, select_fun)
        teams = self.query(op)
        return [t.node for t in teams.viewer.teams.edges]

    def lookup(self, abbreviation, season_value=0, select_fun: Callable[[shield.Team], None] = None):
        # There is no way to lookup teams by anything other than id
        # So we just get them all and pick it from the bunch :|
        def add_abbreviation(team):
            if select_fun:
                select_fun(team)
            team.abbreviation()

        all_teams = self.get_all(season_value, select_fun=add_abbreviation)
        return next(filter(lambda t: t.abbreviation == abbreviation, all_teams), None)

    def by_ids(self, ids: List[str], select_fun: Callable[[shield.Game], None] = None):
        op = Operation(shield.Viewer)
        teams = op.viewer.teams_by_ids(ids=ids)
        apply_selector(teams, shield.Team, select_fun)
        teams = self.query(op)
        return teams.viewer.teams_by_ids


class RosterHelper(Helper):
    def lookup(self, abbreviation, select_fun: Callable[[shield.CurrentClubRoster], None] = None):
        def add_abbr_and_property_id(team):
            if select_fun:
                select_fun(team)
            team.abbreviation()
            team.franchise.property.id()

        all_teams = self.nfl.team.get_all(select_fun=add_abbr_and_property_id)
        the_team = next(filter(lambda t: t.abbreviation == abbreviation, all_teams), None)
        if not the_team:
            return None

        return self.by_id(the_team.franchise.property.id, select_fun)

    def by_id(self, id: str, select_fun: Callable[[shield.CurrentClubRoster], None] = None):
        # id param is team.franchise.property.id
        op = Operation(shield.Viewer)
        roster = op.viewer.clubs.current_club_roster(property_id=id)
        apply_selector(roster, shield.CurrentClubRoster, select_fun)
        roster = self.query(op)
        return roster.viewer.clubs.current_club_roster

    def by_team_id(self, team_id: str, select_fun: Callable[[shield.CurrentClubRoster], None] = None):
        def add_property_id(team):
            if select_fun:
                select_fun(team)
            team.franchise.property.id()

        the_team = self.nfl.team.by_ids(ids=[team_id], select_fun=add_property_id)
        if not len(the_team):
            return None
        else:
            the_team = the_team[0]

        return self.by_id(the_team.franchise.property.id, select_fun)


class CombineHelper(Helper):
    def participants(self, year: int = 0):
        return self.nfl.football.combine_profiles_by_year(year)


class PlayerHelper(Helper):
    def lookup(self, season: int = 0, player_name: str = None, team_id: str = None, status=None, first=100, after=None, select_fun: Callable[[shield.Player], None] = None):
        def add_team_person_fields(player):
            if select_fun:
                select_fun(player)
            else:
                apply_selector(player, shield.Player)
                person = player.person()
                apply_selector(person, shield.PlayerPerson)
                team = player.current_team()
                apply_selector(team, shield.Team)

        op = Operation(shield.Viewer)
        players = op.viewer.players(season_season=season, person_display_name_contains=player_name, current_team_id=team_id, first=first, after=after)
        players.edges.cursor()
        player = players.edges.node()
        apply_selector(player, shield.Player, select_fun=add_team_person_fields)
        players = self.query(op)
        player_list = []
        for p in players.viewer.players.edges:
            p.node.cursor = p.cursor
            player_list.append(p.node)
        return player_list

    def by_id(self, id: str, select_fun: Callable[[shield.Player], None] = None):
        def add_team_person_fields(player):
            if select_fun:
                select_fun(player)
            else:
                apply_selector(player, shield.Player)
                person = player.person()
                apply_selector(person, shield.PlayerPerson)
                team = player.current_team()
                apply_selector(team, shield.Team)

        op = Operation(shield.Viewer)
        player = op.viewer.player(id=id)
        apply_selector(player, shield.Player, select_fun=add_team_person_fields)
        player = self.query(op)
        return player.viewer.player


__all__ = [
    'ScheduleHelper',
    'GameHelper',
    'StandingsHelper',
    'TeamHelper',
    'GameDetailHelper',
    'RosterHelper',
    'PlayerHelper',
    'CombineHelper',
]

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
}


class Helper:
    def __init__(self, nfl):
        self.nfl = nfl

    def query(self, op: Operation):
        return self.nfl.shield.query(op)

    @staticmethod
    def _standard_fields(obj: shield.AbstractEntity, type_):
        obj.__fields__(*DEFAULT_FIELDS.get(type_), 'id')


def apply_selector(obj, type_, select_fun: Callable[[types.Type], None] = None):
    if select_fun:
        select_fun(obj)
    else:
        Helper._standard_fields(obj, type_)


class ScheduleHelper(Helper):
    def current_week(self, date: datetime.datetime = None) -> shield.Week:
        date = date.astimezone(pendulum.UTC)
        op = Operation(shield.Viewer)
        if date is None:
            week: shield.Week = op.viewer.league.current.week()
        else:
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
    def week_games(self, week=None, season_type=None, season=0):
        if week is None or season_type is None:
            current_week = self.nfl.schedule.current_week()
            week = current_week.week_value
            season_type = current_week.season_type

        op = Operation(shield.Viewer)
        games = op.viewer.league.games(first=16, week_season_value=season, week_season_type=season_type,
                                       week_week_value=week, order_by=GameOrderBy.gameTime,
                                       order_by_direction=OrderByDirection.ASC)
        game = games.edges.node
        self._standard_fields(game, shield.Game)
        self._standard_fields(game.home_team(), shield.Team)
        self._standard_fields(game.away_team(), shield.Team)
        games = self.query(op)
        return [game_edge.node for game_edge in games.viewer.league.games.edges]

    def by_id(self, id, select_fun: Callable[[shield.Game], None] = None):
        op = Operation(shield.Viewer)
        game = op.viewer.game(id=id)
        apply_selector(game, shield.Game, select_fun)
        return self.query(op).viewer.game

    def game_detail_id_for_id(self, id):
        return self.nfl.football.game_detail_id_for_id(id)


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
    def get_all(self, season_value=0, select_fun: Callable[[shield.Team], None] = None):
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


__all__ = [
    'ScheduleHelper',
    'GameHelper',
    'StandingsHelper',
    'TeamHelper',
    'GameDetailHelper'
]

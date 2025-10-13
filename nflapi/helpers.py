import datetime
from typing import List

import pendulum


class Helper:
    def __init__(self, nfl):
        self.nfl = nfl


class ScheduleHelper(Helper):
    def current_week(self, date: datetime.datetime = None) -> dict:
        if date is None:
            date = datetime.datetime.now(pendulum.UTC)
        else:
            date = date.astimezone(pendulum.UTC)
        return self.week(date)

    def week(self, date: datetime.datetime):
        return self.nfl.api.week_by_date(date)


class GameHelper(Helper):

    def week_games(self, week=None, season_type=None, season=None):
        if None in (week, season_type, season):
            current_week = self.nfl.schedule.current_week()
            week = current_week.week
            season_type = current_week.season_type
            season = current_week.season
        if None in (season, season_type, week):
            raise Exception("Season (%s), type (%s) or week (%s) unset", season, season_type, week)
        games = self.nfl.api.games_by_week(season, season_type=season_type, week=week)
        return games

    def by_id(self, game_id: str):
        return self.nfl.api.game_by_id(game_id)

    def game_detail(self, game_id: str, include_drive_chart: bool = False, include_replays: bool = False,
                    include_standings: bool = False, include_tagged_videos: bool = False):
        return self.nfl.api.game_details(game_id, include_drive_chart, include_replays, include_standings,
                                         include_tagged_videos)

    def game_detail_id_for_id(self, game_id: str):
        return self.nfl.api.game_detail_id_for_id(game_id)


class StandingsHelper(Helper):
    def get(self, week, season_type, season):
        result = self.nfl.api.standings_by_week(season, season_type, week)
        team_records = result.weeks[0].standings

        teams = {t.id: t for t in self.nfl.team.by_season(season)}

        return [(teams[team_record.team.id], team_record) for team_record in team_records]

    def current(self, date=None):
        current_week = self.nfl.schedule.current_week(date)
        week = current_week.week
        season_type = current_week.season_type
        season = current_week.season
        return self.get(week, season_type, season)


class TeamHelper(Helper):
    def get_all(self, season=0):
        return self.by_season(season)

    def lookup(self, abbreviation, season=0):
        for t in self.by_season(season):
            if t.abbreviation == abbreviation:
                return t
        return None

    def by_ids(self, ids: List[str], season=0):
        teams = list(filter(lambda t: t.id in ids, self.by_season(season)))
        return {t.id: t for t in teams}

    def by_season(self, season: int):
        if season == 0:
            season = self.nfl.schedule.current_week().season
        return self.nfl.api.teams_by_season(season).teams


class RosterHelper(Helper):
    def lookup(self, abbreviation, season: int = 0):
        for roster in self.all(season):
            if roster.team.abbreviation == abbreviation:
                return roster.persons
        return None

    def by_team_id(self, team_id: str, season: int = 0):
        for roster in self.all(season):
            if roster.team.id == team_id:
                return roster.persons
        return None

    def all(self, season: int = 0):
        if season == 0:
            season = self.nfl.schedule.current_week().season
        return self.nfl.api.rosters_by_season(season).rosters


class CombineHelper(Helper):
    def participants(self, year: int = 0):
        return self.nfl.api.combine_profiles_by_year(year)


class DraftHelper(Helper):
    def picks(self, year: int = 0):
        return self.nfl.api.draft_picks_by_year(year)


class PlayerHelper(Helper):
    def lookup(self, season: int = 0, player_name: str = None, team_id: str = None, status=None, first=100, after=None):
        raise Exception("Not available")

    def by_id(self, id: str):
        raise Exception("Not available")


__all__ = [
    'ScheduleHelper',
    'GameHelper',
    'StandingsHelper',
    'TeamHelper',
    'RosterHelper',
    'PlayerHelper',
    'CombineHelper',
    'DraftHelper',
]

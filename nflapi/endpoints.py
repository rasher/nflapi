import datetime
import logging
import pprint

import requests

from nflapi.const import *

logger = logging.getLogger(__name__)


def bs(x):
    """boolean string, convert boolean to string, lower case"""
    return str(x).lower()


class JsonWrapper:
    def __init__(self, json):
        self._raw = json

    def __getattr__(self, item):
        key = self.__to_camel(item)
        item = self.raw.get(key)
        return self.__class__.wrap_object(item)

    def __to_camel(self, s):
        camel = ''.join(word.title() for word in s.split('_'))
        return camel[0].lower() + camel[1:]

    @property
    def raw(self):
        return self._raw

    def __str__(self):
        return str(pprint.pformat(self.raw))

    def __repr__(self):
        return repr(self.raw)

    @classmethod
    def wrap_object(cls, o):
        if isinstance(o, dict):
            return JsonWrapper(o)
        elif isinstance(o, list):
            return [cls.wrap_object(i) for i in o]
        else:
            return o


class API:

    def __init__(self, auth, base_headers):
        self.auth = auth
        self.base_headers = base_headers
        self.game_detail_lut = {}

    def request(self, path, method='GET', **kwargs):
        url = API_HOST + path
        headers = dict(self.base_headers)
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        return JsonWrapper.wrap_object(requests.request(method, url, auth=self.auth, **kwargs).json())

    def game_by_id(self, game_id):
        path = FOOTBALL_GAME_BY_ID.format(game_id=game_id, with_external_ids='true')
        game = self.request(path)
        self.remember_game_detail_id(game)
        return game

    def game_detail_id_for_id(self, game_id):
        """
        These are cached. Fingers crossed they never change
        """
        if game_id in self.game_detail_lut:
            return self.game_detail_lut[game_id]
        result = self.game_by_id(game_id)
        game_detail_id = self._game_detail_id(result)
        if game_detail_id is not None:
            self.game_detail_lut[game_id] = game_detail_id
        return game_detail_id

    def games_by_week(self, season: int, season_type: str, week: int):
        path = FOOTBALL_GAMES_BY_WEEK.format(season=season, season_type=season_type, week=week, with_external_ids='true')
        return self.request(path).games

    def game_summaries_by_week(self, season: int, season_type: str, week: int):
        path = FOOTBALL_STATS_LIVE_GAME_SUMMARIES_BY_WEEK.format(season=season, season_type=season_type, week=week)
        return self.request(path).data

    def week_by_date(self, date: datetime.datetime):
        path = FOOTBALL_WEEK_BY_DATE.format(date=date)
        return self.request(path)

    def teams_by_season(self, season: int):
        path = EXPERIENCE1_TEAMS.format(season=season, limit=100)
        return self.request(path)

    def team_by_id(self, id: str):
        path = FOOTBALL_TEAM_BY_ID.format(id=id, with_external_ids='true')
        return self.request(path)

    def standings_by_week(self, season: int, season_type: str, week: int):
        path = FOOTBALL_STANDINGS_BY_WEEK.format(season=season, season_type=season_type, week=week, with_external_ids='true', limit=100)
        return self.request(path)

    def combine_profiles_by_year(self, year: int, combine_attendance: bool = True, limit: int = 1000):
        path = FOOTBALL_COMBINE_PROFILES_BY_YEAR.format(year=year, combine_attendance=combine_attendance, limit=limit)
        return self.request(path)

    def draft_picks_by_year(self, year: int, limit: int = 1000):
        path = FOOTBALL_DRAFT_PICKS_REPORT_BY_YEAR.format(year=year, limit=limit)
        return self.request(path)

    def rosters_by_season(self, season: int, limit: int = 1000):
        path = FOOTBALL_ROSTERS_BY_SEASON.format(season=season, limit=limit)
        return self.request(path)

    def game_details(self, game_id: str, include_drive_chart: bool = False, include_replays: bool = False,
                    include_standings: bool = False, include_tagged_videos: bool = False):
        path = EXPERIENCE2_GAMEDETAILS_BY_ID.format(id=game_id,
                                                    include_drive_chart=bs(include_drive_chart),
                                                    include_replays=bs(include_replays),
                                                    include_standings=bs(include_standings),
                                                    include_tagged_videos=bs(include_tagged_videos))
        return self.request(path)

    @staticmethod
    def _game_detail_id(game):
        return next((x.id for x in game.external_ids if x.source == "gamedetail"), None)

    def remember_game_detail_id(self, game):
        gdi = self._game_detail_id(game)
        if gdi is not None:
            self.game_detail_lut[game.id] = gdi

import datetime
import logging
import pprint
from typing import Optional, Dict

import pendulum
import requests
from sgqlc.endpoint.requests import RequestsEndpoint
from sgqlc.operation import Operation

from nflapi.const import *

logger = logging.getLogger(__name__)


class Shield:
    def __init__(self, auth, base_headers):
        self.__mangle_datetime()
        self.endpoint = RequestsEndpoint(API_HOST + ENDPOINT_SHIELD_V3, base_headers=base_headers, auth=auth)

    def query(self, op: Operation, variables: Optional[Dict] = None, return_json=False):
        logger.debug("Running query: %s", op)
        data = self.endpoint(op, variables)
        logger.debug("Return data: %s", data)
        if return_json:
            return (op + data), data
        else:
            return op + data

    def __mangle_datetime(self):
        """
        The Shield API insists that Z is the only acceptable timezone,
        so we beat the sgqlc datetime type into submission.
        """
        import sgqlc.types.datetime as DT

        def f(cls, value):
            if value is None:
                return None
            if isinstance(value, str):
                return value
            value = pendulum.instance(value)
            # This is the magic part. sgqlc uses .isoformat()
            return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        DT.DateTime.__to_json_value__ = classmethod(f)


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


class Football:

    def __init__(self, auth, base_headers):
        self.auth = auth
        self.base_headers = base_headers
        self.game_detail_lut = {}

    def request(self, path, method='GET', **kwargs):
        url = API_HOST + ENDPOINT_FOOTBALL_V2 + path
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
        path = FOOTBALL_TEAMS_BY_SEASON.format(season=season, limit=100)
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

    @staticmethod
    def _game_detail_id(game):
        return next((x.id for x in game.external_ids if x.source == "gamedetail"), None)

    def remember_game_detail_id(self, game):
        gdi = self._game_detail_id(game)
        if gdi is not None:
            self.game_detail_lut[game.id] = gdi

from .const import *
from .models import *


class Helper:
    def __init__(self, nfl):
        self.nfl = nfl

    def request(self, class_, *args, is_list=False, **kwargs):
        response = self.nfl.request(*args, **kwargs)
        if is_list:
            ret = []
            if 'data' in response:
                for obj in response['data']:
                    ret.append(class_(obj))
            return ret
        else:
            return class_(response)


class ScheduleHelper(Helper):
    name = 'schedule'
    CW = ENDPOINT_CURRENT_WEEK

    def current_week(self):
        return self.request(Week, self.CW)


class GameHelper(Helper):
    name = 'game'
    GAMES = ENDPOINT_GAMES

    def week(self, week):
        q = {
                "$query": {
                    "week.season": week.season,
                    "week.seasonType": week.seasonType,
                    "week.week": week.week
                    }
                }
        fs = """{
week { season, seasonType, week }
id,
type,
esbId,
gameTime,
gameStatus,
homeTeam { id, type, abbr },
visitorTeam { id, type, abbr },
homeTeamScore { type, pointsTotal },
visitorTeamScore { type, pointsTotal },
venue,
networkChannels,
        }"""
        return self.request(Game, self.GAMES, is_list=True, params={'s': q, 'fs': fs})


__all__ = [
    'ScheduleHelper',
    'GameHelper',
]

from .const import *
from .models import *


class Helper:
    def __init__(self, nfl):
        self.nfl = nfl

    def request(self, class_, *args, **kwargs):
        response = self.nfl.request(*args, **kwargs)
        if isinstance(class_, list):
            return Pager(class_[0], response)
        else:
            return class_(response)


class ScheduleHelper(Helper):
    name = 'schedule'
    CW = ENDPOINT_CURRENT_WEEK

    def current_week(self):
        return self.request(Week, self.CW)


class TeamHelper(Helper):
    name = 'team'
    TEAMS = ENDPOINT_TEAMS

    def get(self, abbr):
        # We cannot query a specific team because the API is "special"
        q = {
                "$query": {
                    "season": 2018,
                    },
                }
        fs = """
{
    id,
    season,
    fullName,
    nickName,
    cityStateRegion,
    abbr,
    teamType,
    venue{name},
    conference{abbr},
    division{abbr},
    branding
}
"""
        team = list(filter(lambda t: t.abbr == abbr.upper(),
                           self.request([Team], self.TEAMS, s=q, fs=fs)))
        return team[0] if len(team) == 1 else None


class StandingsHelper(Helper):
    name = 'standings'
    TEAMS = ENDPOINT_TEAMS

    def current(self):
        week = self.nfl.schedule.current_week()
        return self.get(week.season, week.seasonType), week

    def get(self, season, season_type='REG'):
        q = {
            "$query": {
                "standings": {
                    "$query": {
                        }
                    },
                "$takeLast": 1
                },
            "$take": 40
            }
        fs = """
{
    id,
    season,
    fullName,
    nickName,
    cityStateRegion,
    abbr,
    teamType,
    conference { abbr },
    division { abbr },
    standings {
        overallWins,
        overallWinPct,
        overallLosses,
        overallTies,
        divisionWins,
        divisionLosses,
        clinchDivision,
        clinchDivisionAndHomefield,
        clinchWildcard,
        clinchPlayoff,
        conferenceRank,
        divisionRank
    }
}"""
        q['$query']['season'] = season
        q['$query']['standings']['$query']['week.seasonType'] = season_type
        return self.request([Team], self.TEAMS, s=q, fs=fs)


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
        return self.request([Game], self.GAMES, params={'s': q, 'fs': fs})


__all__ = [
    'ScheduleHelper',
    'GameHelper',
    'StandingsHelper',
    'TeamHelper',
]

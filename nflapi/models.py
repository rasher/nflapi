class NFLModel:
    _fields = {}

    def __init__(self, json):
        self._json = json
        for field, class_ in self._fields.items():
            if field in json:
                setattr(self, field, class_(json[field]))

    def __getattr__(self, attrname):
        return self._json[attrname]

    def __repr__(self):
        return "<{}: {!r}>".format(type(self).__name__, self._json)


class Week(NFLModel):
    pass


class GameStatus(NFLModel):
    pass


class TeamScore(NFLModel):
    pass


class Team(NFLModel):
    pass


class Game(NFLModel):
    _fields = {
            'gameStatus': GameStatus,
            'visitorTeamScore': TeamScore,
            'homeTeamScore': TeamScore,
            'visitorTeam': Team,
            'homeTeam': Team,
            }


__all__ = [
    'Week',
    'Game',
    'GameStatus',
    'TeamScore',
    'Team',
]

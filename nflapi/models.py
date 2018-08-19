import pendulum

class NFLModel:
    _fields = {}
    defaultJson = None

    def __init__(self, json):
        if json is None and self.defaultJson is None:
            raise Exception(("{} initialised with empty json and no default " +
                    "available").format(type(self).__name__))
        self._json = json if json is not None else self.defaultJson
        for field, class_ in self._fields.items():
            if field in json:
                setattr(self, field, class_(json[field]))

    def __getattr__(self, attrname):
        if attrname in self._json:
            return self._json[attrname]

    def __repr__(self):
        return "<{}: {!r}>".format(type(self).__name__, self._json)


class Week(NFLModel):
    pass


class GameStatus(NFLModel):
    pass


class TeamScore(NFLModel):
    defaultJson = {'pointsTotal': 0}


class Team(NFLModel):
    pass


class GameTime(NFLModel):
    """Ideally this would subclass pendulum.DateTime"""

    def __init__(self, data, *args, **kwargs):
        super().__init__(data)
        self.pt = pendulum.parse(data)

    def __getattr__(self, name):
        return getattr(self.pt, name)

    def __format__(self, fmt):
        return self.pt.__format__(fmt)


class Game(NFLModel):
    _fields = {
            'gameStatus': GameStatus,
            'visitorTeamScore': TeamScore,
            'homeTeamScore': TeamScore,
            'visitorTeam': Team,
            'homeTeam': Team,
            'gameTime': GameTime,
            }


__all__ = [
    'Week',
    'Game',
    'GameStatus',
    'TeamScore',
    'Team',
]

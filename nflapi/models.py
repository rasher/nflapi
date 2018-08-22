import pendulum


class NFLModel:
    _fields = {}
    defaultJson = None

    def __init__(self, json):
        if json is None and self.defaultJson is None:
            raise Exception(("{} initialised with empty json and no default "
                             "available").format(type(self).__name__))
        self._json = json if json is not None else self.defaultJson
        for field, class_ in self._fields.items():
            if field in json:
                if isinstance(class_, list):
                    setattr(self, field, Pager(class_[0], json[field]))
                else:
                    setattr(self, field, class_(json[field]))

    def __getattr__(self, attrname):
        if attrname in self._json:
            return self._json[attrname]

    def __repr__(self):
        return "<{}: {!r}>".format(type(self).__name__, self._json)


class Pager(NFLModel):
    def __init__(self, class_, json):
        self.json = json
        self.list = []
        for data in json['data']:
            self.list.append(class_(data))

    def __iter__(self):
        return self.list.__iter__()

    def __next__(self):
        return self.list.__next__()

    def __len__(self):
        return len(self.list)

    def __getitem__(self, index):
        return self.list[index]

    def __setitem__(self, index, value):
        self.list[index] = value

    def __delitem__(self, index):
        del(self.list[index])


class Abbreviated:
    def __hash__(self):
        return hash(str(self.abbr))

    def __eq__(self, other):
        return str(self.abbr) == str(other.abbr)


class Week(NFLModel):
    pass


class GameStatus(NFLModel):
    pass


class TeamScore(NFLModel):
    defaultJson = {'pointsTotal': 0}


class Conference(NFLModel, Abbreviated):
    @property
    def fullName(self):
        """
        For some reason you can't make the API return the fullName
        """
        fullNames = {
                'AFC': 'American Football Conference',
                'NFC': 'National Football Conference',
                }
        return fullNames[self.abbr]


class Division(NFLModel, Abbreviated):
    @property
    def fullName(self):
        """
        For some reason you can't make the API return the fullName
        """
        fullNames = {
                'ACE': 'AFC East',
                'ACN': 'AFC North',
                'ACS': 'AFC South',
                'ACW': 'AFC West',
                'NCE': 'NFC East',
                'NCN': 'NFC North',
                'NCS': 'NFC South',
                'NCW': 'NFC West',
                }
        return fullNames[self.abbr]


class Standings(NFLModel):
    pass


class Venue(NFLModel):
    pass


class Team(NFLModel, Abbreviated):
    _fields = {
            'conference': Conference,
            'division': Division,
            'standings': [Standings],
            'venue': Venue,
            }


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
    'Pager',
    'Week',
    'Game',
    'GameStatus',
    'TeamScore',
    'Team',
]

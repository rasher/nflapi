class NFLModel:
    def __init__(self, json):
        self._json = json

    def __getattr__(self, attrname):
        return self._json[attrname]

    def __repr__(self):
        return "<{}: {!r}>".format(type(self).__name__, self._json)

class Week(NFLModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

__all__ = [
    'Week',
]

from .const import *
from .models import *

class Helper:
    def __init__(self, nfl):
        self.nfl = nfl
        pass

    def request(self, class_, *args, **kwargs):
        return class_(self.nfl.request(*args, **kwargs))

class ScheduleHelper(Helper):
    name = 'schedule'
    CW = ENDPOINT_CURRENT_WEEK

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def current_week(self):
        return self.request(Week, self.CW)

__all__ = [
    'ScheduleHelper',
]

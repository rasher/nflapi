import logging
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


class Football:

    def __init__(self, auth, base_headers):
        self.auth = auth
        self.base_headers = base_headers
        self.game_detail_lut = {}

    def request(self, path, method='GET', **kwargs):
        url = API_HOST + ENDPOINT_FOOTBALL_V2 + path
        return requests.request(method, url, auth=self.auth, **kwargs).json()

    def game_by_id(self, game_id):
        path = FOOTBALL_GAME_BY_ID.format(game_id=game_id, with_external_ids='true')
        result = self.request(path)
        return result

    def game_detail_id_for_id(self, game_id):
        """
        These are cached. Fingers crossed they never change
        """
        if game_id in self.game_detail_lut:
            return self.game_detail_lut[game_id]
        result = self.game_by_id(game_id)
        game_detail_id = next((x["id"] for x in result["externalIds"] if x["source"] == "gamedetail"), None)
        if game_detail_id is not None:
            self.game_detail_lut[game_id] = game_detail_id
        return game_detail_id

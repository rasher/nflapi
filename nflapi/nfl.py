import logging
from os import environ
from pprint import pformat

import pendulum
import requests
from fcache.cache import FileCache
from requests.exceptions import HTTPError

from .const import *
from .endpoints import Football, Shield
from .helpers import *
from .__version__ import __version__

logger = logging.getLogger(__name__)

EPOCH = pendulum.datetime(1970, 1, 1)


class NFLClientCredentials(requests.auth.AuthBase):
    """
    A requests Auth object that maintains a token for the nfl.com api

    The token is cached using a file cache that may or may not work
    across multiple processes. The worst that can happen is that it
    is refreshed unnecessarily.
    """

    def __init__(self, cache_name: str = 'nflapi'):
        self.cache = FileCache(cache_name, flag='cs')

    def __call__(self, r: requests.Request):
        r.headers['Authorization'] = self.__get_token(ua=r.headers.get('User-Agent', None))
        return r

    def __get_token(self, ua):
        expire = self.cache.get('expire', EPOCH) or EPOCH  # In case we accidentally set it to None
        refresh_token = self.cache.get('refreshToken', None)
        access_token = self.cache.get('accessToken', None)

        logging.debug("Expire is %s", expire)
        token = None
        if access_token is not None and expire > pendulum.now():
            logger.debug("Using stored token")
            token = access_token
        if token is None and refresh_token is not None:
            token = self.__refresh_token(refresh_token, ua)
        if token is None:
            token = self.__get_and_store_new_token(ua)
        return 'Bearer {token}'.format(token=token)

    def __refresh_token(self, refresh_token: str, ua: str) -> str:
        logger.debug("Using refresh token")
        extra_data = {
            'refreshToken': refresh_token,
        }
        try:
            js = self.__token_request(ENDPOINT_IDENTITY_V3_TOKEN_REFRESH, extra_data, ua)
            return js['accessToken']
        except Exception as e:
            logging.debug("Could not refresh token", exc_info=1)

    def __get_and_store_new_token(self, ua: str):
        logger.debug("Retrieving new access token")
        js = self.__token_request(ENDPOINT_IDENTITY_V3_TOKEN, {}, ua)
        return js['accessToken']

    def __token_request(self, path, extra_data, ua):
        data = {
            'clientKey': environ['NFL_CLIENT_KEY'],
            'clientSecret': environ['NFL_CLIENT_SECRET'],
            'deviceId': '',
            'deviceInfo': '',
            'networkType': 'other',
            'peacockUUID': 'undefined',
        }
        data.update(extra_data)

        headers = {'User-Agent': ua}
        logger.debug('Request: POST %s, data=<%s>', path, pformat(data))

        url = API_HOST + path
        logger.debug('Request headers: %s', pformat(headers))
        response = requests.request('POST', url, data=data,
                                    headers=headers)
        try:
            js = response.json()
            response.raise_for_status()
            logger.debug('Response: %s', pformat(js))
            self.cache['accessToken'] = js['accessToken']
            self.cache['refreshToken'] = js['refreshToken']
            self.cache['expire'] = pendulum.from_timestamp(js['expiresIn'])
            logger.debug('Response: %s', pformat(js))
            logger.debug('Expire: %s', self.cache['expire'])
            return js
        except HTTPError as e:
            raise Exception("Unsuccessful response: %r" % response.data) from e
        except ValueError as e:
            raise Exception("Response from API was not json: %s"
                            % response.data) from e


class NFL:
    def __init__(self, ua: str, auth: requests.auth.AuthBase = False):
        self.__version__ = __version__
        self.ua = ua
        base_headers = {
            'X-Domain-Id': '100',
            'User-Agent': self.ua,
        }
        if auth is False:
            auth = NFLClientCredentials('nflapi')
        self.football = Football(auth, base_headers)
        self.shield = Shield(auth, base_headers)

        self.team = TeamHelper(self)
        self.schedule = ScheduleHelper(self)
        self.standings = StandingsHelper(self)
        self.game = GameHelper(self)
        self.game_detail = GameDetailHelper(self)
        self.roster = RosterHelper(self)
        self.player = PlayerHelper(self)
        self.combine = CombineHelper(self)
        self.draft = DraftHelper(self)

    def query(self, *args, **kwargs):
        logger.info("Using deprecated method")
        return self.shield.query(*args, **kwargs)

import logging

import pendulum
import requests

from .const import *

logger = logging.getLogger(__name__)

class NFL:
    __AUTH_TOKEN = None
    __AUTH_TOKEN_EXPIRE = None

    def __init__(self, ua):
        self.ua = ua

    def __update_token(self):
        logger.debug('Updating auth token')
        data = {
            'grant_type': 'client_credentials'
                }
        response = self.__request(ENDPOINT_REROUTE, method='POST', data=data, token_request=True)
        self.__AUTH_TOKEN = '{token_type} {access_token}'.format(**response)
        self.__AUTH_TOKEN_EXPIRE = pendulum.now().add(seconds=response['expires_in']-2)
        logger.debug('Updated token: %s - expires %s', self.__AUTH_TOKEN, self.__AUTH_TOKEN_EXPIRE)

    def __request(self, path, method='GET', params=None, data=None, token_request=False, add_headers=None):
        logger.debug('Request: %s %s, params=%r, data=%r', method, path, params, data)
        now = pendulum.now()

        if not token_request and (self.__AUTH_TOKEN is None or now > self.__AUTH_TOKEN_EXPIRE):
            self.__update_token()

        headers = {
            'Origin': 'http://www.nfl.com',
            'X-Domain-Id': '100',
            'User-Agent': self.ua,
            'DNT': '1',
            'Accept': '*/*',
            'Referer': 'http://www.nfl.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        }

        if self.__AUTH_TOKEN:
            headers['Authorization'] = self.__AUTH_TOKEN

        if add_headers:
            headers.update(add_headers)

        if method == 'POST':
            headers['Content-type'] = 'application/x-www-form-urlencoded'

        url = API_HOST + path
        logger.debug('Request headers %r', headers)
        response = requests.request(method, url, data=data, params=params, headers=headers)
        response.raise_for_status()
        try:
            json = response.json()
            logger.debug('Response: %r', json)
            return json
        except ValueError as e:
            raise Exception("Response from API was not json") from e


import requests


class RestApiBase:

    def __init__(self, session=None):
        self._session = session if session else requests.session()

    def _get(self, url, params={}):
        response = self._session.get(url, params=params)
        return response

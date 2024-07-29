import logging
import re
from urllib.parse import urlparse

import requests

from galaxykit.utils import GalaxyClientError

logger = logging.getLogger(__name__)


class GatewayAuthClient:
    def __init__(self, auth, galaxy_root):
        self.auth = auth
        self.galaxy_root = galaxy_root
        self.headers = {}
        parsed_url = urlparse(self.galaxy_root)
        self.url = f"{parsed_url.scheme}://{parsed_url.hostname}"
        if parsed_url.port is not None and (
            (parsed_url.scheme == "https" and parsed_url.port != 443)
            or (parsed_url.scheme == "http" and parsed_url.port != 80)
        ):
            self.url += ":" + str(parsed_url.port)
        self.host = parsed_url.hostname
        self.login_url = f"{self.url}/api/gateway/v1/login/"
        self.logout_url = f"{self.url}/api/gateway/v1/logout/"
        self.gw_cookies = None
        self.csrftoken = None
        self.response = None
        self.session = None

    @property
    def cookies(self):
        return dict(self.session.cookies)

    def login(self):
        with requests.Session() as session:
            self.session = session
            session.verify = False
            self.response = self._gw_login(session)
            self.headers = self.get_cookies_from_response(self.response)
            return self.response

    def logout(self):
        self.session.headers = self.headers
        self.session.headers.update({"Origin": self.url})
        self.session.headers.update({"Referer": f"{self.url}/overview"})
        self.session.headers.update({"X-CSRFToken": self.csrftoken})
        self.session.post(self.logout_url)
        return self.session

    def _gw_login(self, session):
        self.header_csfrtoken = self.get_header_csfrtoken(session)
        self.gw_cookies = session.cookies
        session.headers.update({"Referer": f"{self.url}/login"})
        session.headers.update({"Set-Cookie": f"csrftoken={self.header_csfrtoken}"})
        session.headers.update({"X-Csrftoken": self.header_csfrtoken})
        data = {
            "username": (None, self.auth["username"]),
            "password": (None, self.auth["password"]),
        }
        response = session.post(self.login_url, files=data, allow_redirects=False)
        if response.status_code == 401:
            raise GalaxyClientError(
                "401 Unauthorized. Incorrect username or password.",
                response=response,
            )
        return response

    def get_header_csfrtoken(self, session):
        response = session.get(self.login_url)
        response.raise_for_status()
        token_pattern = r'"csrfToken":\s+?"(.+?)"'
        match = re.search(token_pattern, response.text)
        return match.group(1)

    def get_cookies_from_response(self, response):
        self.csrftoken = response.cookies["csrftoken"]
        gateway_sessionid = response.cookies["gateway_sessionid"]
        return {
            "Accept": "application/json",
            "Cookie": f"csrftoken={self.csrftoken}; gateway_sessionid={gateway_sessionid}",
            "X-CSRFToken": self.csrftoken,
        }

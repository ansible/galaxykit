import logging
import re
from urllib.parse import urlparse

import requests

from galaxykit.github_social_auth_client import AuthenticationFailed

logger = logging.getLogger(__name__)



class GatewayAuthClient:
    def __init__(self, auth, galaxy_root):
        self.auth = auth
        self.galaxy_root = galaxy_root
        self.headers = {}
        parsed_url = urlparse(self.galaxy_root)
        self.url = f"{parsed_url.scheme}://{parsed_url.hostname}"
        self.host = parsed_url.hostname
        self.login_url = f"{self.url}/api/gateway/v1/login/"
        self.gw_cookies = None

    def login(self):
        with requests.Session() as session:
            session.verify = False
            self.headers = self._gw_login(session)

    def _gw_login(self, session):
        header_csfrtoken = self.get_header_csfrtoken(session)
        self.gw_cookies = session.cookies
        session.headers.update({"Referer": f"{self.url}/login"})
        session.headers.update({"Set-Cookie": f"csrftoken={header_csfrtoken}"})
        session.headers.update({"X-Csrftoken": header_csfrtoken})
        data = {"username": (None, self.auth["username"]),
                "password": (None, self.auth["password"]),}
        response = session.post(self.login_url, files=data, allow_redirects=False)

        return get_cookies_from_response(response)

    def get_header_csfrtoken(self, session):
        response = session.get(self.login_url)
        response.raise_for_status()
        token_pattern = r'csrfToken:\s+?"(.+?)"'
        match = re.search(token_pattern, response.text)
        return match.group(1)

def get_cookies_from_response(response):
    csrftoken = response.cookies["csrftoken"]
    gateway_sessionid = response.cookies["gateway_sessionid"]
    return {
        "Accept": "application/json",
        "Cookie": f"csrftoken={csrftoken}; gateway_sessionid={gateway_sessionid}",
    }

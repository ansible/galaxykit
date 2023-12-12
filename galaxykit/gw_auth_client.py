import logging
import re
import uuid
from urllib.parse import urlparse, to_bytes

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
        self.login_url = f"{self.url}/api/gateway/v1/login/"
        self.gw_cookies = None

    def login(self):
        with requests.Session() as session:
            session.verify = False
            self.headers = self._gw_login(session)

    def _gw_login(self, session):
        header_csfrtoken = self.get_header_csfrtoken(session)
        self.gw_cookies = session.cookies
        login_data = {
            'username': 'admin',
            'password': None
        }
        session.headers.update({"Referer": f"{self.url}/login"})
        session.headers.update({"Content-Type": "multipart/form-data"})
        session.headers.update({"Cookie": f"csrftoken={header_csfrtoken}"})
        session.headers.update({"Set-Cookie": f"csrftoken={header_csfrtoken}"})
        session.headers.update({"X-Csrftoken": header_csfrtoken})

        form = []
        boundary = "--------------------------%s" % uuid.uuid4().hex
        part_boundary = b"--" + boundary.encode("utf8")

        form.extend(
            [
                part_boundary,
                b'Content-Disposition: form-data; name="username"',
                b"admin",
            ]
        )

        form.extend(
            [
                part_boundary,
                b'Content-Disposition: form-data; name="password"',
                b"1n5ecD90L1d4N",
            ]
        )

        data = b"\r\n".join(form)


        response = session.post(self.login_url, data=login_data, cookies=self.gw_cookies)

        response = session.get(
            self.login_url, cookies=self.gw_cookies, allow_redirects=False
        )
        response.raise_for_status()
        next_url = response.headers["location"]
        response = session.get(
            next_url, cookies=self.github_cookies, allow_redirects=False
        )
        response.raise_for_status()
        try:
            complete_url = response.headers["location"]
        except KeyError:
            logger.debug(
                "Too many requests to GitHub login service. Re-authorization needed"
            )
            raise AuthenticationFailed("Too many requests. Re-authorization needed.")
        response = session.get(
            complete_url, cookies=self.github_cookies, allow_redirects=False
        )
        response.raise_for_status()
        return get_cookies_from_response(response)

    def _reauthenticate(self, session):
        self.github_cookies = self._github_login(session)
        response = session.get(
            self.login_url, cookies=self.github_cookies, allow_redirects=False
        )
        response.raise_for_status()
        next_url = response.headers["location"]
        response = session.get(
            next_url, cookies=self.github_cookies, allow_redirects=False
        )
        response.raise_for_status()
        new_authenticity_token = extract_authenticity_token(response.text)
        session.headers.update({"Referer": next_url})
        session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        r = session.post(
            self.GITHUB_AUTH_URL,
            data={
                "authorize": 1,
                "authenticity_token": new_authenticity_token,
                "redirect_uri_specified": True,
                "client_id": get_client_id(next_url),
                "redirect_uri": f"{self.url}/complete/github/",
                "scope": "read:org,user:email",
                "state": get_state_from_url(next_url),
                "authorize": 1,
            },
            cookies=self.github_cookies,
        )
        complete_url = extract_complete_url(r.text)
        response = session.get(
            complete_url, cookies=self.github_cookies, allow_redirects=False
        )
        response.raise_for_status()
        return get_cookies_from_response(response)

    def _github_login(self, session):
        authenticity_token = self.get_authenticity_token(session)
        login_data = {
            "commit": "Sign in",
            "login": self.auth["username"],
            "password": self.auth["password"],
            "authenticity_token": authenticity_token,
        }
        session.cookies.set(
            "_device_id", "4066e3c5dbc8a65829b6a1b8eecbb476", domain="github.com"
        )
        session.post(self.GITHUB_SESSION_URL, data=login_data, allow_redirects=False)
        return session.cookies

    def get_header_csfrtoken(self, session):
        response = session.get(self.login_url)
        response.raise_for_status()
        token_pattern = r'csrfToken:\s+?"(.+?)"'
        match = re.search(token_pattern, response.text)
        return match.group(1)


def extract_authenticity_token(text):
    token_pattern = r'name="authenticity_token" value="(.+?)"'
    match = re.search(token_pattern, text)
    return match.group(1)


def get_state_from_url(url):
    state_pattern = r"&state=(.+?)&"
    match = re.search(state_pattern, url)
    return match.group(1)


def extract_complete_url(text):
    token_pattern = r'data-url="(.+?)"'
    match = re.search(token_pattern, text)
    return match.group(1)


def get_client_id(url):
    state_pattern = r"client_id=(.+?)&"
    match = re.search(state_pattern, url)
    return match.group(1)


def get_cookies_from_response(response):
    csrftoken = response.cookies["csrftoken"]
    return {
        "Accept": "application/json",
        "X-CSRFToken": csrftoken,
        "Cookie": f"csrftoken={csrftoken}; sessionid={sessionid}",
    }

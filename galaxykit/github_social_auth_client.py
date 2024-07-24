import logging
import re
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class AuthenticationFailed(Exception):
    def __init__(self, message):
        self.message = message


class GitHubSocialAuthClient:
    GITHUB_SESSION_URL = "https://github.com/session"
    GITHUB_LOGIN_URL = "https://github.com/login"
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"

    def __init__(self, auth, galaxy_root):
        self.auth = auth
        self.galaxy_root = galaxy_root
        self.headers = {}
        parsed_url = urlparse(self.galaxy_root)
        self.url = f"{parsed_url.scheme}://{parsed_url.hostname}"
        if parsed_url.scheme == 'http' and parsed_url.port != 80:
            self.url += ':' + str(parsed_url.port)
        elif parsed_url.scheme == 'https' and parsed_url.port != 443:
            self.url += ':' + str(parsed_url.port)
        self.login_url = f"{self.url}/login/github/"
        self.github_cookies = None

    def login(self):
        with requests.Session() as session:
            try:
                self.headers = self._beta_galaxy_stage_login(session)
            except AuthenticationFailed:
                # if we get here, we have exceeded the GitHub rate limit and
                # need to re-authenticate
                self.headers = self._reauthenticate(session)

    def _beta_galaxy_stage_login(self, session):
        self.github_cookies = self._github_login(session)
        logger.debug(f'github cookies {dict(self.github_cookies)}')
        response = session.get(
            self.login_url, cookies=self.github_cookies, allow_redirects=False
        )
        response.raise_for_status()
        next_url = response.headers["location"]
        logger.debug(f'github redirect {next_url}')
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
        logger.debug(f'complete url {complete_url}')

        # we expect this to just simply login ... ?
        response = session.get(
            complete_url, cookies=self.github_cookies, allow_redirects=False
        )
        response.raise_for_status()
        cookies = get_cookies_from_response(response)
        logger.debug(f'new github cookies {dict(cookies)}')
        return cookies

    def _reauthenticate(self, session):
        self.github_cookies = self._github_login(session)
        logger.debug(f'cookies after github login {self.github_cookies}')
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
        logger.debug(f'github login authenticity token {authenticity_token}')
        login_data = {
            "commit": "Sign in",
            "login": self.auth["username"],
            "password": self.auth["password"],
            "authenticity_token": authenticity_token,
        }
        session.cookies.set(
            "_device_id", "4066e3c5dbc8a65829b6a1b8eecbb476", domain="github.com"
        )
        resp = session.post(self.GITHUB_SESSION_URL, data=login_data, allow_redirects=False)
        logger.debug(f'github login POST response {resp.status_code} {resp.reason}')
        if 'Incorrect username or password' in resp.text:
            raise Exception('github auth failed with incorrect username&password')
        return session.cookies

    def get_authenticity_token(self, session):
        response = session.get(self.GITHUB_LOGIN_URL)
        response.raise_for_status()
        token_pattern = r'name="authenticity_token" value="(.+?)"'
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
    sessionid = response.cookies["sessionid"]
    return {
        "Accept": "application/json",
        "X-CSRFToken": csrftoken,
        "Cookie": f"csrftoken={csrftoken}; sessionid={sessionid}",
    }

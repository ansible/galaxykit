import re
from urllib.parse import urlparse

import requests


def get_authenticity_token(session):
    response = session.get("https://github.com/login")
    response.raise_for_status()
    token_pattern = r'name="authenticity_token" value="(.+?)"'
    match = re.search(token_pattern, response.text)
    return match.group(1)


class GitHubSocialAuthClient:
    def __init__(self, auth, galaxy_root):
        self.auth = auth
        self.galaxy_root = galaxy_root
        self.headers = {}

    def login(self):
        with requests.Session() as session:
            authenticity_token = get_authenticity_token(session)

            login_data = {
                'commit': 'Sign in',
                'login': self.auth["username"],
                'password': self.auth["password"],
                'authenticity_token': authenticity_token
            }
            session.post('https://github.com/session', data=login_data)
            github_cookies = session.cookies

            parsed_url = urlparse(self.galaxy_root)
            url = f"{parsed_url.scheme}://{parsed_url.hostname}"
            login_url = f"{url}/login/github/"

            response = session.get(login_url, cookies=github_cookies, allow_redirects=False)
            response.raise_for_status()
            next_url = response.headers["location"]

            response = session.get(next_url, cookies=github_cookies, allow_redirects=False)
            response.raise_for_status()
            next_url = response.headers["location"]

            response = session.get(next_url, cookies=github_cookies, allow_redirects=False)
            response.raise_for_status()
            csrftoken = response.cookies["csrftoken"]
            sessionid = response.cookies["sessionid"]

            headers = {
                'Accept': 'application/json',
                'X-CSRFToken': csrftoken,
                'Cookie': f'csrftoken={csrftoken}; sessionid={sessionid}'
            }
            self.headers = headers

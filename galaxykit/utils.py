"""Utility functions"""
import base64
import logging
import json
import time
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class TaskWaitingTimeout(Exception):
    pass


class TaskFailed(Exception):
    def __init__(self, message):
        self.message = message


class GalaxyClientError(Exception):
    pass


def wait_for_task(api_client, task, timeout=300, raise_on_error=False):
    if isinstance(task, dict):
        url = urljoin(api_client.galaxy_root, task["task"])
    else:
        task = json.loads(task.text)
        url = urljoin(api_client.galaxy_root, task["task"])

    ready = False
    wait_until = time.time() + timeout
    while not ready:
        if wait_until < time.time():
            raise TaskWaitingTimeout()
        try:
            resp = api_client.get(url)
            if resp["state"] == "failed":
                logger.error(resp["error"])
                if raise_on_error:
                    raise TaskFailed(resp["error"])
        except GalaxyClientError as e:
            if "500" not in str(e):
                raise
        else:
            ready = resp["state"] not in ("running", "waiting")
        time.sleep(5)
    return resp


class BasicAuthToken(object):
    token_type = "Basic"

    def __init__(self, username, password=None):
        self.username = username
        self.password = password
        self._token = None

    @staticmethod
    def _encode_token(username, password):
        token = "%s:%s" % (username, password)
        b64_val = base64.b64encode(
            str.encode(token, encoding="utf-8", errors="surrogate_or_strict")
        )
        return b64_val.decode("utf-8")

    def get(self):
        if self._token:
            return self._token
        self._token = self._encode_token(self.username, self.password)

        return self._token

    def headers(self):
        headers = {"Authorization": "%s %s" % (self.token_type, self.get())}
        return headers

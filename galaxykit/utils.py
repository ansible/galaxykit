"""Utility functions"""
import logging
import json
import time
from urllib import request
from urllib.parse import urljoin

import requests
from simplejson.errors import JSONDecodeError

logger = logging.getLogger(__name__)


class TaskWaitingTimeout(Exception):
    pass


class TaskFailed(Exception):
    def __init__(self, message):
        self.message = message


class GalaxyClientError(Exception):
    response = None
    json = None

    @property
    def status_code(self):
        if self.response:
            return self.response.status_code
        else:
            return None

    def __init__(self, *args, **kwargs):
        skip = 0
        if args and isinstance(args[0], requests.Response):
            self.response = args[0]
            skip = 1
        elif "response" in kwargs:
            self.response = kwargs.pop("response")
        if "json" in kwargs:
            self.json = kwargs.pop("json")
        elif self.response:
            try:
                self.json = self.response.json()
            except JSONDecodeError:
                pass
        super().__init__(*args[skip:], **kwargs)


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

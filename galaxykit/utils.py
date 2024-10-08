"""Utility functions"""

import logging
import re
import time
from urllib.parse import urljoin

import requests
from simplejson.errors import JSONDecodeError

from .constants import SLEEP_SECONDS_POLLING


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


def wait_for_task(
    api_client, resp, task_id=None, timeout=300, raise_on_error=False, version="v3"
):
    if task_id:
        url = f"{version}/tasks/{task_id}/"
    else:
        url = urljoin(api_client.galaxy_root, resp["task"])

    ready = False
    wait_until = time.time() + timeout
    while not ready:
        if wait_until < time.time():
            raise TaskWaitingTimeout()
        try:
            resp = api_client.get(url)
            if version == "v1":
                if resp["results"][0]["state"] == "failed":
                    logger.error(resp["error"])
                    if raise_on_error:
                        raise TaskFailed(resp["error"])
            else:
                if resp["state"] == "failed":
                    logger.error(resp["error"])
                    if raise_on_error:
                        raise TaskFailed(resp["error"])
        except GalaxyClientError as e:
            if "500" not in str(e):
                raise
        else:
            if version == "v1":
                ready = resp["results"][0]["state"] not in ("running", "waiting")
            else:
                ready = resp["state"] not in ("running", "waiting")

        time.sleep(SLEEP_SECONDS_POLLING)
    return resp


def pulp_href_to_id(href):
    uuid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

    for section in href.split("/"):
        if re.match(uuid_regex, section):
            return section

    return None


def wait_for_url(client, url, timeout_sec=6000):
    """Wait until url stops returning a 404."""
    ready = False
    res = None
    wait_until = time.time() + timeout_sec
    while not ready:
        if wait_until < time.time():
            raise TaskWaitingTimeout()
        try:
            res = client.get(url)
        except GalaxyClientError as e:
            if "404" not in str(e):
                raise
            time.sleep(SLEEP_SECONDS_POLLING)
        else:
            ready = True
    return res

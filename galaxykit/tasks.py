from time import sleep
from .constants import SLEEP_SECONDS_POLLING
from .constants import POLLING_MAX_ATTEMPTS


def get_tasks(client, only_running=False):
    tasks_url = f"pulp/api/v3/tasks/?ordering=-pulp_created"
    if only_running:
        tasks_url += f"&state__in=waiting,running"

    return client.get(tasks_url)


def get_task(client, task_id):
    tasks_url = f"pulp/api/v3/tasks/{task_id}/"
    return client.get(tasks_url)


def wait_task(client, task_id, sleep_seconds=None, max_attempts=None):
    if sleep_seconds is None:
        sleep_seconds = SLEEP_SECONDS_POLLING
    if max_attempts is None:
        max_attempts = POLLING_MAX_ATTEMPTS

    task = get_task(client, task_id)

    while task["state"] not in ["completed", "failed", "canceled"]:
        if max_attempts != None:
            max_attempts -= 1
            if max_attempts == 0:
                break

        sleep(sleep_seconds)
        task = get_task(client, task_id)

    if task["state"] != "completed":
        raise ValueError(task)

    return task


def wait_all(client, sleep_seconds=None, max_attempts=10):
    if sleep_seconds is None:
        sleep_seconds = SLEEP_SECONDS_POLLING
    if max_attempts is None:
        max_attempts = POLLING_MAX_ATTEMPTS

    tasks = get_tasks(client, only_running=True)

    while tasks and tasks["results"]:
        if max_attempts != None:
            max_attempts -= 1
            if max_attempts == 0:
                break

        sleep(sleep_seconds)
        tasks = get_tasks(client, only_running=True)

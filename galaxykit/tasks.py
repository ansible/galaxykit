import re
from time import sleep


def get_tasks(client, only_running=False):
    tasks_url = f"pulp/api/v3/tasks/?ordering=-pulp_created"
    if only_running:
        tasks_url += f"&state__in=waiting,running"

    return client.get(tasks_url)


def get_task(client, task_id):
    tasks_url = f"pulp/api/v3/tasks/{task_id}/"
    return client.get(tasks_url)


def wait_task(client, task_id, sleep_seconds=10, max_attempts=10):
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


def wait_all(client, sleep_seconds=10, max_attempts=10):
    tasks = get_tasks(client, only_running=True)

    while tasks and tasks["results"]:
        if max_attempts != None:
            max_attempts -= 1
            if max_attempts == 0:
                break

        sleep(sleep_seconds)
        tasks = get_tasks(client, only_running=True)

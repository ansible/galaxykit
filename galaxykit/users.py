"""
Functions for creating, updating, and deleting users.
"""

import requests
import json


def get_or_create_user(
        galaxy_root, headers, username, password, group, fname="", lname="", email="", superuser=False
):
    """
    A simple utility to create a new user. All the arguments aside from
    `group` should be strings. `group` needs to be a dict of the following
    form:

    group = {
        "id": group_id,
        "name": group_name,
        "pulp_href": f"/pulp/api/v3/groups/{group_id}",
    }
    """
    # check if the user already exists
    user_url = f"{galaxy_root}_ui/v1/users?username={username}"
    user_resp = requests.get(user_url, headers=headers).json()
    if user_resp["meta"]["count"] == 0:
        create_user(
                galaxy_root, headers, username, password, group, fname, lname, email
        )
        user_resp = requests.get(user_url, headers=headers).json()

    return user_resp["data"][0]


def create_user(
    galaxy_root, headers, username, password, group, fname="", lname="", email="", superuser=False
):
    """
    Create a new user. All the arguments aside from
    `group` should be strings. `group` needs to be a dict of the following
    form:

    group = {
        "id": group_id,
        "name": group_name,
        "pulp_href": f"/pulp/api/v3/groups/{group_id}",
    }
    """
    if group is None:
        group = []
    else:
        group = [group]

    create_body = {
        "username": username,
        "first_name": fname,
        "last_name": lname,
        "email": email,
        "password": password,
        "groups": group,
        "is_superuser": superuser,
    }
    create_body = json.dumps(create_body).encode("utf8")
    headers = {
        **headers,
        "Content-Type": "application/json;charset=utf-8",
        "Content-length": str(len(create_body)),
    }
    # return the response so the caller has access to the id and other
    # metadata from the response.
    requests.post(
        f"{galaxy_root}_ui/v1/users/",
        create_body,
        headers=headers,
    )


def delete_user(galaxy_root, headers, user):
    user_id = get_user_id(galaxy_root, headers, user)
    delete_url = f"{galaxy_root}_ui/v1/users/{user_id}/"
    headers = {
        **headers,
        "Content-Type": "application/json;charset=utf-8",
        "Content-length": "0",
    }
    return requests.delete(delete_url, headers=headers)


def get_user_id(galaxy_root, headers, username):
    """
    Returns the id for a given username
    """
    user_url = f"{galaxy_root}_ui/v1/users/?username={username}"
    user_resp = requests.get(user_url, headers=headers)
    return user_resp.json()["data"][0]["id"]

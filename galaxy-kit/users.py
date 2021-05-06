"""
Functions for creating, updating, and deleting users.
"""

import requests
import json


def get_or_create_user(
    galaxy_root, username, password, group, fname="", lname="", email="", headers={}
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
    user_url = f"{galaxy_root}_ui/v1/users/?username={username}"
    user_resp = requests.get(user_url, headers=headers)
    if user_resp["meta"]["count"] == 0:
        return create_user(
            galaxy_root, username, password, group, fname, lname, email, headers
        )

    return user_resp.json()["data"][0]


def create_user(
    galaxy_root, username, password, group, fname="", lname="", email="", headers={}
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
    create_body = {
        "username": username,
        "first_name": fname,
        "last_name": lname,
        "email": email,
        "password": password,
        "groups": [group],
    }
    create_body = json.dumps(create_body).encode("utf8")
    headers = {
        **headers,
        "Content-Type": "application/json;charset=utf-8",
        "Content-length": str(len(create_body)),
    }
    # return the response so the caller has access to the id and other
    # metadata from the response.
    return requests.post(
        f"{galaxy_root}_ui/v1/users/",
        create_body,
        headers=headers,
    )


def delete_user(user, galaxy_root, headers):
    user_id = get_user_id(user, galaxy_root, headers)
    delete_url = f"{galaxy_root}_ui/v1/users/{user_id}/"
    headers = {
        **headers,
        "Content-Type": "application/json;charset=utf-8",
        "Content-length": "0",
    }
    requests.delete(delete_url, headers=headers)


def get_user_id(username, galaxy_root, headers):
    """
    Returns the id for a given username
    """
    user_url = f"{galaxy_root}_ui/v1/users/?username={username}"
    user_resp = requests.get(user_url, headers=headers)
    return user_resp.json()["data"][0]["id"]

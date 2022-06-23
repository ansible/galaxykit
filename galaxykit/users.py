"""
Functions for creating, updating, and deleting users.
"""

import json


def get_or_create_user(
    client, username, password, group, fname="", lname="", email="", superuser=False
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
    user_url = f"_ui/v1/users?username={username}"
    user_resp = client.get(user_url)
    if user_resp["meta"]["count"] == 0:
        return True, create_user(
            client, username, password, group, fname, lname, email, superuser
        )

    return False, user_resp["data"][0]


def create_user(
    client, username, password, group, fname="", lname="", email="", superuser=False
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
        assert isinstance(group, dict)
        assert "id" in group
        assert "name" in group
        assert "pulp_href" in group
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
    # return the response so the caller has access to the id and other
    # metadata from the response.
    resp = client.post(f"_ui/v1/users/", create_body)
    return resp


def update_user(client, user):
    return client.put(f"_ui/v1/users/{user['id']}/", user)


def delete_user(client, user):
    user_id = get_user_id(client, user)
    delete_url = f"_ui/v1/users/{user_id}/"
    client.delete(delete_url, parse_json=False)


def get_user_id(client, username):
    """
    Returns the id for a given username
    """
    user_url = f"_ui/v1/users/?username={username}"
    resp = client.get(user_url)
    if resp["data"]:
        return resp["data"][0]["id"]
    else:
        raise ValueError(f"No user '{username}' found.")


def get_user(client, username):
    """
    Returns the id for a given username
    """
    user_url = f"_ui/v1/users/?username={username}"
    user_resp = client.get(user_url)
    return user_resp["data"][0]


def get_user_list(client):
    """
    Returns list of usernames of users in the system
    """
    return client.get("_ui/v1/users/")

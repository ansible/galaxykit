from . import roles


def get_group(client, group_name):
    """
    Returns the data of the group with group_name
    """
    groups_url = f"_ui/v1/groups/?name={group_name}"
    return client.get(groups_url)["data"][0]


def get_group_id(client, group_name):
    """
    Returns the id for a given group
    """
    groups_url = f"_ui/v1/groups/?name={group_name}"
    resp = client.get(groups_url)
    if resp["data"]:
        return resp["data"][0]["id"]
    else:
        raise ValueError(f"No group '{group_name}' found.")


def create_group(client, group_name):
    """
    Creates a group
    """
    return client.post("_ui/v1/groups/", {"name": group_name})


def delete_group(client, group_name):
    # need to get the group id,
    # then make the url and requests.delete it
    group_id = get_group_id(client, group_name)
    delete_url = f"_ui/v1/groups/{group_id}"
    return client.delete(delete_url, parse_json=False)


def get_roles(client, group_name):
    group_id = get_group_id(client, group_name)
    roles_url = f"pulp/api/v3/groups/{group_id}/roles/?content_object=null"
    return client.get(roles_url)


def add_role(client, group_name, role_name):
    """
    Assigns the given role to the group.
    The roles should match the "galaxy.role-name" format.
    """
    group_id = get_group_id(client, group_name)
    roles_url = f"pulp/api/v3/groups/{group_id}/roles/"
    payload = {
        "content_object": None,
        "role": role_name,
    }
    return client.post(roles_url, payload)


def get_group_role_id(client, group_name, role_name):
    """
    Returns the id for a given role in a group
    """
    group_id = get_group_id(client, group_name)
    roles_url = (
        f"pulp/api/v3/groups/{group_id}/roles/?content_object=null&role={role_name}"
    )
    resp = client.get(roles_url)
    if resp["results"]:
        return roles.pulp_href_to_id(resp["results"][0]["pulp_href"])
    else:
        raise ValueError(f"No role '{role_name}' found in group '{group_name}'.")


def remove_role(client, group_name, role_name):
    """
    Removes a role from a group.
    """
    group_id = get_group_id(client, group_name)
    role_id = get_group_role_id(client, group_name, role_name)
    roles_url = f"pulp/api/v3/groups/{group_id}/roles/{role_id}/"
    return client.delete(roles_url, parse_json=False)


def get_group_list(client):
    """
    Returns list of group names of groups in the system
    """
    return client.get("_ui/v1/groups/")


def add_user_to_group(client, username, group_id):
    """
    Adds a user to a group
    """
    user_to_group_url = f"_ui/v1/groups/{group_id}/users/"
    user_to_group_body = {"username": username}
    return client.post(user_to_group_url, user_to_group_body)


def add_role_to_group(client, role_name, group_id):
    """
    Adds a role to a group
    """
    role_to_group_url = f"pulp/api/v3/groups/{group_id}/roles/"
    body = {"role": role_name, "content_object": None}
    return client.post(role_to_group_url, body)

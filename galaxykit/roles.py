import re


def pulp_href_to_id(href):
    uuid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

    for section in href.split("/"):
        if re.match(uuid_regex, section):
            return section

    return None


def get_role_list(client):
    """
    Returns list of galaxy rbac roles in the system
    """
    return client.get(f"pulp/api/v3/roles/?name__startswith=galaxy.")


def get_role(client, role_name):
    """
    Returns the data of the role with role_name
    """
    roles_url = f"pulp/api/v3/roles/?name={role_name}"
    return client.get(roles_url)["results"][0]


def get_role_id(client, role_name):
    """
    Returns the id for a given role
    """
    roles_url = f"pulp/api/v3/roles/?name={role_name}"
    resp = client.get(roles_url)
    if resp["results"]:
        return pulp_href_to_id(resp["results"][0]["pulp_href"])
    else:
        raise ValueError(f"No role '{role_name}' found.")


def create_role(client, role_name, description, permissions):
    """
    Creates an rbac role
    """
    payload = {
        "description": description,
        "name": role_name,
        "permissions": permissions or [],
    }
    resp = client.post("pulp/api/v3/roles/", payload, parse_json=False)
    if resp.status_code == 400:
        raise ValueError(resp.json())
    return resp


def patch_update_role(client, role_name, updated_body):
    """
    Updates a role. It can be partially updated.
    """
    role = get_role(client, role_name)
    pulp_href = role["pulp_href"]
    return client.patch(pulp_href, updated_body)


def put_update_role(client, role_name, updated_body):
    """
    Updates a role. Entire data has to be provided.
    """
    role = get_role(client, role_name)
    pulp_href = role["pulp_href"]
    return client.put(pulp_href, updated_body)


def delete_role(client, role_name):
    """
    Deletes an rbac role
    """
    role_id = get_role_id(client, role_name)
    delete_url = f"pulp/api/v3/roles/{role_id}/"
    return client.delete(delete_url, parse_json=False)


# `permissions` must be a list of strings, each one recognized as a permission by the backend.
#
# See them listed at the link below:
# https://github.com/ansible/galaxy_ng/blob/ca503375077a225a5fb215e6fb2c6ae47e09cfd7/galaxy_ng/app/api/ui/serializers/user.py#L122
#
# Container permissions are in another file:
# https://github.com/ansible/galaxy_ng/blob/009385fb3a1a34d1df9ff369e2e15c3fa27869b3/galaxy_ng/app/access_control/statements/pulp_container.py#L139
#
# The permissions are the ones that match the "namespace.permission-name" format.


def get_permissions(client, role_name):
    return get_role(client, role_name)["permissions"]


def set_permissions(client, role_name, add_permissions=[], remove_permissions=[]):
    """
    Assigns the given permissions to the role.
    """
    role = get_role(client, role_name)
    role_id = pulp_href_to_id(role["pulp_href"])
    role_url = f"pulp/api/v3/roles/{role_id}/"

    permissions = set(role["permissions"])
    permissions = permissions | set(add_permissions)
    permissions = permissions - set(remove_permissions)

    payload = {"permissions": list(permissions)}
    resp = client.patch(role_url, payload, parse_json=False)
    if resp.status_code == 400:
        raise ValueError(resp.json())
    return resp

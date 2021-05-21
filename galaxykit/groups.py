import requests
import json


def find_group(client, group_name):
    """
    Returns the data of the group with group_name
    """
    groups_url = f"_ui/v1/groups/?name={group_name}"
    return client.get(groups_url)

def get_group_id(client, group_name):
    """
    Returns the id for a given group
    """
    groups_url = f"_ui/v1/groups/?name={group_name}"
    resp = client.get(groups_url)
    return resp["data"][0]["id"]


def create_group(client, group_name):
    """
    Creates a group
    """
    return client.post("_ui/v1/groups/", {"name": group_name})


def delete_group(client, group_name):
    # need to get the group id,
    # then make the url and requests.delete it
    group_id = find_group(client, group_name)[0]["id"]
    delete_url = f"_ui/v1/groups/{group_id}"
    return client.delete(delete_url)


def set_permissions(client, group_name, permissions):
    """
    Assigns the given permissions to the group.
    `permissions` must be a list of strings, each one recognized as a permission by the backend. See
    them listed at the link below:
    https://github.com/ansible/galaxy_ng/blob/ca503375077a225a5fb215e6fb2c6ae47e09cfd7/galaxy_ng/app/api/ui/serializers/user.py#L122

    Container permissions are in another file:
    https://github.com/ansible/galaxy_ng/blob/009385fb3a1a34d1df9ff369e2e15c3fa27869b3/galaxy_ng/app/access_control/statements/pulp_container.py#L139

    The permissions are the ones that match the "namespace.permission-name" format.

    """
    group_id = find_group(client, group_name)[0]["id"]
    permissions_url = f"_ui/v1/groups/{group_id}/model-permissions/"
    for perm in permissions:
        payload = {"permission": perm}
        client.post(permissions_url, payload)
        # TODO: Check the results of each and aggregate for a return value

def get_group_list(client):
    """
    Returns list of group names of groups in the system
    """
    return client.get("_ui/v1/groups/")

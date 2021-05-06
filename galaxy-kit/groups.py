import requests
import json


def find_group(galaxy_root, headers, group_name):
    """
    Returns the data of the group with group_name
    """
    all_groups = requests.get(f"{galaxy_root}_ui/v1/groups/", headers=headers).json()
    match_group = [x for x in all_groups["data"] if x["name"] == group_name]
    return match_group


def create_group(galaxy_root, headers, group_name):
    """
    Creates a group
    """
    group_url = f"{galaxy_root}_ui/v1/groups/"
    payload = json.dumps({"name": group_name}).encode("utf8")
    headers = {
        **headers,
        "Content-Type": "application/json;charset=utf-8",
        "Content-length": str(len(payload)),
    }
    return requests.post(group_url, headers=headers, data=payload)


def delete_group(galaxy_root, headers, group_name):
    # need to get the group id,
    # then make the url and requests.delete it
    group_id = find_group(galaxy_root, headers, group_name)[0]["id"]
    delete_url = f"{galaxy_root}_ui/v1/groups/{group_id}"
    return requests.delete(delete_url, headers=headers)


def set_permissions(galaxy_root, headers, group_name, permissions):
    """
    Assigns the given permissions to the group.
    `permissions` must be a list of strings, each one recognized as a permission by the backend. See
    them listed at the link below:
    https://github.com/ansible/galaxy_ng/blob/ca503375077a225a5fb215e6fb2c6ae47e09cfd7/galaxy_ng/app/api/ui/serializers/user.py#L122

    Container permissions are in another file:
    https://github.com/ansible/galaxy_ng/blob/009385fb3a1a34d1df9ff369e2e15c3fa27869b3/galaxy_ng/app/access_control/statements/pulp_container.py#L139

    The permissions are the ones that match the "namespace.permission-name" format.

    """
    group_id = find_group(galaxy_root, headers, group_name)[0]["id"]
    permissions_url = f"{galaxy_root}_ui/v1/groups/{group_id}/model-permissions/"
    for perm in permissions:
        payload = json.dumps({"permission": perm}).encode("utf8")
        headers = {
            **headers,
            "Content-Type": "application/json;charset=utf-8",
            "Content-length": str(len(payload)),
        }
        requests.post(
            permissions_url,
            data=payload,
            headers=headers,
        )

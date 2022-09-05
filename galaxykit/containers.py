from pprint import pprint
from . import registries


def get_readme(client, container):
    """
    Returns a json response containing the readme
    """
    url = f"_ui/v1/execution-environments/repositories/{container}/_content/readme/"
    return client.get(url)


def set_readme(client, container, readme):
    """
    Accepts a string and sets the container readme to that string.
    """
    url = f"_ui/v1/execution-environments/repositories/{container}/_content/readme/"
    resp = get_readme(client, container)
    resp["text"] = readme
    return client.put(url, resp)


def delete_container(client, name):
    """
    Delete container
    """
    delete_url = f"_ui/v1/execution-environments/repositories/{name}/"
    return client.delete(delete_url, parse_json=False)


def create_container(client, name, upstream_name, registry):
    """
    Create container
    """
    create_url = f"_ui/v1/execution-environments/remotes/"
    registry_id = registries.get_registry_pk(client, registry)
    data = {
        "name": name,
        "upstream_name": upstream_name,
        "registry": registry_id,
        "exclude_tags": [],
        "include_tags": ["latest"],
    }
    return client.post(create_url, data)


def add_owner_to_ee(client, ee_name, group_name, object_roles):
    """
    Add owner to Execution Environment
    """
    url = f"_ui/v1/execution-environments/namespaces/{ee_name}/"
    existing_groups = client.get(url)["groups"]
    existing_groups.append({"name": group_name, "object_roles": object_roles})
    data = {"groups": existing_groups}
    return client.put(url, data)


def inspect_container_namespace(client, ee_name):
    """
    Inspect a container namepsace
    """
    url = f"_ui/v1/execution-environments/namespaces/{ee_name}/"
    return client.get(url)

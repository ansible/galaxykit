from . import groups
from .utils import logger


def create_namespace(client, name, group):
    try:
        get_namespace(client, name)
    except KeyError:
        ns_groups = []
        if group:
            group_id = groups.get_group_id(client, group)
            ns_groups.append(
                {
                    "id": group_id,
                    "name": group,
                    "object_permissions": ["change_namespace", "upload_to_namespace"],
                    "object_roles": [],
                }
            )
        create_body = {"name": name, "groups": ns_groups}
        logger.debug(f"Creating namespace {name}. Request body {create_body}")
        return client.post("v3/namespaces/", create_body)
    else:
        if group:
            add_group(client, name, group)


def get_namespace(client, name):
    try:
        namespace = client.get(f"v3/namespaces/{name}/")
        return namespace
    except Exception as e:
        if e.args[0]["status"] == "404":
            raise KeyError(f"No namespace {name} found.")
        else:
            raise


def get_namespace_collections(client, name):
    try:
        collection_list = client.get(f"_ui/v1/repo/published/?namespace={name}")
        return collection_list
    except Exception as e:
        if e.args[0]["status"] == "404":
            raise KeyError(f"No namespace {name} found.")
        else:
            raise


def update_namespace(client, namespace):
    name = namespace["name"]
    return client.put(f"v3/namespaces/{name}/", namespace)


def add_group(client, ns_name, group_name):
    namespace = get_namespace(client, ns_name)
    group = groups.get_group(client, group_name)
    namespace["groups"].append(
        {
            "id": group["id"],
            "name": group["name"],
            "object_permissions": ["change_namespace", "upload_to_namespace"],
        }
    )
    return update_namespace(client, namespace)


def remove_group(client, ns_name, group_name):
    namespace = get_namespace(client, ns_name)
    namespace["groups"] = [
        group for group in namespace["groups"] if group["name"] != group_name
    ]
    return update_namespace(client, namespace)


def get_namespace_id(client, name):
    """
    Returns the id for a given namespace
    """
    url = f"v3/namespaces/?name={name}"
    resp = client.get(url)
    if resp["data"]:
        return resp["data"][0]["id"]
    else:
        raise ValueError(f"No namespace '{name}' found.")


def delete_namespace(client, name):
    """
    Delete namespace
    """
    delete_url = f"_ui/v1/namespaces/{name}"
    return client.delete(delete_url, parse_json=False)


def get_namespace_list(client):
    """
    Returns list of namespaces
    """
    return client.get("_ui/v1/namespaces")

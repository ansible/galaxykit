from . import groups
from .utils import logger
from .collections import delete_collection


def create_namespace(client, name, group, object_roles=None):
    try:
        get_namespace(client, name)
    except KeyError:
        ns_groups = []
        object_roles = [] if object_roles is None else object_roles
        if group:
            group_id = groups.get_group_id(client, group)
            _group = {
                "id": group_id,
                "name": group,
                "object_permissions": ["change_namespace", "upload_to_namespace"],
            }
            if client.rbac_enabled:
                _group["object_roles"] = object_roles
            ns_groups.append(_group)
        create_body = {"name": name, "groups": ns_groups}
        logger.debug(f"Creating namespace {name}. Request body {create_body}")
        return client.post("v3/namespaces/", create_body)
    else:
        if group:
            add_group(client, name, group, object_roles)


def get_namespace(client, name):
    try:
        namespace = client.get(f"v3/namespaces/{name}/")
        return namespace
    except Exception as e:
        logger.exception(e)
        if e.args[0]["status"] == "404":
            raise KeyError(f"No namespace {name} found.")
        else:
            raise


def get_namespace_collections(client, name):
    try:
        collection_list = client.get(f"_ui/v1/repo/published/?namespace={name}")
        return collection_list
    except Exception as e:
        logger.exception(e)
        if e.args[0]["status"] == "404":
            raise KeyError(f"No namespace {name} found.")
        else:
            raise


def update_namespace(client, namespace):
    name = namespace["name"]
    return client.put(f"v3/namespaces/{name}/", namespace)


def add_group(client, ns_name, group_name, object_roles=None):
    namespace = get_namespace(client, ns_name)
    group = groups.get_group(client, group_name)
    object_roles = [] if object_roles is None else object_roles
    _group = {
        "id": group["id"],
        "name": group["name"],
        "object_permissions": ["change_namespace", "upload_to_namespace"],
    }
    if client.rbac_enabled:
        _group["object_roles"] = object_roles
    namespace["groups"].append(_group)
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


def delete_v1_namespace(client, name):
    """
    Delete namespace
    """
    ns_url = f"v1/namespaces/?name={name}"
    results = client.get(ns_url)
    if results["count"] > 0:
        delete_url = f"v1/namespaces/{results['results'][0]['id']}/"
    else:
        raise ValueError(f"No namespace '{name}' found.")
    return client.delete(delete_url, parse_json=False)


def delete_namespace(client, name, cascade=False):
    """
    Delete namespace
    """

    if cascade:
        # find all collections first ...
        collections = set()
        next_url = f"v3/plugin/ansible/search/collection-versions/?namespace={name}&is_highest=true"
        while next_url:
            resp = client.get(next_url)
            for collection in resp["data"]:
                collections.add((
                    collection["repository"]["name"],
                    collection["collection_version"]["namespace"],
                    collection["collection_version"]["name"],
                ))
            if resp["links"]["next"] is None:
                break
            next_url = resp["links"]["next"]

        for collection in collections:
            delete_collection(client, collection[1], collection[2], repository=collection[0])

    delete_url = f"_ui/v1/namespaces/{name}"
    return client.delete(delete_url, parse_json=False)


def get_namespace_list(client):
    """
    Returns list of namespaces
    """
    return client.get("_ui/v1/namespaces")

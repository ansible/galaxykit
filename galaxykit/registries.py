from pprint import pprint


def get_registry_pk(client, name):
    """
    Returns the primary key for a given registry name
    """
    user_url = f"_ui/v1/execution-environments/registries/?name={name}"
    resp = client.get(user_url)
    if resp["data"]:
        return resp["data"][0]["pk"]
    else:
        raise ValueError(f"No registry '{name}' found.")


def delete_registry(client, name):
    """
    Delete registry
    """
    pk = get_registry_pk(client, name)
    delete_url = f"_ui/v1/execution-environments/registries/{pk}/"
    return client.delete(delete_url, parse_json=False)


def create_registry(client, name, url):
    """
    Create registry
    """
    post_url = f"_ui/v1/execution-environments/registries/"
    registry = {
        "name": name,
        "url": url,
    }
    return client.post(post_url, registry)

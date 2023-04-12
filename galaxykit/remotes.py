from . import utils


def community_remote_config(
    client, url, username, password, tls_validation=False, signed_only=True
):
    """
    Configures community remote repository
    """
    remote_url = "content/community/v3/sync/config/"
    body = {
        "url": url,
        "username": username,
        "password": password,
        "tls_validation": tls_validation,
        "signed_only": signed_only,
    }
    return client.put(remote_url, body)


def get_community_remote(client):
    """
    Gets community remote repository details
    """
    url = "content/community/v3/sync/config"
    return client.get(url)


def get_remote_pk(client, name):
    """
    Returns the primary key for a given remote name
    """
    href = get_remote_href(client, name)
    return utils.pulp_href_to_id(href)


def get_remote_href(client, name):
    """
    Returns the href for a given remote name
    """
    user_url = f"pulp/api/v3/remotes/ansible/collection/?name={name}"
    resp = client.get(user_url)
    if resp["results"] and resp["results"][0]:
        return resp["results"][0]["pulp_href"]
    else:
        raise ValueError(f"No remote '{name}' found.")


def delete_remote(client, name):
    """
    Delete remote
    """
    pk = get_remote_pk(client, name)
    delete_url = f"pulp/api/v3/remotes/ansible/collection/{pk}/"
    return client.delete(delete_url, parse_json=False)


def create_remote(client, name, url):
    """
    Create remote
    """
    post_url = f"pulp/api/v3/remotes/ansible/collection/"
    registry = {
        "name": name,
        "url": url,
    }
    return client.post(post_url, registry)

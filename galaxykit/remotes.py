from galaxykit.utils import wait_for_task, pulp_href_to_id

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
    r = client.delete(delete_url)
    return wait_for_task(client, r)


def create_remote(client, name, url, signed_only=False, tls_validation=False, params=None):
    """
    Create remote
    """
    params = params or {}
    remote_url = "pulp/api/v3/remotes/ansible/collection/"
    body = {
        "name": name,
        "url": url,
        "tls_validation": tls_validation,
        "download_concurrency": 10,
        "signed_only": signed_only,
        **params
    }
    return client.post(remote_url, body)


def view_remotes(client, name=None):
    remote_url = f"pulp/api/v3/remotes/ansible/collection/?name={name}"
    return client.get(remote_url)


def update_remote(client, name, url, params=None):
    params = params or {}
    pulp_href = view_remotes(client, name)
    pulp_id = pulp_href_to_id(pulp_href["results"][0]["pulp_href"])
    remote_url = f"pulp/api/v3/remotes/ansible/collection/{pulp_id}/"
    body = {
        "name": name,
        "url": url,
        **params
    }
    return client.put(remote_url, body)


def add_permissions_to_remote(client, name, role, groups):
    r = view_remotes(client, name)
    pulp_href = r["results"][0]["pulp_href"]
    body = {"role": role, "groups": groups}
    return client.post(pulp_href+"add_role/", body)

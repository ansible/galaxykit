from galaxykit.utils import wait_for_task


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


def create_remote(client, name, url, signed_only=False, tls_validation=False, params=None):
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
    pulp_id = pulp_href["results"][0]["pulp_href"].split("/")[-2]
    remote_url = f"pulp/api/v3/remotes/ansible/collection/{pulp_id}/"
    body = {
        "name": name,
        "url": url,
        **params
    }
    return client.put(remote_url, body)


def delete_remote(client, name):
    pulp_href = view_remotes(client, name)
    pulp_id = pulp_href["results"][0]["pulp_href"].split("/")[-2]
    remote_url = f"pulp/api/v3/remotes/ansible/collection/{pulp_id}/"
    r = client.delete(remote_url)
    wait_for_task(client, r)

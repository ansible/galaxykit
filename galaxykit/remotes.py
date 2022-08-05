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

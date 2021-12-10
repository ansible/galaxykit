def create_registry(client, registry_name, registry_url):
    """
    to create a registry:

        POST http://localhost:8002/api/automation-hub/_ui/v1/execution-environments/registries/
        {
        "name":"docker",
                "tls_validation":true
                ,"write_only_fields":[
                        {"name":"username",
                            "is_set":false},
                        {"name":"password",
                            "is_set":false},
                        {"name":"proxy_username",
                            "is_set":false},
                        {"name":"proxy_password",
                            "is_set":false},
                        {"name":"client_key","is_set":false}],
                "url":"docker.io"}
    """

    body = {
        "name": name,
        "tls_validation": true,
        "write_only_fields": [
            {"name": "username", "is_set": false},
            {"name": "password", "is_set": false},
            {"name": "proxy_username", "is_set": false},
            {"name": "proxy_password", "is_set": false},
            {"name": "client_key", "is_set": false},
        ],
        "url": registry_url,
    }
    client.post("_ui/v1/execution-environments/registries/", body)


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

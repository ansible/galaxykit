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

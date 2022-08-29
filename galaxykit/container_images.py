from pprint import pprint


def delete_container(client, container, image):
    """
    Delete container image
    """
    delete_url = f"v3/plugin/execution-environments/repositories/{container}/_content/images/{image}/"
    return client.delete(delete_url, parse_json=False)

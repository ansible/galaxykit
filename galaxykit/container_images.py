from pprint import pprint


def delete_container(client, container, image):
    """
    Delete container image
    """
    delete_url = f"{client.ui_ee_endpoint_prefix}execution-environments/repositories/{container}/_content/images/{image}/"

    return client.delete(delete_url, parse_json=False)


def get_container_images(client, container):
    """
    Gets container images
    """
    get_url = f"{client.ui_ee_endpoint_prefix}execution-environments/repositories/{container}/_content/images/"
    return client.get(get_url)


def get_container_history(client, container):
    """
    Gets container history
    """
    get_url = f"{client.ui_ee_endpoint_prefix}execution-environments/repositories/{container}/_content/history/"
    return client.get(get_url)


def get_containers(client):
    """
    Gets containers
    """
    url = f"{client.ui_ee_endpoint_prefix}execution-environments/repositories/"
    return client.get(url)


def get_container(client, name):
    """
    Gets a container
    """
    url = f"{client.ui_ee_endpoint_prefix}execution-environments/repositories/{name}/"
    return client.get(url)


def get_container_readme(client, name):
    """
    Gets container's readme
    """
    url = f"{client.ui_ee_endpoint_prefix}execution-environments/repositories/{name}/_content/readme/"
    return client.get(url)


def put_container_readme(client, name, data):
    """
    Updates container's readme
    """
    url = f"{client.ui_ee_endpoint_prefix}execution-environments/repositories/{name}/_content/readme/"
    return client.put(url, body=data)

from . import repositories
from . import utils


def get_distribution_pk(client, name):
    """
    Returns the primary key for a given distribution name
    """
    return utils.pulp_href_to_id(get_distribution_href(client, name))


def get_distribution_href(client, name):
    """
    Returns the href for a given distribution name
    """
    user_url = f"pulp/api/v3/distributions/ansible/ansible/?name={name}"
    resp = client.get(user_url)
    if resp["results"] and resp["results"][0]:
        href = resp["results"][0]["pulp_href"]
        return href
    else:
        raise ValueError(f"No remote '{name}' found.")


def delete_distribution(client, name):
    """
    Delete distribution
    """
    pk = get_distribution_pk(client, name)
    delete_url = f"pulp/api/v3/distributions/ansible/ansible/{pk}/"
    return client.delete(delete_url, parse_json=False)


def create_distribution(client, name):
    """
    Create distribution from repository
    """

    repository = repositories.get_repository_href(client, name)

    post_url = f"pulp/api/v3/distributions/ansible/ansible/"
    data = {
        "name": name,
        "base_path": name,
        "repository": repository,
    }

    res = client.post(post_url, data)
    return res


def get_all_distributions(client):
    """
    Lists all distributions
    """
    url = "pulp/api/v3/distributions/ansible/ansible/"
    return client.get(url)["results"]


def get_v1_distributions(client):
    url = "_ui/v1/distributions/"
    return client.get(url)

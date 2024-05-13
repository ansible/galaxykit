from . import remotes
from . import utils
from galaxykit.utils import wait_for_task
from urllib.parse import urljoin


def get_repository_pk(client, name):
    """
    Returns the primary key for a given repository name
    """
    return utils.pulp_href_to_id(get_repository_href(client, name))


def get_repository_href(client, name):
    """
    Returns the href for a given repository name
    """
    user_url = f"pulp/api/v3/repositories/ansible/ansible/?name={name}"
    resp = client.get(user_url)
    if resp["results"] and resp["results"][0]:
        href = resp["results"][0]["pulp_href"]
        return href
    else:
        raise ValueError(f"No remote '{name}' found.")


def delete_repository(client, name):
    """
    Delete repository
    """
    pk = get_repository_pk(client, name)
    delete_url = f"pulp/api/v3/repositories/ansible/ansible/{pk}/"
    task_resp = client.delete(delete_url)
    return wait_for_task(client, task_resp)


def create_repository(
    client,
    name,
    pipeline=None,
    remote=None,
    description=None,
    private=False,
    hide_from_search=False,
):
    """
    Create repository
    """
    post_url = f"pulp/api/v3/repositories/ansible/ansible/"

    registry = {"name": name, "private": private}
    registry.update({"description": description}) if description is not None else False
    registry.update(
        {"pulp_labels": {"hide_from_search": ""}}
    ) if hide_from_search is not False else False

    if pipeline:
        registry["pulp_labels"] = {"pipeline": pipeline}

    if remote:
        pk = remotes.get_remote_href(client, remote)
        registry["remote"] = pk

    return client.post(post_url, registry)


def patch_update_repository(client, repository_id, update_body):
    update_repo_url = f"pulp/api/v3/repositories/ansible/ansible/{repository_id}/"
    return client.patch(update_repo_url, update_body)


def put_update_repository(client, repository_id, update_body):
    update_repo_url = f"pulp/api/v3/repositories/ansible/ansible/{repository_id}/"
    return client.put(update_repo_url, update_body)


def search_collection(client, **search_param):
    search_url = "v3/plugin/ansible/search/collection-versions/?"
    for key, value in search_param.items():
        if isinstance(value, list):
            param = "&".join([f"{key}={v}" for v in value])
        else:
            param = f"{key}={value}"
        search_url += f"{param}&"
    search_url = search_url[:-1]
    return client.get(search_url)


def get_all_repositories(client):
    """
    Lists all repositories
    """
    url = "pulp/api/v3/repositories/"
    return client.get(url)["results"]


def get_distribution_id(client, name):
    ansible_distribution_path = (
        f"pulp/api/v3/distributions/ansible/ansible/?name={name}"
    )
    resp = client.get(ansible_distribution_path)
    return resp["results"][0]["pulp_href"].split("/")[-2]


def copy_content_between_repos(
    client, cv_hrefs, source_repo_href, destination_repo_hrefs
):
    url = urljoin(source_repo_href, "copy_collection_version/")
    body = {
        "collection_versions": cv_hrefs,
        "destination_repositories": destination_repo_hrefs,
    }
    r = client.post(url, body)
    return wait_for_task(client, r)


def move_content_between_repos(
    client, cv_hrefs, source_repo_href, destination_repo_hrefs
):
    url = urljoin(source_repo_href, "move_collection_version/")
    body = {
        "collection_versions": cv_hrefs,
        "destination_repositories": destination_repo_hrefs,
    }
    r = client.post(url, body)
    return wait_for_task(client, r)


def view_repositories(client, name=None):
    repo_url = f"pulp/api/v3/repositories/ansible/ansible/?name={name}"
    return client.get(repo_url)


def view_distributions(client, name=None):
    dist_url = f"pulp/api/v3/distributions/ansible/ansible/?name={name}"
    return client.get(dist_url)


def add_permissions_to_repository(client, name, role, groups):
    r = view_repositories(client, name)
    pulp_href = r["results"][0]["pulp_href"]
    body = {"role": role, "groups": groups}
    return client.post(pulp_href + "add_role/", body)


def create_distribution(client, dist_name, repo_href):
    ansible_distribution_path = "pulp/api/v3/distributions/ansible/ansible/"
    dist_data = {"base_path": dist_name, "name": dist_name, "repository": repo_href}
    task_resp = client.post(ansible_distribution_path, dist_data)
    wait_for_task(client, task_resp)
    return repo_href


def delete_distribution(client, dist_name):
    r = view_distributions(client, dist_name)
    pulp_href = r["results"][0]["pulp_href"]
    task_resp = client.delete(pulp_href)
    return wait_for_task(client, task_resp)

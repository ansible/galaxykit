from . import remotes
from . import utils
from . import tasks

def get_repository_pk(client, name):
    """
    Returns the primary key for a given repository name
    """
    return utils.parse_pulp_id(get_repository_href(client, name))
   
def get_repository_href(client, name):
    """
    Returns the href for a given repository name
    """
    user_url = f"pulp/api/v3/repositories/ansible/ansible/?name={name}"
    resp = client.get(user_url)
    if resp["results"] and resp["results"][0]:
        href = resp["results"][0]["pulp_href"];
        return href
    else:
        raise ValueError(f"No remote '{name}' found.")

def delete_repository(client, name):
    """
    Delete repository
    """
    pk = get_repository_pk(client, name)
    delete_url = f"pulp/api/v3/repositories/ansible/ansible/{pk}/"
    return client.delete(delete_url, parse_json=False)

def create_repository(client, name, pipeline, remote):
    """
    Create repository
    """
    post_url = f"pulp/api/v3/repositories/ansible/ansible/"
    registry = {
        "name" : name,
    }

    if pipeline:
        registry["pulp_labels"] = { "pipeline" : pipeline }

    if remote:
        pk = remotes.get_remote_href(client, remote)
        registry["remote"] = pk

    return client.post(post_url, registry)  

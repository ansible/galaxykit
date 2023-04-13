from . import remotes
from . import utils
from . import tasks
import uuid
from urllib.parse import urlparse

from ansible.module_utils.common.text.converters import to_text

from galaxykit.utils import GalaxyClientError, wait_for_task
import time
import os
import subprocess
import tarfile
import tempfile
import json
from typing import List, Union

try:
    import importlib.resources as pkg_resources
except ModuleNotFoundError:
    import importlib_resources as pkg_resources


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
    return client.delete(delete_url, parse_json=False)


def create_repository(client, name, pipeline, remote, description=None, private=False, hide_from_search=False):
    """
    Create repository
    """
    post_url = f"pulp/api/v3/repositories/ansible/ansible/"
    registry = {
        "name": name, "private": private
    }
    registry.update({"description": description}) if description is not None else False
    registry.update({"pulp_labels": {"hide_from_search": ""}}) if hide_from_search is not False else False

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
    # get rid of the api_prefix
    galaxy_root_bck = client.galaxy_root
    client.galaxy_root = client.galaxy_root.split('api/automation-hub/')[0]
    search_url = f'pulp_ansible/galaxy/default/api/v3/' \
                 f'plugin/ansible/search/collection-versions/?'
    for key, value in search_param.items():
        if isinstance(value, list):
            param = '&'.join([f"{key}={v}" for v in value])
        else:
            param = f"{key}={value}"
        search_url += f"{param}&"
    search_url = search_url[:-1]
    response = client.get(search_url)
    client.galaxy_root = galaxy_root_bck
    return response


# move out from here

class TaskWaitingTimeout(Exception):
    pass


def wait_for_url(api_client, url, timeout_sec=30):
    """Wait until url stops returning a 404."""
    ready = False
    res = None
    wait_until = time.time() + timeout_sec
    while not ready:
        if wait_until < time.time():
            raise TaskWaitingTimeout()
        try:
            res = api_client.get(url)
        except GalaxyClientError as e:
            if "404" not in str(e):
                raise
            time.sleep(0.5)
        else:
            ready = True
    return res


def _urljoin(*args):
    return '/'.join(to_text(a, errors='surrogate_or_strict').strip('/') for a in args + ('',) if a)


def set_certification(client, collection, level="published", upload_signatures=True):
    """Moves a collection from the `staging` to the `published` repository.

    For use in instances that use repository-based certification and that
    do not have auto-certification enabled.
    """
    # check if artifact is in staging repo, if not wait
    staging_artifact_url = (
        f"v3/plugin/ansible/content/staging/collections/index/"
        f"{collection.namespace}/{collection.name}/versions/{collection.version}/"
    )
    wait_for_url(client, staging_artifact_url)

    if upload_signatures:
        # Write manifest to temp file
        tf = tarfile.open(collection.filename, mode="r:gz")
        tdir = tempfile.TemporaryDirectory()
        keyring = tempfile.NamedTemporaryFile("w")
        tf.extract("MANIFEST.json", tdir.name)

        # Setup local keystore
        # gpg --no-default-keyring --keyring trustedkeys.gpg
        # gpg --import clowder-data.key
        with pkg_resources.path("dev.data", "ansible-sign.gpg") as keyfilename:
            subprocess.run(
                [
                    "gpg",
                    "--quiet",
                    "--batch",
                    "--pinentry-mode",
                    "loopback",
                    "--yes",
                    "--no-default-keyring",
                    "--keyring",
                    keyring.name,
                    "--import",
                    keyfilename,
                ]
            )

        # Run gpg to generate signature
        with pkg_resources.path("dev.data", "collection_sign.sh") as collection_sign:
            result = subprocess.check_output(
                [collection_sign, os.path.join(tdir.name, "MANIFEST.json")],
                env={
                    "KEYRING": keyring.name,
                },
            )
            signature_filename = json.loads(result)["signature"]

        rep_obj_url = "pulp/api/v3/repositories/ansible/ansible/?name=staging"
        repository_pulp_href = client.get(rep_obj_url)["results"][0]["pulp_href"]

        artifact_obj_url = f"_ui/v1/repo/staging/{collection.namespace}/" f"{collection.name}/"
        all_versions = client.get(artifact_obj_url)["all_versions"]
        one_version = [v for v in all_versions if v["version"] == collection.version][0]
        artifact_pulp_id = one_version["id"]
        # FIXME: used unified url join utility below
        artifact_pulp_href = (
                "/"
                + _urljoin(
            urlparse(client.galaxy_root).path,
            "pulp/api/v3/content/ansible/collection_versions/",
            artifact_pulp_id,
        )
                + "/"
        )

        data = {
            "repository": repository_pulp_href,
            "signed_collection": artifact_pulp_href,
        }
        kwargs = setup_multipart(signature_filename, data)
        sig_url = "pulp/api/v3/content/ansible/collection_signatures/"
        resp = client.post(sig_url, kwargs.pop('args'), **kwargs)
        wait_for_task(client, resp)

    # move the artifact from staging to destination repo
    url = (
        f"v3/collections/{collection.namespace}/{collection.name}/versions/"
        f"{collection.version}/move/staging/{level}/"
    )
    job_tasks = client.post(url, b"{}")
    assert "copy_task_id" in job_tasks
    assert "remove_task_id" in job_tasks

    # wait for each unique task to finish ...
    for key in ["copy_task_id", "remove_task_id"]:
        task_id = job_tasks.get(key)

        # The task_id is not a url, so it has to be assembled from known data ...
        # http://.../api/automation-hub/pulp/api/v3/tasks/8be0b9b6-71d6-4214-8427-2ecf81818ed4/
        ds = {"task": f"{client.galaxy_root}pulp/api/v3/tasks/{task_id}"}
        task_result = wait_for_task(client, ds)
        assert task_result["state"] == "completed", task_result

    # callers expect response as part of this method, ensure artifact is there
    dest_url = (
        f"v3/plugin/ansible/content/{level}/collections/index/"
        f"{collection.namespace}/{collection.name}/versions/{collection.version}/"
    )
    return wait_for_url(client, dest_url)


def setup_multipart(path: str, data: dict) -> dict:
    buffer = []
    boundary = b"--" + uuid.uuid4().hex.encode("ascii")
    filename = os.path.basename(path)

    buffer += [
        boundary,
        b'Content-Disposition: file; name="file"; filename="%s"' % filename.encode("ascii"),
        b"Content-Type: application/octet-stream",
    ]
    buffer += [
        b"",
        open(path, "rb").read(),
    ]

    for name, value in data.items():
        add_multipart_field(boundary, buffer, name, value)

    buffer += [
        boundary + b"--",
    ]

    data = b"\r\n".join(buffer)
    headers = {
        "Content-Type": "multipart/form-data; boundary=%s"
                        % boundary[2:].decode("ascii"),  # strip --
        "Content-Length": str(len(data)),
    }

    return {
        "args": data,
        "headers": headers,
    }


def add_multipart_field(
        boundary: bytes, buffer: List[bytes], name: Union[str, bytes], value: Union[str, bytes]
):
    if isinstance(name, str):
        name = name.encode("utf8")
    if isinstance(value, str):
        value = value.encode("utf8")
    buffer += [
        boundary,
        b'Content-Disposition: form-data; name="%s"' % name,
        b"Content-Type: text/plain",
        b"",
        value,
    ]


def get_distribution_id(client, name):
    ansible_distribution_path = f"/api/automation-hub/pulp/api/v3/distributions/ansible/ansible/?name={name}"
    resp = client.get(ansible_distribution_path)
    return resp["results"][0]["pulp_href"].split("/")[-2]


def copy_content_between_repos(client, cv_hrefs, source_repo_href, destination_repo_hrefs):
    url = f"{source_repo_href}copy_collection_version/"
    body = {
        "collection_versions": cv_hrefs,
        "destination_repositories": destination_repo_hrefs,
        # "signing_service": ""
    }
    return client.post(url, body)


def move_content_between_repos(client, cv_hrefs, source_repo_href, destination_repo_hrefs):
    url = f"{source_repo_href}move_collection_version/"
    body = {
        "collection_versions": cv_hrefs,
        "destination_repositories": destination_repo_hrefs,
        # "signing_service": ""
    }
    return client.post(url, body)


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
    return client.post(pulp_href+"add_role/", body)


def create_distribution(client, dist_name, repo_href):
    ansible_distribution_path = "/api/automation-hub/pulp/api/v3/distributions/ansible/ansible/"
    dist_data = {"base_path": dist_name, "name": dist_name, "repository": repo_href}
    task_resp = client.post(ansible_distribution_path, dist_data)
    wait_for_task(client, task_resp)
    return repo_href


def delete_distribution(client, dist_name):
    r = view_distributions(client, dist_name)
    pulp_href = r["results"][0]["pulp_href"]
    task_resp = client.delete(pulp_href)
    return wait_for_task(client, task_resp)

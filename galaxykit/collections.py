"""
Functions for managing collections. Currently only handles uploading test collections.
"""

import uuid
import os
import json
from time import sleep
from urllib.parse import urljoin
from pkg_resources import parse_version

from orionutils.generator import build_collection
from .utils import wait_for_task, logger, GalaxyClientError, wait_for_url
from .constants import EE_ENDPOINTS_CHANGE_VERSION


def collection_info(client, repository, namespace, collection_name, version):
    url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection_name}/versions/{version}/"
    return client.get(url)


def get_collection(client, namespace, collection_name, version):
    # collection_url = f"v3/collections/{namespace}/{collection_name}/versions/{version}/"
    collection_url = (
        f"v3/plugin/ansible/content/published/collections/index/"
        f"{namespace}/{collection_name}/versions/{version}/"
    )
    return client.get(collection_url)


def get_collection_from_repo(client, repository, namespace, collection_name, version):
    collection_url = (
        f"content/{repository}/v3/plugin/ansible/content/{repository}"
        f"/collections/index/{namespace}/{collection_name}/versions/{version}/"
    )
    return client.get(collection_url)


def get_ui_collection(client, repository, namespace, collection_name, version):
    ui_collection_url = (
        f"_ui/v1/repo/{repository}/{namespace}/"
        f"{collection_name}/?versions={version}"
    )
    return client.get(ui_collection_url)


def get_collection_list(client):
    url = "_ui/v1/collection-versions/?limit=999999"
    return client.get(url)


def get_all_collections(client):
    url = "v3/collections/"
    return client.get(url)


def create_test_collection(
    namespace=None,
    name=None,
    version="1.0.0",
    tags=None,
    template="skeleton",
):
    config = {
        "namespace": namespace,
        "version": version,
    }

    if name is not None:
        config["name"] = name

    # cloud importer config requires at least one tag
    if tags is not None:
        config["tags"] = tags

    return build_collection(template, config=config)


def save_test_collection(
    namespace=None,
    collection_name=None,
    version="1.0.0",
    tags=["tools"],
    template="skeleton",
):
    """
    Saves (locally) a test collection generated with orionutils
    """
    artifact = create_test_collection(
        namespace, collection_name, version, tags, template
    )

    return {
        "namespace": artifact.namespace,
        "name": artifact.name,
        "version": artifact.version,
        "published": artifact.published,
        "filename": artifact.filename,
    }


def upload_test_collection(
    client,
    namespace=None,
    collection_name=None,
    version="1.0.0",
    path="staging",
    tags=["tools"],
    template="skeleton",
):
    """
    Uploads a test collection generated with orionutils
    """
    artifact = create_test_collection(
        namespace or client.username, collection_name, version, tags, template
    )

    resp = upload_artifact(None, client, artifact, path=path)
    wait_for_task(client, resp)

    return {
        "namespace": artifact.namespace,
        "name": artifact.name,
        "version": artifact.version,
        "published": artifact.published,
    }


def upload_artifact(
    config,
    client,
    artifact,
    hash=True,
    no_filename=False,
    no_file=False,
    path=None,
    use_distribution=False,
):
    """
    Publishes a collection to a Galaxy server and returns the import task URI.

    :param config: unused, left for compatibility
    :param client: a GalaxyClient object. Must be authenticated.
    :param artifact: the collection artifact to be uploaded. Expects structure to be that
        of collections produced using the orionutils build_collection function.
    :param hash: If false, no hash is produced. If true, hash is generated on the fly.
        Alternatively, could pass a hash in directly as this argument.
    :param no_filename: If True, no filename is attached to the request.
    :param no_file: If True, no file is attached to the request.
    :param path: the repository the artifact will be directly uploaded to
    :return: The import task URI that contains the import results.
    """

    def to_bytes(s, errors=None):
        return s.encode("utf8")

    collection_path = artifact.filename
    with open(collection_path, "rb") as collection_tar:
        data = collection_tar.read()

    boundary = "--------------------------%s" % uuid.uuid4().hex
    file_name = os.path.basename(collection_path)
    part_boundary = b"--" + to_bytes(boundary, errors="surrogate_or_strict")

    form = []

    if hash:
        if isinstance(hash, bytes):
            # if a pre-computed hash is passed in, just use that.
            b_hash = hash
        else:
            # otherwise hash the collection contents.
            from hashlib import sha256

            b_hash = to_bytes(sha256(data).hexdigest(), errors="surrogate_or_strict")

        # add the hash to the request.
        form.extend(
            [part_boundary, b'Content-Disposition: form-data; name="sha256"', b_hash]
        )

    # only add the file to the request if no_file == False
    if not no_file:
        # skip the filename if no_filename
        if no_filename:
            form.extend(
                [
                    part_boundary,
                    b'Content-Disposition: file; name="file"',
                    b"Content-Type: application/octet-stream",
                ]
            )
        else:
            form.extend(
                [
                    part_boundary,
                    b'Content-Disposition: file; name="file"; filename="%s"'
                    % to_bytes(file_name),
                    b"Content-Type: application/octet-stream",
                ]
            )
    else:
        form.append(part_boundary)

    form.extend([b"", data, b"%s--" % part_boundary])

    data = b"\r\n".join(form)

    headers = {
        "Content-Type": "multipart/form-data; boundary=%s" % boundary,
        "Content-Length": f"{len(data)}",
    }

    if client.token:
        auth = {"Authorization": f"{client.token_type} {client.token}"}
        headers.update(auth)

    if parse_version(client.server_version) >= parse_version(
        EE_ENDPOINTS_CHANGE_VERSION
    ):
        col_upload_path = f"v3/artifacts/collections/"
        if path:
            col_upload_path = f"content/{path}/v3/artifacts/collections/"
    else:
        col_upload_path = (
            f"content/inbound-{artifact.namespace}/v3/artifacts/collections/"
        )

    if use_distribution:
        n_url = urljoin(
            client.galaxy_root,
            f"content/inbound-{artifact.namespace}/v3/artifacts/collections/",
        )
    else:
        n_url = urljoin(client.galaxy_root, col_upload_path)
    resp = client.post(n_url, body=data, headers=headers)
    return resp


def approve_collection(client, namespace, collection_name, version):
    return move_or_copy_collection(
        client,
        namespace,
        collection_name,
        version,
        source="staging",
        destination="published",
        operation="move",
    )


def move_or_copy_collection(
    client,
    namespace,
    collection_name,
    version="1.0.0",
    source="staging",
    destination="published",
    operation="move",
):
    """
    Moves a collection between repositories. The default arguments are for the most common usecase, which
    is moving a collection from the staging to published repositories.

    POST v3/collections/{namespace}/{collection_name}/versions/{version}/move/{source}/{destination}/
    """
    move_url = f"v3/collections/{namespace}/{collection_name}/versions/{version}/{operation}/{source}/{destination}/"
    payload = ""
    client.post(move_url, payload)

    dest_url = f"_ui/v1/repo/{destination}/{namespace}/{collection_name}/"
    ready = False
    timeout = 5
    while not ready:
        try:
            client.get(dest_url)
            ready = True
        except GalaxyClientError:
            sleep(1)
            timeout = timeout - 1
            if timeout < 0:
                raise

    dest_url = (
        f"v3/plugin/ansible/content/{destination}/collections/index/"
        f"{namespace}/{collection_name}/versions/{version}/"
    )
    return wait_for_url(client, dest_url)


def delete_collection(
    client, namespace, collection, version=None, repository="published"
):
    """
    Delete collection version
    """
    logger.debug(f"Deleting {collection} from {namespace} on {client.galaxy_root}")
    if version is None:
        delete_url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection}/"
    else:
        delete_url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection}/versions/{version}/"
    resp = client.delete(delete_url)
    wait_for_task(client, resp)
    return resp


def deprecate_collection(client, namespace, collection, repository):
    logger.debug(f"Deprecating {collection} in {namespace} on {client.galaxy_root}")
    url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection}/"
    body = {"deprecated": True}
    resp = client.patch(url, body)
    wait_for_task(client, resp)
    return resp


def undeprecate_collection(client, namespace, collection, repository):
    logger.debug(f"Undeprecating {collection} in {namespace} on {client.galaxy_root}")
    url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection}/"
    body = {"deprecated": False}
    resp = client.patch(url, body)
    wait_for_task(client, resp)
    return resp


def collection_sign(
    client,
    repository,
    namespace,
    collection,
    version,
    signing_service="ansible-default",
):
    url = f"content/{repository}/v3/sign/collections/"
    body = {
        "signing_service": signing_service,
        "repository": repository,
        "namespace": namespace,
        "collection": collection,
        "version": version,
    }
    return client.post(url, body)


def sign_collection(client, cv_href, repo_pulp_href):
    results = client.get("pulp/api/v3/signing-services/?name=ansible-default")
    signing_service = results["results"][0]
    body = {"content_units": [cv_href], "signing_service": signing_service["pulp_href"]}
    resp = client.post(f"{repo_pulp_href}sign/", body)

    resp = wait_for_task(client, resp)
    assert resp["state"] == "completed"

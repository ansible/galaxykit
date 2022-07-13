"""
Functions for managing collections. Currently only handles uploading test collections.
"""

import uuid
import os
import json
from time import sleep
from urllib.parse import urljoin

from orionutils.generator import build_collection
from .utils import wait_for_task, logger, GalaxyClientError


def collection_info(client, repository, namespace, collection_name, version):
    url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection_name}/versions/{version}/"
    return client.get(url)


def get_collection_list(client):
    url = "_ui/v1/collection-versions/?limit=999999"
    return client.get(url)


def upload_test_collection(
    client, namespace=None, collection_name=None, version="1.0.0"
):
    """
    Uploads a test collection generated with orionutils
    """
    config = {
        "namespace": namespace or client.username,
        "version": version,
    }
    if collection_name is not None:
        config["name"] = collection_name
    # cloud importer config requires at least one tag
    config["tags"] = ["tools"]
    artifact = build_collection("skeleton", config=config)
    upload_resp_url = upload_artifact(config, client, artifact)["task"]

    ready = False
    state = ""
    while not ready:
        sleep(1)
        task_resp = client.get(upload_resp_url)
        state = task_resp["state"]
        ready = state in ["completed", "failed"]
    if state == "failed":
        raise GalaxyClientError(json.dumps(task_resp))
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
):
    """
    Publishes a collection to a Galaxy server and returns the import task URI.

    :param config: a configuration object to describe the artifact to be uploaded.
        Example:
            {"namespace": "foo", "name": "bar"}
    :param client: a GalaxyClient object. Must be authenticated.
    :param artifact: the collection artifact to be uploaded. Expects structure to be that
        of collections produced using the orionutils build_collection function.
    :param hash: If false, no hash is produced. If true, hash is generated on the fly.
        Alternatively, could pass a hash in directly as this argument.
    :param no_filename: If True, no filename is attached to the request.
    :param no_file: If True, no file is attached to the request.
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
        "Content-type": "multipart/form-data; boundary=%s" % boundary,
        "Content-length": f"{len(data)}",
        "Authorization": f"{client.token_type} {client.token}",
    }

    n_url = urljoin(
        client.galaxy_root,
        f"content/inbound-{artifact.namespace}/v3/artifacts/collections/",
    )
    resp = client._http("post", n_url, data=data, headers=headers)
    return resp


def move_collection(
    client,
    namespace,
    collection_name,
    version="1.0.0",
    source="staging",
    destination="published",
):
    """
    Moves a collection between repositories. The default arguments are for the most common usecase, which
    is moving a collection from the staging to published repositories.

    POST v3/collections/{namespace}/{collection_name}/versions/{version}/move/{source}/{destination}/
    """
    move_url = f"v3/collections/{namespace}/{collection_name}/versions/{version}/move/{source}/{destination}/"
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
    return True


def delete_collection(
    client, namespace, collection, version=None, repository="published"
):
    """
    Delete collection version
    """
    logger.debug(f"Deleting {collection} from {namespace} on {client.galaxy_root}")
    if version == None:
        delete_url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection}/"
    else:
        delete_url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection}/versions/{version}/"
    resp = client.delete(delete_url, parse_json=False)
    wait_for_task(client, resp)
    return resp


def deprecate_collection(client, namespace, collection, repository):
    logger.debug(f"Deprecating {collection} in {namespace} on {client.galaxy_root}")
    url = f"v3/plugin/ansible/content/{repository}/collections/index/{namespace}/{collection}/"
    body = {"deprecated": True}
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

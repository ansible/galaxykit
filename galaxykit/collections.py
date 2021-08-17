"""
Functions for managing collections. Currently only handles uploading test collections.
"""

import uuid
import os
import json
from time import sleep
from urllib.parse import urljoin
from orionutils.generator import build_collection
from .client import GalaxyClientError


def upload_test_collection(client, namespace=None, collection_name=None):
    """
    Uploads a test collection generated with orionutils
    """
    config = {"namespace": namespace or client.username}
    if collection_name is not None:
        config["name"] = collection_name
    artifact = build_collection(
        "skeleton",
        config=config,
    )
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
    return task_resp


def upload_artifact(
    config,
    client,
    artifact,
    hash=True,
    no_filename=False,
    no_file=False,
    use_distribution=True,
):
    """
    Publishes a collection to a Galaxy server and returns the import task URI.

    :param collection_path: The path to the collection tarball to publish.
    :return: The import task URI that contains the import results.
    """
    collection_path = artifact.filename
    with open(collection_path, "rb") as collection_tar:
        data = collection_tar.read()

    def to_bytes(s, errors=None):
        return s.encode("utf8")

    boundary = "--------------------------%s" % uuid.uuid4().hex
    file_name = os.path.basename(collection_path)
    part_boundary = b"--" + to_bytes(boundary, errors="surrogate_or_strict")

    form = []

    if hash:
        if isinstance(hash, bytes):
            b_hash = hash
        else:
            from hashlib import sha256

            b_hash = to_bytes(sha256(data).hexdigest(), errors="surrogate_or_strict")

        form.extend(
            [part_boundary, b'Content-Disposition: form-data; name="sha256"', b_hash]
        )

    if not no_file:
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
        "Authorization": f"Token {client.token}",
    }

    n_url = f"{client.galaxy_root}/content/inbound-{artifact.namespace}/v3/artifacts/collections/"
    resp = client._http("post", n_url, data=data, headers=headers)
    return resp

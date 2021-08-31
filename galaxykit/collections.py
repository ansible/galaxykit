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
        "Authorization": f"Token {client.token}",
    }

    n_url = f"{client.galaxy_root}/content/inbound-{artifact.namespace}/v3/artifacts/collections/"
    resp = client._http("post", n_url, data=data, headers=headers)
    return resp

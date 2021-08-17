"""
Functions for managing collections. Currently only handles uploading test collections.
"""

from subprocess import run
from orionutils.generator import build_collection


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
        extra_files={"meta/runtime.yml": {"requires_ansible": "==2.10"}},
    )
    collection_path = artifact.filename
    run_args = [
        "ansible-galaxy",
        "collection",
        "publish",
        collection_path,
        "--server",
        client.galaxy_root,
        "--api-key",
        client.token,
    ]
    run(run_args)

"""
Functions for managing collections. Currently only handles uploading test collections.
"""

from subprocess import run
from orionutils.generator import build_collection


def upload_test_collection(client, namespace=None):
    """
    Uploads a test collection generated with orionutils
    """
    if namespace is None:
        namespace = client.username
    artifact = build_collection(
        "skeleton",
        config={"namespace": namespace},
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

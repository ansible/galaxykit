"""
client.py contains the wrapping interface for all the other modules (aside from cli.py)
"""
from urllib.parse import urlparse
import requests

import dockerutils
import users


class GalaxyClient:
    """
    The primary class for the client - this is the authenticated context from
    which all authentication flows.
    """

    headers = {}
    galaxy_root = ""
    token = ""
    docker_client = None

    def __init__(self, galaxy_root, user="", password="", container_engine=""):
        self.galaxy_root = galaxy_root
        if user != "" and password != "":
            self.token = (
                requests.post(galaxy_root + "v3/auth/token/", auth=(user, password))
                .json()
                .get("token")
            )
            self.headers = {
                "accept": "application/json",
                "Authorization": f"Token {self.token}",
            }

            if container_engine != "":
                container_registry = (
                    urlparse(self.galaxy_root).netloc.split(":") + ":5001"
                )

                self.docker_client = dockerutils.DockerClient(
                    user, password, container_engine, container_registry
                )

    def pull_image(self, image_name):
        """pulls an image with the given credentials"""
        self.docker_client.pull_image(image_name)

    def tag_image(self, image_name, newtag, version="latest"):
        """tags a pulled image with the given newtag and version"""
        self.docker_client.tag_image(image_name, newtag, version=version)

    def push_image(self, image_tag):
        """pushs a image"""
        self.docker_client.push_image(image_tag)

    def get_or_create_user(
        self, username, password, group, fname="", lname="", email=""
    ):
        users.get_or_create_user(
            self.galaxy_root,
            username,
            password,
            group,
            fname,
            lname,
            email,
            self.headers,
        )

    def delete_user(self, username):
        users.delete_user(username, self.galaxy_root, self.headers)

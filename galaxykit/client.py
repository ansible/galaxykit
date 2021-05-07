"""
client.py contains the wrapping interface for all the other modules (aside from cli.py)
"""
from simplejson.errors import JSONDecodeError
import sys
from urllib.parse import urlparse

import requests

from . import dockerutils
from . import users
from . import groups


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
            resp = requests.post(galaxy_root + "v3/auth/token/", auth=(user, password))
            try:
                self.token = resp.json().get("token")
            except JSONDecodeError as e:
                print(f"Failed to fetch token: {resp.text}", file=sys.stderr)
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
        return self.docker_client.pull_image(image_name)

    def tag_image(self, image_name, newtag, version="latest"):
        """tags a pulled image with the given newtag and version"""
        return self.docker_client.tag_image(image_name, newtag, version=version)

    def push_image(self, image_tag):
        """pushs a image"""
        return self.docker_client.push_image(image_tag)

    def get_or_create_user(
        self, username, password, group, fname="", lname="", email="", superuser=False
    ):
        """
        Returns user info if that already username exists,
        creates a user if not.
        """
        return users.get_or_create_user(
            self.galaxy_root,
            self.headers,
            username,
            password,
            group,
            fname,
            lname,
            email,
            superuser,
        )

    def delete_user(self, username):
        """deletes a user"""
        return users.delete_user(self.galaxy_root, self.headers, username)

    def create_group(self, group_name):
        """
        Creates a group
        """
        return groups.create_group(self.galaxy_root, self.headers, group_name)

    def find_group(self, group_name):
        """
        Returns the data of the group with group_name
        """
        return groups.find_group(self.galaxy_root, self.headers, group_name)

    def delete_group(self, group_name):
        """
        Deletes the given group
        """
        return groups.delete_group(self.galaxy_root, self.headers, group_name)

    def set_permissions(self, group_name, permissions):
        """
        Assigns the given permissions to the group
        """
        return groups.set_permissions(
            self.galaxy_root, self.headers, group_name, permissions
        )

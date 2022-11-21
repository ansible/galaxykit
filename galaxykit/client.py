"""
client.py contains the wrapping interface for all the other modules (aside from cli.py)
"""
import logging
import platform
import sys
from urllib.parse import urlparse, urljoin
from simplejson.errors import JSONDecodeError
from simplejson import dumps
from pkg_resources import parse_version

import requests

from .utils import GalaxyClientError
from . import containers
from . import containerutils
from . import groups
from . import users
from . import namespaces
from . import collections
from . import roles
from . import __version__ as VERSION
from .constants import RBAC_VERSION, EE_ENDPOINTS_CHANGE_VERSION

logger = logging.getLogger(__name__)


def user_agent():
    """Returns a user agent used by ansible-galaxy to include the Ansible version, platform and python version."""

    python_version = sys.version_info
    return "galaxy-kit/{version} ({platform}; python:{py_major}.{py_minor}.{py_micro})".format(
        version=VERSION,
        platform=platform.system(),
        py_major=python_version.major,
        py_minor=python_version.minor,
        py_micro=python_version.micro,
    )


class GalaxyClient:
    """
    The primary class for the client - this is the authenticated context from
    which all authentication flows.
    """

    headers = None
    galaxy_root = ""
    auth_url = None
    original_token = None
    token = ""
    token_type = None
    container_client = None
    username = ""
    password = ""
    _rbac_enabled = None
    _server_version = None
    _container_client = None
    _ui_ee_endpoint_prefix = None

    def __init__(
        self,
        galaxy_root,
        auth=None,
        container_engine=None,
        container_registry=None,
        container_tls_verify=True,
        https_verify=False,
    ):
        self.galaxy_root = galaxy_root
        self.headers = {}
        self.token = None
        self.https_verify = https_verify
        self._container_engine = container_engine
        self._container_registry = container_registry
        self._container_tls_verify = container_tls_verify

        if auth:
            if isinstance(auth, dict):
                self.username = auth.get("username")
                self.password = auth.get("password")
                self.token = auth.get("token")
                self.auth_url = auth.get("auth_url")
            elif isinstance(auth, tuple):
                self.username, self.password = auth

            self.token_type = "Token"
            if not self.token and self.auth_url:

                # https://developers.redhat.com/blog/2020/01/29/api-login-and-jwt-token-generation-using-keycloak
                # When testing ephemeral environments, we won't have the
                # access token up front, so we have to create one via user+pass.
                # Does this work on real SSO? I have no idea.

                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                ds = {
                    "client_id": "cloud-services",
                    "username": self.username,
                    "password": self.password,
                    "grant_type": "password",
                }
                jdata = self._http("post", self.auth_url, headers=headers, data=ds)
                self.token_type = "Bearer"
                if "access_token" not in jdata:
                    raise GalaxyClientError(
                        f"`access_token` not found in JWT response.",
                        json=jdata,
                    )
                self.token = jdata["access_token"]

            elif self.token and self.auth_url:
                self._refresh_jwt_token()

            elif self.token is None:
                auth_url = urljoin(self.galaxy_root, "v3/auth/token/")
                resp = self._http(
                    "post", auth_url, auth=(self.username, self.password), headers=None
                )
                try:
                    self.token = resp.get("token")
                except JSONDecodeError:
                    print(f"Failed to fetch token: {resp.text}", file=sys.stderr)

            self._update_auth_headers()

    @property
    def container_client(self):
        """Only create a container client if its actually needed."""

        if self._container_client is None:
            if not (self.username and self.password):
                raise ValueError(
                    "Cannot use container engine commands without username and password for authentication."
                )
            container_registry = (
                self._container_registry
                or urlparse(self.galaxy_root).netloc.split(":")[0] + ":5001"
            )

            self._container_client = containerutils.ContainerClient(
                (self.username, self.password),
                self._container_engine,
                container_registry,
                tls_verify=self._container_tls_verify,
            )
        return self._container_client

    def _refresh_jwt_token(self):
        if not self.original_token:
            self.original_token = self.token
        else:
            logger.warning("Refreshing JWT Token and retrying request")

        payload = "grant_type=refresh_token&client_id=%s&refresh_token=%s" % (
            "cloud-services",
            self.original_token,
        )
        headers = {
            "User-Agent": user_agent(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        json = self._http(
            "post",
            self.auth_url,
            data=payload,
            headers=headers,
        )
        self.token = json["access_token"]
        self.token_type = "Bearer"

    def _update_auth_headers(self):
        self.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"{self.token_type} {self.token}",
            }
        )

    def _get_server_version(self):
        return self._http("get", self.galaxy_root)["galaxy_ng_version"]

    def _is_rbac_available(self):
        galaxy_ng_version = self.server_version
        return parse_version(galaxy_ng_version) >= parse_version(RBAC_VERSION)

    def _http(self, method, path, *args, **kwargs):
        url = urljoin(self.galaxy_root, path)
        headers = kwargs.pop("headers", self.headers)
        parse_json = kwargs.pop("parse_json", True)

        resp = requests.request(
            method, url, headers=headers, verify=self.https_verify, *args, **kwargs
        )

        if "Invalid JWT token" in resp.text and "claim expired" in resp.text:
            self._refresh_jwt_token()
            self._update_auth_headers()
            resp = requests.request(
                method, url, headers=headers, verify=self.https_verify, *args, **kwargs
            )

        if parse_json:
            try:
                json = resp.json()
            except JSONDecodeError as exc:
                logging.error(
                    f"Cannot parse expected JSON response ({url}): {resp.text}"
                )
                raise ValueError("Failed to parse JSON response from API") from exc
            if "errors" in json:
                raise GalaxyClientError(resp, *json["errors"])
            return json
        else:
            if resp.status_code >= 400:
                raise GalaxyClientError(resp, resp.status_code)
            return resp

    def _payload(self, method, path, body, *args, **kwargs):
        if isinstance(body, dict):
            body = dumps(body)
        if isinstance(body, str):
            body = body.encode("utf8")
        headers = {
            **kwargs.pop("headers", self.headers),
            "Content-Type": "application/json;charset=utf-8",
            "Content-length": str(len(body)),
        }
        kwargs["headers"] = headers
        kwargs["data"] = body
        return self._http(method, path, *args, **kwargs)

    def get(self, path, *args, **kwargs):
        return self._http("get", path, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._payload("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._payload("put", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._payload("patch", *args, **kwargs)

    def delete(self, path, *args, **kwargs):
        return self._http("delete", path, *args, **kwargs)

    def pull_image(self, image_name):
        """pulls an image with the given credentials"""
        return self.container_client.pull_image(image_name)

    def tag_image(self, image_name, newtag):
        """tags a pulled image with the given newtag"""
        return self.container_client.tag_image(image_name, newtag)

    def push_image(self, image_tag):
        """pushs a image"""
        return self.container_client.push_image(image_tag)

    def get_or_create_user(
        self, username, password, group, fname="", lname="", email="", superuser=False
    ):
        """
        Returns a "created" flag and user info if that already username exists,
        creates a user if not.
        """
        return users.get_or_create_user(
            self,
            username,
            password,
            group,
            fname,
            lname,
            email,
            superuser,
        )

    def get_user_list(self):
        """returns a list of all the users"""
        return users.get_user_list(self)

    def delete_user(self, username):
        """deletes a user"""
        return users.delete_user(self, username)

    def create_group(self, group_name):
        """
        Creates a group
        """
        return groups.create_group(self, group_name)

    def get_group(self, group_name):
        """
        Returns the data of the group with group_name
        """
        return groups.get_group(self, group_name)

    def delete_group(self, group_name):
        """
        Deletes the given group
        """
        return groups.delete_group(self, group_name)

    def set_permissions(self, group_name, permissions):
        """
        Assigns the given permissions to the group
        """
        return groups.set_permissions(self, group_name, permissions)

    def get_container_readme(self, container):
        return containers.get_readme(self, container)

    def set_container_readme(self, container, readme):
        return containers.set_readme(self, container, readme)

    def create_namespace(self, name, group, object_roles=None):
        """
        Creates a namespace
        """
        return namespaces.create_namespace(self, name, group, object_roles)

    def delete_collection(self, namespace, collection, version, repository):
        """deletes a collection"""
        return collections.delete_collection(
            self, namespace, collection, version, repository
        )

    def deprecate_collection(self, namespace, collection, repository):
        """deprecates a collection"""
        return collections.deprecate_collection(self, namespace, collection, repository)

    def create_role(self, role_name, description, permissions):
        """
        Creates a role
        """
        return roles.create_role(self, role_name, description, permissions)

    def delete_role(self, role_name):
        """
        Deletes a role
        """
        return roles.delete_role(self, role_name)

    def get_role(self, role_name):
        """
        Gets a role
        """
        return roles.get_role(self, role_name)

    def patch_update_role(self, role_name, updated_body):
        """
        Updates a role
        """
        return roles.patch_update_role(self, role_name, updated_body)

    def put_update_role(self, role_name, updated_body):
        """
        Updates a role
        """
        return roles.put_update_role(self, role_name, updated_body)

    def add_user_to_group(self, username, group_id):
        """
        Adds a user to a group
        """
        return groups.add_user_to_group(self, username, group_id)

    def add_role_to_group(self, role_name, group_id):
        """
        Adds a role to a group
        """
        return groups.add_role_to_group(self, role_name, group_id)

    @property
    def rbac_enabled(self):
        if self._rbac_enabled is None:
            self._rbac_enabled = self._is_rbac_available()
        return self._rbac_enabled

    @property
    def server_version(self):
        if self._server_version is None:
            self._server_version = self._get_server_version()
        return self._server_version

    @property
    def ui_ee_endpoint_prefix(self):
        if self._ui_ee_endpoint_prefix is None:
            if parse_version(self.server_version) >= parse_version(
                EE_ENDPOINTS_CHANGE_VERSION
            ):
                # the EE endpoints that used to be under _ui/v1/ moved to v3/plugin/ starting with 4.7.0dev
                self._ui_ee_endpoint_prefix = "v3/plugin/"
            else:
                self._ui_ee_endpoint_prefix = "_ui/v1/"
        return self._ui_ee_endpoint_prefix

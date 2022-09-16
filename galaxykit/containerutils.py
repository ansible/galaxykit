"""
Holds all of the functions used by GalaxyClient to handle container operations.

i.e. cli commands with podman, e.g. podman pull, podman image tag, etc.
"""

from logging import getLogger
from subprocess import run
from subprocess import PIPE

from .utils import GalaxyClientError

logger = getLogger(__name__)


class ContainerClient:
    """
    ContainerClient authenticates with the passed registry, as well as
    provides utility functions for pushing, tagging, and pulling images.
    """

    engine = ""
    registry = ""
    tls_verify = True

    last_login_username = None

    def __init__(
        self,
        auth=None,
        engine="podman",
        registry="docker.io/library/",
        tls_verify=True,
    ):
        """
        auth should be `(username, password)` for logging into the container registry.

        If not provided, then no login attempt is made.
        """
        self.engine = engine
        self.registry = registry
        self.tls_verify = tls_verify
        self.auth = auth

        if auth:  # we only need to auth if creds are supplied
            self.login(*auth, fail_ok=True)

    def _check_login(self):
        """Ensure any associated crednetials are the last or current login."""
        if self.auth:
            username, _ = self.auth
            if username != self.last_login_username:
                self.login(self.username, self.password)

    def login(self, username, password, fail_ok=False):
        if username == self.last_login_username:
            return

        run_args = [
            self.engine,
            "login",
            self.registry,
            "--username",
            username,
            "--password",
            password,
        ]
        if self.engine == "podman":
            run_args.append(f"--tls-verify={self.tls_verify}")
        try:
            run_command(run_args)
            logger.debug(f"Logged in with user {username}")
            self.username = username
            self.password = password
            # Remember the last successful logged in user across all ContainerClient
            # instances. This is because podman or docker can only allow a single user
            # logged in at a time. If operations are done with the same user, we can
            # use the existing logged in status. If the last login was by a different
            # user, we'll need to perform a new login to change the active user session.
            ContainerClient.last_login_username = username
        except FileNotFoundError:
            if fail_ok:
                logger.warn(f"Container engine '{self.engine}' not found.")
            else:
                raise

    def pull_image(self, image_name):
        """
        pull an image from the configured default registry
        """
        self._check_login()
        if self.engine == "podman" and not self.tls_verify:
            run_command(
                [self.engine, "pull", self.registry + image_name, "--tls-verify=False"]
            )
        else:
            run_command([self.engine, "pull", self.registry + image_name])

    def tag_image(self, image_name, image_tag):
        """
        Tags an image with the given tag (prepends the registry to the tag.)
        """
        self._check_login()
        sep = "" if self.registry.endswith("/") else "/"
        full_tag = f"{self.registry}{sep}{image_tag}"
        run_args = [
            self.engine,
            "image",
            "tag",
            image_name,
            full_tag,
        ]
        run_command(run_args)

    def push_image(self, image_tag):
        """
        Pushes an image to the registry
        """
        self._check_login()
        sep = "" if self.registry.endswith("/") else "/"
        full_tag = f"{self.registry}{sep}{image_tag}"
        run_args = [self.engine, "push", full_tag]

        if self.engine == "podman":
            run_args.append(f"--tls-verify={self.tls_verify}")

        return run_command(run_args)


def run_command(run_args, retcode=0):
    cmd_string = " ".join(run_args)
    logger.debug(f"Run command run_args: {cmd_string}")
    result = run(run_args, stderr=PIPE, stdout=PIPE)
    logger.debug(f"Run command stderr: {result.stderr.decode('utf-8')}")
    logger.debug(f"Run command stdout: {result.stdout.decode('utf-8')}")
    logger.debug(f"Run command return code: {result.returncode}")
    if retcode is not None:
        if result.returncode != retcode:
            raise GalaxyClientError(
                f"Container engine command failed (retcode {result.returncode}): {cmd_string}"
            )
    return result.returncode

"""
Holds all of the functions used by GalaxyClient to handle container operations.

i.e. cli commands with podman, e.g. podman pull, podman image tag, etc.
"""

from subprocess import run


class ContainerClient:
    """
    ContainerClient authenticates with the passed registry, as well as
    provides utility functions for pushing, tagging, and pulling images.
    """

    engine = ""
    registry = ""
    tls_verify = True

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

        if auth:  # we only need to auth if creds are supplied
            run_args = [
                engine,
                "login",
                registry,
                "--username",
                auth[0],
                "--password",
                auth[1],
            ]
            if engine == "podman":
                run_args.append(f"--tls-verify={tls_verify}")
            run(run_args)

    def pull_image(self, image_name):
        """
        pull an image from the configured default registry
        """
        if self.engine == "podman" and not self.tls_verify:
            run([self.engine, "pull", self.registry + image_name, "--tls-verify=False"])
        else:
            run([self.engine, "pull", self.registry + image_name])

    def tag_image(self, image_name, newtag):
        """
        Tags an image with the given tag (prepends the registry to the tag.)
        """
        run(
            [
                self.engine,
                "image",
                "tag",
                image_name,
                f"{self.registry}/{newtag}",
            ]
        )

    def push_image(self, image_tag):
        """
        Pushes an image to the registry
        """
        sep = "" if self.registry.endswith("/") else "/"
        full_tag = f"{self.registry}{sep}{image_tag}"
        run_args = [self.engine, "push", full_tag]

        if self.engine == "podman":
            run_args.append(f"--tls-verify={self.tls_verify}")

        run(run_args)

# Architecture

Galaxykit has a fairly simple structure:

```
(galaxykit) henderson@mars => tree .
.
├── CHANGES.md
├── CONTRIBUTE.md
├── galaxykit
│   ├── client.py
│   ├── collections.py
│   ├── command.py
│   ├── container_images.py
│   ├── containers.py
│   ├── containerutils.py
│   ├── groups.py
│   ├── namespaces.py
│   ├── registries.py
│   └── users.py
├── LICENSE.md
├── README.md
├── setup.cfg
└── setup.py
```

Let's work through these files individually:

### CHANGES.md
A changelog, tracking all the updates to the code.

### CONTRIBUTE.md

This file, with advice on how to effectively contribute to galaxykit.

### LICENSE.md

This is the GPLv2, which is the same licence galaxy_ng is distributed under.

### README.md

Landing page.

### setup.cfg

Currently just contains a few linter settings.

### setup.py

All the metadata and things used when releasing this utility on PyPi.

### galaxykit/:

The source directory, containing all the code that goes into galaxykit.

#### client.py

This file contains the GalaxyClient object, which is essentially a single authenticated context for making requests against an existing galaxy_ng instance. This file and `command.py` contain the primary two interfaces to interacting with galaxykit.

#### collections.py

Functions for managing collections.

#### command.py

The command-line interface logic - this is what gets run when you invoke galaxykit directly on the command-line. Currently in a bit of a hacky state, as it's grown faster than we can refactor it. An extensive refactor is in progress - check out [this PR](https://github.com/ansible/galaxykit/pull/30) if you want to review the changes.

#### container_images.py

For interacting with individual container images (currently only contains 1 function for deleting a particular image (as opposed to deleting a _container_ which includes all the associated images.))

#### containers.py

Functions for dealing with containers as as discrete units (deleting, setting metadata.)

#### containerutils.py

This code abstracts over common `podman` or `docker` commands for uploading or downloading container images from a galaxy_ng instance.

#### groups.py

Adding/deleting/modifying the permissions of groups.

#### namespaces.py

Creating and deleting namespaces.

#### registries.py

Adding new remote container registries.

#### users.py

Adding/deleting users.


# Development Practices

Please run the [`black`](https://pypi.org/project/black/) code formatter on your code before opening a PR. An easy way to ensure this is done is to install the pre-commit hooks bundled with this repository for any PRs. This is as simple as:

```
pip install pre_commit
pre-commit install
pre-commit install-hooks
```

If you don't, CI will make suggestions based on black, and we'll need to get those suggestions into your branch before we merge the PR.

# Release Process

## dependencies:

So far we've been using `twine` to upload releases to PyPi.

## Creating the release PR:

1. Create a new branch and check it out, something like `release-v0.7.1`
2. Update the version number in setup.py.
3. Add the version that's going to be released the top of CHANGES.md, above all the changes that are going to be released.
4. Push those changes, and make the PR in GitHub.

## steps after the release PR:

1. tag the release and push to git.

2. verify you are on the correct branch (you should be on main, just after having merged the new release PR and pushed the new tag.)

3. build the dist folder:

    The below snippet builds both a binary wheel and a source distribution.

    ```shell
    python setup.py sdist bdist_wheel
    ```

4. use twine to upload a release to test pypi:

    ```shell
    twine upload --repository testpypi dist/*
    ```

    Note that twine relies on a `~/.pypirc` file that defines the various servers, usernames, and other config it needs.

5. install from testpypi to make sure things work as expected:

    ```shell
    pip install -i https://test.pypi.org/pypi galaxykit
    ```

    Once you have it installed, you can run tests with it, etc, to verify that it's working as expected.

6. release to real pypi

    ```shell
    twine upload --repository pypi dist/*
    ```

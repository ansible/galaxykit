## Galaxykit

Galaxykit is a client library for [galaxy\_ng](https://github.com/ansible/galaxy_ng), designed for use in internal testing.

It's intended to be a low-dependency and low-abstraction client for performing actions on a remote Automation Hub or galaxy\_ng instance.

### Prerequisites

[Ansible](https://github.com/ansible/ansible).

```pip3 install ansible```

### Installing:

To install the latest development version, run `pip3 install -e .` in the root of your checked-out copy of this repository.

To set up the pre-commit hooks we are using (currently just autoformatting with `black`), run the following snippet:

```bash
pre-commit install
pre-commit install-hooks
```

After running those commands, make sure to run the following command to the latest unreleased version:

```pip3 install ansible git+https://github.com/ansible/galaxykit.git@master```

After that's been done, the first commit you make will have to install any of those dependencies, and may take a few minutes.

### Distributing

To build a distribution package you need to install `build` tool, a build-backend agnostic and standartized tool 
for building dictrubiton packages.

```shell
pip install build
```

After installation, execute it as following:

```shell
python -m build
```


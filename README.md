## Galaxykit

Galaxykit is a client library for [galaxy\_ng](https://github.com/ansible/galaxy_ng), designed for use in internal testing.

It's intended to be a low-dependency and low-abstraction client for performing actions on a remote Automation Hub or galaxy\_ng instance.

### Installing:

To install the latest development version, run `pip install -e .` in the root of your checked-out copy of this repository.

To set up the pre-commit hooks we are using (currently just autoformatting with `black`), run the following snippet:

```bash
pre-commit install
pre-commit install-hooks
```

After that's been done, the first commit you make will have to install any of those dependencies, and may take a few minutes.

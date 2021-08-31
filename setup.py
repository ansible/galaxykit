#!/usr/bin/env python3
"""
setuptools script for installing galaxykit
"""

import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    author="Red Hat PEAQE Team",
    description="A small client library for testing galaxy_ng.",
    license="GPLv2",
    long_description=README,
    long_description_content_type="text/markdown",
    name="galaxykit",
    packages={"galaxykit"},
    url="https://github.com/hendersonreed/galaxykit/",
    version="0.5.1",
    install_requires=["requests", "simplejson", "orionutils", "pyyaml"],
    extra_requires={"dev": ["pre-commit"]},
    entry_points={
        "console_scripts": [
            "galaxykit = galaxykit.command:main",
        ],
    },
)

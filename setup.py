#!/usr/bin/env python3
"""
setuptools script for installing galaxykit
"""

import pathlib
from setuptools import setup
from distutils.util import convert_path

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

main_ns = {}
ver_path = convert_path("galaxykit/_version.py")
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)
VERSION = main_ns["__version__"]

setup(
    author="Red Hat PEAQE Team",
    description="A small client library for testing galaxy_ng.",
    license="GPLv2",
    long_description=README,
    long_description_content_type="text/markdown",
    name="galaxykit",
    packages={"galaxykit"},
    url="https://github.com/hendersonreed/galaxykit/",
    version=VERSION,
    install_requires=["requests", "simplejson", "orionutils", "pyyaml"],
    extra_requires={"dev": ["pre-commit"]},
    entry_points={
        "console_scripts": [
            "galaxykit = galaxykit.command:main",
        ],
    },
)

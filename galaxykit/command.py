import argparse
import sys
import json

from .client import GalaxyClient, GalaxyClientError
from . import containers
from . import collections
from . import groups
from . import namespaces
from . import users

EXIT_OK = 0
EXIT_UNKNOWN_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_DUPLICATE = 4


def print_unknown_error(args):
    print(f"Unknown {args.object} operation '{args.operation}'")
    sys.exit(EXIT_UNKNOWN_ERROR)


def format_list(data, identifier):
    buffer = []
    for datum in data:
        line = [datum[identifier]]
        for key, value in datum.items():
            if key != identifier and value:
                s = f"{key}={value}"
                line.append(s)
        buffer.append(" ".join(line))
    return "\n".join(buffer)


def report_error(resp):
    if "errors" in resp:
        for error in resp["errors"]:
            print(
                f"API Failure: HTTP {error['status']} {error['code']}; {error['title']} ({error['detail']})"
            )

def user():
    
    return None

def namespace():
    return None

def collection():
    return None

def group():
    return None

def remote_registry():
    return None

def execution_environment():
    return None


def user(parent_parser, client):
    parser = argparse.ArgumentParser(parent=parent_parser)
    args = parser.parse_args(parent_parser.rest)
    return None


def namespace(parent_parser, client):
    return None


def collection(parent_parser, client):
    return None


def group(parent_parser, client):
    return None


def registry(parent_parser, client):
    return None


def container(parent_parser, client):
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "object",
        type=str,
        action="store",
        help="Type of API content to operate against (user, group, namespace)",
    )
    parser.add_argument("operation", type=str, action="store")
    parser.add_argument("remaining", type=str, action="store", nargs="*")
    parser.add_argument("-i", "--ignore", default=False, action="store_true")
    parser.add_argument("-u", "--username", type=str, action="store")
    parser.add_argument("-p", "--password", type=str, action="store")
    parser.add_argument(
        "-c",
        "--ignore-certs",
        default=False,
        action="store_true",
        help="Ignore invalid SSL certificates",
    )
    parser.add_argument(
        "-s",
        "--server",
        type=str,
        action="store",
        default="http://localhost:8002/api/automation-hub/",
    )

    args = parser.parse_args()
    ignore = args.ignore
    https_verify = not args.ignore_certs
    client = GalaxyClient(
        args.server, (args.username, args.password), https_verify=https_verify
    )
    try:
        funs = {
            "user": user,
            "group": group,
            "namespace": namespace,
            "container": container,
            "collection": collection,
            "url": url,
        }
        if args.object in funs:
            funs[args.object](args.rest, client)
        else:
            print(f"Unknown resource type '{args.object}'")
            sys.exit(EXIT_UNKNOWN_ERROR)
    except GalaxyClientError:
        if not ignore:
            raise

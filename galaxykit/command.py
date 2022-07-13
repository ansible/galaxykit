import argparse
import sys
import json
from pprint import pprint

from .client import GalaxyClient
from .utils import GalaxyClientError
from . import containers
from . import collections
from . import groups
from . import namespaces
from . import users
from . import container_images
from . import registries
from . import __version__ as VERSION

EXIT_OK = 0
EXIT_UNKNOWN_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_DUPLICATE = 4


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


# galaxykit <kind> <operation> [<subop>] (args)
KIND_OPS = {
    "collection": {
        "help": "Collection",
        "ops": {
            "list": {
                "help": "List all collections",
                "args": None,
            },
            "upload": {
                "help": "Create and upload a new collection",
                "args": {
                    "namespace": {
                        "help": "Collection namespace (optional, defaults to --username)",
                        "nargs": "?",
                        "default": None,
                    },
                    "collection_name": {
                        "help": "Collection name (optional, randomly generated)",
                        "nargs": "?",
                        "default": None,
                    },
                    "version": {
                        "help": "Version (optional, defaults to 1.0.0)",
                        "nargs": "?",
                        "default": "1.0.0",
                    },
                },
            },
            "move": {
                "args": {
                    "namespace": {},
                    "collection_name": {},
                    "version": {"nargs": "?", "default": "1.0.0"},
                    "source": {"nargs": "?", "default": "staging"},
                    "destination": {"nargs": "?", "default": "published"},
                },
            },
            "delete": {
                "args": {
                    "namespace": {},
                    "collection": {},
                    "version": {"nargs": "?", "default": None},
                    "repository": {"nargs": "?", "default": "published"},
                },
            },
            "download": None,
            "info": {
                "args": {
                    "repository": {"nargs": "?", "default": "published"},
                    "namespace": {},
                    "collection_name": {},
                    "version": {},
                },
            },
            "sign": {
                "args": {
                    "repository": {"nargs": "?", "default": "published"},
                    "namespace": {},
                    "collection_name": {},
                    "version": {},
                },
            },
        },
    },
    "namespace": {
        "help": "Collection Namespace",
        "ops": {
            "get": {
                "args": {
                    "name": {},
                }
            },
            "list": {"args": None},
            "list-collections": {
                "args": {
                    "name": {},
                }
            },
            "create": {
                "args": {
                    "name": {},
                    "group": {"nargs": "?", "default": None},
                }
            },
            "delete": {
                "args": {
                    "name": {},
                }
            },
            "groups": None,
            "addgroup": {
                "args": {
                    "name": {},
                    "group": {},
                }
            },
            "removegroup": {
                "args": {
                    "name": {},
                    "group": {},
                }
            },
            "addgroupperm": None,
            "removegroupperm": None,
            "sign": None,
        },
    },
    "container": {
        "help": "Execution Environment",
        "ops": {
            "readme": {
                "args": {
                    "container": {},
                    "readme": {"nargs": "?", "default": None},
                }
            },
            "delete": {
                "args": {
                    "name": {},
                }
            },
            "create": {
                "args": {
                    "name": {},
                    "upstream_name": {},
                    "registry": {},
                }
            },
        },
    },
    "container-image": {
        "help": "Execution Environment image",
        "ops": {
            "delete": {
                "args": {
                    "container": {},
                    "image": {},
                }
            },
        },
    },
    "registry": {
        "help": "Remote Registry",
        "ops": {
            "delete": {
                "args": {
                    "name": {},
                }
            },
            "create": {
                "args": {
                    "name": {},
                    "url": {},
                }
            },
        },
    },
    "user": {
        "help": "RBAC User",
        "ops": {
            "list": {"args": None},
            "create": {
                "args": {
                    "username": {},
                    "password": {},
                    "--email": {},
                    "--first_name": {},
                    "--is_superuser": {
                        "action": "store_true",
                        "default": False,
                    },
                    "--last_name": {},
                }
            },
            "delete": {
                "args": {
                    "username": {},
                }
            },
            "group": {
                "help": "User group membership",
                "subops": {
                    "add": {
                        "help": "Add user to group",
                        "args": {
                            "username": {},
                            "groupname": {},
                        },
                    },
                    "remove": {
                        "help": "Remove user from group",
                        "args": {
                            "username": {},
                            "groupname": {},
                        },
                    },
                },
            },
        },
    },
    "group": {
        "help": "RBAC Group",
        "ops": {
            "list": {"args": None},
            "create": {
                "args": {
                    "name": {},
                }
            },
            "delete": {
                "args": {
                    "name": {},
                }
            },
            "perm": {
                "subops": {
                    "list": {
                        "args": {
                            "groupname": {},
                        }
                    },
                    "add": {
                        "args": {
                            "groupname": {},
                            "perm": {},
                        }
                    },
                    "remove": {
                        "args": {
                            "groupname": {},
                            "perm": {},
                        }
                    },
                },
            },
        },
    },
    "url": {
        "help": "Generic GET/POST",
        "ops": {
            "get": {
                "args": {
                    "url": {},
                }
            },
            "post": {
                "args": {
                    "url": {},
                }
            },
        },
    },
}


def parse_args(parser, args):
    for arg in args:
        parser.add_argument(arg, **(args[arg]))


def parse_subop(subparsers, subop, subop_params):
    parser = subparsers.add_parser(subop, help=subop_params.get("help"))
    args = subop_params.get("args")

    if args:
        parse_args(parser, args)


def parse_subops(parser, subops):
    subparsers = parser.add_subparsers(dest="subop", required=True)

    for subop in subops:
        subop_params = subops[subop]
        parse_subop(subparsers, subop, subop_params)


def parse_op(subparsers, op, op_params):
    if op_params == None:
        help, args, subops = "Not implemented", None, None
    else:
        help, args, subops = (
            op_params.get("help"),
            op_params.get("args"),
            op_params.get("subops"),
        )

    parser = subparsers.add_parser(op, help=help)

    if subops:
        parse_subops(parser, subops)

    if args:
        parse_args(parser, args)


def parse_ops(parser, ops):
    subparsers = parser.add_subparsers(
        dest="operation", help="Operation", required=True
    )

    for op in ops:
        op_params = ops[op]
        parse_op(subparsers, op, op_params)


def parse_kind(subparsers, kind, kind_params):
    parser = subparsers.add_parser(kind, help=kind_params.get("help"))
    parse_ops(parser, kind_params["ops"])


def parse_kinds(parser):
    subparsers = parser.add_subparsers(
        dest="kind",
        help="Kind of API content to operate against",
        required=True,
    )

    for kind in KIND_OPS:
        kind_params = KIND_OPS[kind]
        parse_kind(subparsers, kind, kind_params)


def params_main(parser):
    parser.add_argument(
        "-i",
        "--ignore",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-u",
        "--username",
        action="store",
        default="admin",
        dest="auth_username",
        type=str,
    )
    parser.add_argument(
        "-p",
        "--password",
        action="store",
        default="admin",
        dest="auth_password",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--token",
        action="store",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--auth-url",
        action="store",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--ignore-certs",
        action="store_true",
        default=False,
        help="Ignore invalid SSL certificates",
    )
    parser.add_argument(
        "-s",
        "--server",
        action="store",
        default="http://localhost:8002/api/automation-hub/",
        type=str,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=("%(prog)s " + VERSION),
    )


def main():
    parser = argparse.ArgumentParser(prog="galaxykit")
    params_main(parser)
    parse_kinds(parser)

    args = parser.parse_args()
    if args.debug:
        pprint(args)

    https_verify = not args.ignore_certs

    if args.auth_url and not args.token:
        creds = {
            "auth_url": args.auth_url,
            "username": args.auth_username,
            "password": args.auth_password,
        }
    elif args.token:
        creds = {
            "token": args.token,
        }
        if args.auth_url:
            creds["auth_url"] = args.auth_url
    else:
        creds = {
            "username": args.auth_username,
            "password": args.auth_password,
        }
    client = GalaxyClient(args.server, creds, https_verify=https_verify)

    resp = None

    try:
        if args.kind == "user":
            if args.operation == "list":
                resp = users.get_user_list(client)
                print(format_list(resp["data"], "username"))
            elif args.operation == "create":
                username, password, email, first_name, is_superuser, last_name = (
                    args.username,
                    args.password,
                    args.email or "",
                    args.first_name or "",
                    args.is_superuser,
                    args.last_name or "",
                )
                created, resp = users.get_or_create_user(
                    client,
                    username,
                    password,
                    None,
                    first_name,
                    last_name,
                    email,
                    is_superuser,
                )
                if created:
                    print("Created user", username)
                elif not args.ignore:
                    print(f"User {username} already existed")
                    sys.exit(EXIT_NOT_FOUND)
                else:
                    print(f"User {username} already existed")
            elif args.operation == "delete":
                username = args.username
                try:
                    resp = users.delete_user(client, username)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            elif args.operation == "group":
                if args.subop == "add":
                    username, groupname = args.username, args.groupname
                    user_data = users.get_user(client, username)
                    group_id = groups.get_group_id(client, groupname)
                    user_data["groups"].append(
                        {
                            "id": group_id,
                            "name": groupname,
                            "pulp_href": f"/pulp/api/v3/groups/{group_id}",
                        }
                    )
                    resp = users.update_user(client, user_data)
                elif args.subop == "remove":
                    username, groupname = args.username, args.groupname
                    user_data = users.get_user(client, username)
                    group_id = groups.get_group_id(client, groupname)
                    user_data["groups"] = list(
                        filter(
                            lambda group: group["id"] != group_id, user_data["groups"]
                        )
                    )
                    resp = users.update_user(client, user_data)

        elif args.kind == "group":
            if args.operation == "list":
                resp = groups.get_group_list(client)
                print(format_list(resp["data"], "name"))
            elif args.operation == "create":
                name = args.name
                resp = groups.create_group(client, name)
            elif args.operation == "delete":
                name = args.name
                try:
                    resp = groups.delete_group(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            elif args.operation == "perm":
                if args.subop == "list":
                    groupname = args.groupname
                    resp = groups.get_permissions(client, groupname)
                    print(format_list(resp["data"], "permission"))
                elif args.subop == "add":
                    groupname, perm = args.groupname, args.perm
                    perms = [
                        p["permission"]
                        for p in groups.get_permissions(client, groupname)["data"]
                    ]
                    perms = list(set(perms) | set([perm]))
                    resp = groups.set_permissions(client, groupname, perms)
                elif args.subop == "remove":
                    groupname, perm = args.groupname, args.perm
                    resp = groups.delete_permission(client, groupname, perm)

        elif args.kind == "namespace":
            if args.operation == "get":
                name = args.name
                print(json.dumps(namespaces.get_namespace(client, name)))
            elif args.operation == "list":
                print(json.dumps(namespaces.get_namespace_list(client)))
            elif args.operation == "list-collections":
                name = args.name
                print(json.dumps(namespaces.get_namespace_collections(client, name)))
            elif args.operation == "create":
                name, group = args.name, args.group
                resp = namespaces.create_namespace(client, name, group)

            elif args.operation == "delete":
                name = args.name
                try:
                    resp = namespaces.delete_namespace(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)

            elif args.operation == "groups":
                raise NotImplementedError
            elif args.operation == "addgroup":
                name, group = args.name, args.group
                resp = namespaces.add_group(client, name, group)
            elif args.operation == "removegroup":
                name, group = args.name, args.group
                resp = namespaces.remove_group(client, name, group)
            elif args.operation == "addgroupperm":
                raise NotImplementedError
            elif args.operation == "removegroupperm":
                raise NotImplementedError
            elif args.operation == "sign":
                raise NotImplementedError

        elif args.kind == "container":
            if args.operation == "readme":
                if args.readme == None:
                    container = args.container
                    resp = containers.get_readme(client, container)
                    print(resp["text"])
                else:
                    container, readme = args.container, args.readme
                    resp = containers.set_readme(client, container, readme)

            elif args.operation == "delete":
                name = args.name
                try:
                    resp = containers.delete_container(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)

            elif args.operation == "create":
                name, upstream_name, registry = (
                    args.name,
                    args.upstream_name,
                    args.registry,
                )
                try:
                    resp = containers.create_container(
                        client, name, upstream_name, registry
                    )
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)

        elif args.kind == "container-image":
            if args.operation == "delete":
                container, image = args.container, args.image
                try:
                    resp = container_images.delete_container(client, container, image)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)

        elif args.kind == "registry":
            if args.operation == "delete":
                name = args.name
                try:
                    resp = registries.delete_registry(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            elif args.operation == "create":
                name, url = args.name, args.url
                try:
                    resp = registries.create_registry(client, name, url)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)

        elif args.kind == "collection":
            if args.operation == "list":
                print(json.dumps(collections.get_collection_list(client)))
            elif args.operation == "upload":
                namespace, collection_name, version = (
                    args.namespace or client.username,
                    args.collection_name,
                    args.version or "1.0.0",
                )

                resp = namespaces.create_namespace(client, namespace, None)
                artifact = collections.upload_test_collection(
                    client,
                    namespace=namespace,
                    collection_name=collection_name,
                    version=version,
                )
                print(json.dumps(artifact))
            elif args.operation == "move":
                namespace, collection_name, version, source, destination = (
                    args.namespace,
                    args.collection_name,
                    args.version or "1.0.0",
                    args.source or "staging",
                    args.destination or "published",
                )
                collections.move_collection(
                    client, namespace, collection_name, version, source, destination
                )
            elif args.operation == "delete":
                namespace, collection, version, repository = (
                    args.namespace,
                    args.collection,
                    args.version,
                    args.repository or "published",
                )
                try:
                    if version == "None":
                        version = None
                    resp = collections.delete_collection(
                        client, namespace, collection, version, repository
                    )
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            elif args.operation == "download":
                raise NotImplementedError
            elif args.operation == "info":
                repository, namespace, collection_name, version = (
                    args.repository or "published",
                    args.namespace,
                    args.collection_name,
                    args.version,
                )
                print(
                    json.dumps(
                        collections.collection_info(
                            client, repository, namespace, collection_name, version
                        )
                    )
                )
            elif args.operation == "sign":
                repository, namespace, collection_name, version = (
                    args.repository or "published",
                    args.namespace,
                    args.collection_name,
                    args.version,
                )
                print(
                    json.dumps(
                        collections.collection_sign(
                            client, repository, namespace, collection_name, version
                        )
                    )
                )

        elif args.kind == "url":
            if args.operation == "get":
                url = args.url
                print(json.dumps(client.get(url)))
            elif args.operation == "post":
                url = args.url
                body = sys.stdin.read()
                print(json.dumps(client.post(url, body)))

        if resp and not args.ignore:
            report_error(resp)

    except GalaxyClientError:
        if not args.ignore:
            raise

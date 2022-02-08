import argparse
import sys
import json

from .client import GalaxyClient, GalaxyClientError
from . import containers
from . import collections
from . import groups
from . import namespaces
from . import users
from . import container_images
from . import registries

EXIT_OK = 0
EXIT_UNKNOWN_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_DUPLICATE = 4


def print_unknown_error(args):
    print(f"Unknown {args.kind} operation '{args.operation}'")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "kind",
        type=str,
        action="store",
        help="Kind of API content to operate against (user, group, namespace)",
    )
    parser.add_argument("operation", type=str, action="store")
    parser.add_argument("rest", type=str, action="store", nargs="*")
    parser.add_argument("-i", "--ignore", default=False, action="store_true")
    parser.add_argument("-u", "--username", type=str, action="store")
    parser.add_argument("-p", "--password", type=str, action="store")
    parser.add_argument("-t", "--token", type=str, action="store")
    parser.add_argument("-a", "--auth-url", type=str, action="store")
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
    https_verify = not args.ignore_certs

    if args.token:
        creds = {
            "token": args.token,
        }
        if args.auth_url:
            creds["auth_url"] = args.auth_url
    else:
        creds = {
            "username": args.username,
            "password": args.password,
        }
    client = GalaxyClient(
        args.server, creds, https_verify=https_verify
    )

    resp = None

    try:
        if args.kind == "user":
            if args.operation == "list":
                resp = users.get_user_list(client)
                print(format_list(resp["data"], "username"))
            elif args.operation == "create":
                username, password = args.rest
                created, resp = users.get_or_create_user(
                    client, username, password, None
                )
                if created:
                    print("Created user", username)
                else:
                    print(f"User {username} already existed")
            elif args.operation == "delete":
                (username,) = args.rest
                try:
                    resp = users.delete_user(client, username)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            elif args.operation == "group":
                subop, *subopargs = args.rest
                if subop == "add":
                    username, groupname = subopargs
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
            else:
                print_unknown_error(args)

        elif args.kind == "group":
            if args.operation == "list":
                resp = groups.get_group_list(client)
                print(format_list(resp["data"], "name"))
            elif args.operation == "create":
                (name,) = args.rest
                resp = groups.create_group(client, name)
            elif args.operation == "delete":
                (name,) = args.rest
                try:
                    resp = groups.delete_group(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            elif args.operation == "perm":
                subop, *subopargs = args.rest
                if subop == "list":
                    (groupname,) = subopargs
                    resp = groups.get_permissions(client, groupname)
                    print(format_list(resp["data"], "permission"))
                elif subop == "add":
                    groupname, perm = subopargs
                    perms = [
                        p["permission"]
                        for p in groups.get_permissions(client, groupname)["data"]
                    ]
                    perms = list(set(perms) | set([perm]))
                    resp = groups.set_permissions(client, groupname, perms)
                elif subop == "remove":
                    groupname, perm = subopargs
                    resp = groups.delete_permission(client, groupname, perm)
                else:
                    print(f"Unknown group perm operation '{subop}'")
                    sys.exit(EXIT_UNKNOWN_ERROR)
            else:
                print_unknown_error(args)

        elif args.kind == "namespace":
            if args.operation == "get":
                (name,) = args.rest
                print(json.dumps(namespaces.get_namespace(client, name)))
            elif args.operation == "list":
                print(json.dumps(namespaces.get_namespace_list(client)))
            elif args.operation == "list-collections":
                (name,) = args.rest
                print(json.dumps(namespaces.get_namespace_collections(client, name)))
            elif args.operation == "create":
                if len(args.rest) == 2:
                    name, group = args.rest
                else:
                    (name,) = args.rest
                    group = None
                resp = namespaces.create_namespace(client, name, group)

            elif args.operation == "delete":
                (name,) = args.rest
                try:
                    resp = namespaces.delete_namespace(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)

            elif args.operation == "groups":
                raise NotImplementedError
            elif args.operation == "addgroup":
                name, group = args.rest
                resp = namespaces.add_group(client, name, group)
            elif args.operation == "removegroup":
                name, group = args.rest
                resp = namespaces.remove_group(client, name, group)
            elif args.operation == "addgroupperm":
                raise NotImplementedError
            elif args.operation == "removegroupperm":
                raise NotImplementedError
            elif args.operation == "sign":
                raise NotImplementedError
            else:
                print_unknown_error(args)

        elif args.kind == "container":
            if args.operation == "readme":
                if len(args.rest) == 1:
                    (container,) = args.rest
                    resp = containers.get_readme(client, container)
                    print(resp["text"])
                elif len(args.rest) == 2:
                    container, readme = args.rest
                    resp = containers.set_readme(client, container, readme)
                else:
                    print("container readme takes either 1 or 2 parameters.")
                    sys.exit(EXIT_UNKNOWN_ERROR)
            elif args.operation == "delete":
                (name,) = args.rest
                try:
                    resp = containers.delete_container(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            else:
                print_unknown_error(args)

        elif args.kind == "container-image":
            if args.operation == "delete":
                container, image  = args.rest
                try:
                    resp = container_images.delete_container(client, container, image)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            else:
                print_unknown_error(args) 

        elif args.kind == "registry":
            if args.operation == "delete":
                (name,) = args.rest
                try:
                    resp = registries.delete_registry(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            else:
                print_unknown_error(args) 

        elif args.kind == "collection":
            if args.operation == "upload":
                if len(args.rest) == 0:
                    (namespace, collection_name) = (client.username, None)
                else:
                    (namespace, collection_name) = args.rest

                resp = namespaces.create_namespace(client, namespace, None)
                artifact = collections.upload_test_collection(
                    client, namespace=namespace, collection_name=collection_name
                )
                print(json.dumps(artifact))
            elif args.operation == "move":
                if len(args.rest) == 2:
                    (namespace, collection_name) = args.rest
                    # defaults to version = 1.0.0, source = staging, destination = published
                    collections.move_collection(client, namespace, collection_name)
                else:
                    (
                        namespace,
                        collection_name,
                        version,
                        source,
                        destination,
                    ) = args.rest
                    collections.move_collection(
                        client, namespace, collection_name, version, source, destination
                    )
            elif args.operation == "delete":
                if len(args.rest) == 3:
                    namespace, collection, version = args.rest
                if len(args.rest) == 2:
                    namespace, collection = args.rest
                    version = None    
                try:
                    resp = collections.delete_collection(client, namespace, collection, version)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            elif args.operation == "download":
                raise NotImplementedError
            elif args.operation == "info":
                if len(args.rest) == 3:
                    (namespace, collection_name, version) = args.rest
                    repository = "published"
                elif len(args.rest) == 4:
                    (repository, namespace, collection_name, version) = args.rest
                else:
                    print("galaxykit collection info [repository] <namespace> <collection> <version>")
                    print(args.rest)
                    sys.exit(EXIT_UNKNOWN_ERROR)
                print(json.dumps(collections.collection_info(client, repository, namespace, collection_name, version)))
            elif args.operation == "sign":
                if len(args.rest) == 3:
                    (namespace, collection_name, version) = args.rest
                    repository = "published"
                elif len(args.rest) == 4:
                    (repository, namespace, collection_name, version) = args.rest
                else:
                    print("galaxykit collection info [repository] <namespace> <collection> <version>")
                    print(args.rest)
                    sys.exit(EXIT_UNKNOWN_ERROR)
                print(json.dumps(collections.collection_sign(client, repository, namespace, collection_name, version)))
            else:
                print_unknown_error(args)
            

        elif args.kind == "url":
            if args.operation == "get":
                (url,) = args.rest
                print(json.dumps(client.get(url)))
            elif args.operation == "post":
                url = args.rest[0]
                body = ""# sys.stdin.read()
                print(json.dumps(client.post(url, body)))
            else:
                print_unknown_error(args)

        else:
            print(f"Unknown resource type '{args.kind}'")
            sys.exit(EXIT_UNKNOWN_ERROR)

        if resp and not ignore:
            report_error(resp)

    except GalaxyClientError:
        if not ignore:
            raise

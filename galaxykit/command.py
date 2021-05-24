import argparse
import sys

from .client import GalaxyClient, GalaxyClientError
from . import users
from . import groups
from . import namespaces

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
            print(f"API Failure: HTTP {error['status']} {error['code']}; {error['title']} ({error['detail']})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", type=str, action="store",
        help="Kind of API content to operate against (user, group, namespace)")
    parser.add_argument("operation", type=str, action="store")
    parser.add_argument("rest", type=str, action="store", nargs="*")
    parser.add_argument("-i", "--ignore", default=False, action="store_true")
    parser.add_argument("-u", "--username", type=str, action="store")
    parser.add_argument("-p", "--password", type=str, action="store")
    parser.add_argument("-s", "--server", type=str, action="store",
        default="http://localhost:8002/api/automation-hub/")

    args = parser.parse_args()
    ignore = args.ignore
    client = GalaxyClient(args.server, (args.username, args.password))
    resp = None

    try:
        if args.kind == "user":
            if args.operation == "list":
                resp = users.get_user_list(client)
                print(format_list(resp["data"], "username"))
            if args.operation == "create":
                username, password = args.rest
                created, resp = users.get_or_create_user(client, username, password, None)
                if created:
                    print("Created user", username)
                else:
                    print(f"User {username} already existed")
            if args.operation == "delete":
                username, = args.rest
                try:
                    resp = users.delete_user(client, username)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)
            if args.operation == "group":
                subop, *subopargs = args.rest
                if subop == "add":
                    username, groupname = subopargs
                    user_data = users.get_user(client, username)
                    group_id = groups.get_group_id(client, groupname)
                    user_data["groups"].append({
                        "id": group_id,
                        "name": groupname,
                        "pulp_href": f"/pulp/api/v3/groups/{group_id}",
                    })
                    resp = users.update_user(client, user_data)

        elif args.kind == "group":
            if args.operation == "list":
                resp = groups.get_group_list(client)
                print(format_list(resp["data"], "name"))
            if args.operation == "create":
                name, = args.rest
                resp = groups.create_group(client, name)
            if args.operation == "delete":
                name, = args.rest
                try:
                    resp = groups.delete_group(client, name)
                except ValueError as e:
                    if not args.ignore:
                        print(e)
                        sys.exit(EXIT_NOT_FOUND)

        elif args.kind == "namespace":
            if args.operation == "list":
                raise NotImplementedError
            if args.operation == "create":
                if len(args.rest) == 2:
                    name, group = args.rest
                else:
                    name, = args.rest
                    group = None
                resp = namespaces.create_namespace(client, name, group)
            if args.operation == "delete":
                raise NotImplementedError
            if args.operation == "groups":
                raise NotImplementedError
            if args.operation == "addgroup":
                name, group = args.rest
                resp = namespaces.add_group(client, name, group)
            if args.operation == "removegroup":
                name, group = args.rest
                resp = namespaces.remove_group(client, name, group)
            if args.operation == "addgroupperm":
                raise NotImplementedError
            if args.operation == "removegroupperm":
                raise NotImplementedError
    
        if resp and not ignore:
            report_error(resp)
    
    except GalaxyClientError as e:
        if not ignore:
            raise

import argparse
import sys
import json
from typing import Collection
from . import cli_functions


def parse_collections(subparsers):
    return None


def parse_containers(subparsers):
    container_parser = subparsers.add_parser(
        "container", help="subcommand for manipulating container metadata"
    )
    container_subparser = container_parser.add_subparsers()

    # parsing the get-readme subcommand
    container_get_readme_parser = container_subparser.add_parser(
        "get-readme", help="Returns the readme for the given container."
    )
    container_get_readme_parser.add_argument(
        "collection_name", help="name of container."
    )
    container_get_readme_parser.get_defaults(function="container-get-readme")

    # parsing the set-readme subcommand
    container_set_readme_parser = container_subparser.add_parser(
        "set-readme",
        help="Sets the readme for the given container to the passed string.",
    )
    container_set_readme_parser.add_argument(
        "collection_name", help="Name of container."
    )
    container_set_readme_parser.add_argument(
        "new_readme", help="String that will be set as new readme."
    )
    container_set_readme_parser.set_defaults(function="container-set-readme")


def parse_groups(subparsers):
    """
    if args.operation == "list":
    elif args.operation == "create":
    elif args.operation == "delete":
    elif args.operation == "perm":
        if subop == "list":
        elif subop == "add":
        elif subop == "remove":
    """
    group_parser = subparsers.add_parser(
        "group", help="List, create, delete, edit permissions of groups."
    )
    group_subparser = group_parser.add_subparsers()

    # group list subcommand
    group_list_parser = group_subparser.add_parser("list", help="List all groups")
    group_list_parser.set_defaults(function="group-list")

    # group create
    group_create_parser = group_subparser.add_parser(
        "create", help="create a group with given name"
    )
    group_create_parser.add_argument(
        "group_name", type=str, help="name of group to be created."
    )
    group_create_parser.set_defaults(function="group-create")

    # group delete
    group_delete_parser = group_subparser.add_parser(
        "delete", help="delete a group with given name"
    )
    group_delete_parser.add_argument(
        "group_name", type=str, help="name of group to be deleted."
    )
    group_delete_parser.set_defaults(function="group-delete")

    # permissions subcommands
    group_perm_parser = subparsers.add_parser("perm", help="Permission subcommand")
    group_perm_subparser = group_parser.add_subparsers()

    """
        if subop == "list":
        elif subop == "add":
        elif subop == "remove":
    """
    # group perm list
    group_perm_list_parser = group_perm_subparser.add_parser(
        "list", help="list the permissions of a given group."
    )
    group_perm_list_parser.add_argument("group_name")
    group_perm_list_parser.set_defaults(function="group-perm-list")

    # group perm add
    group_perm_add_parser = group_perm_subparser.add_parser(
        "add", help="add the passed permission to the given group."
    )
    group_perm_add_parser.add_argument("group_name")
    group_perm_add_parser.add_argument("permission_name")
    group_perm_add_parser.set_defaults(function="group-perm-add")

    # group perm remove
    group_perm_remove_parser = group_perm_subparser.remove_parser(
        "remove", help="remove the passed permission from the given group."
    )
    group_perm_remove_parser.remove_argument("group_name")
    group_perm_remove_parser.remove_argument("permission_name")
    group_perm_remove_parser.set_defaults(function="group-perm-remove")


def parse_namespaces(subparsers):
    """
    # TODO: implement these down the line
    "delete":
    "groups":
    "addgroupperm":
    "removegroupperm":
    """

    namespace_parser = subparsers.add_parser("namespace", help="namespace help")
    namespace_subparser = namespace_parser.add_subparsers()

    # 'namespace get' subcommand
    namespace_get_parser = namespace_subparser.add_parser(
        "get", help="Get namespace metadata."
    )
    namespace_get_parser.set_defaults(function="get-namespace")
    namespace_get_parser.add_argument(
        "namespace",
        type=str,
    )

    # list Collections subcommand
    namespace_list_parser = namespace_subparser.add_parser(
        "list-collections", help="Get namespace collections."
    )
    namespace_list_parser.set_defaults(function="get-namespace-collections")
    namespace_list_parser.add_argument(
        "namespace",
        type=str,
    )

    # create a namespace subcommand
    namespace_create_parser = namespace_subparser.add_parser(
        "create", help="Create a namespace"
    )
    namespace_create_parser.set_defaults(function="create-namespace")
    namespace_create_parser.add_argument(
        "namespace",
        type=str,
    )

    # add group to a namespace subcommand
    namespace_add_group_parser = namespace_subparser.add_parser("add-group")
    namespace_add_group_parser.set_defaults(function="namespace-add-group")
    namespace_add_group_parser.add_argument(
        "namespace", type=str, help="Namespace name."
    )
    namespace_add_group_parser.add_argument("group", type=str, help="Namespace group.")

    # remove group from a namespace subcommand
    namespace_remove_group_parser = namespace_subparser.add_parser("remove-group")
    namespace_remove_group_parser.set_defaults(function="namespace-remove-group")
    namespace_remove_group_parser.add_argument(
        "namespace", type=str, help="Namespace name."
    )

    namespace_add_group_parser.add_argument("group", type=str, help="Namespace group.")


def parse_user(subparsers):
    user_parser = subparsers.add_parser("user", help="user help")
    user_subparser = user_parser.add_subparsers()

    # 'user list' subcommand
    user_list_parser = user_subparser.add_parser("list")
    user_list_parser.set_defaults(function=cli_functions.list_users)

    # 'user create' subcommand
    user_create_parser = user_subparser.add_parser("create")
    user_create_parser.add_argument(
        "new_user", type=str, help="username of the user to be created."
    )
    user_create_parser.add_argument(
        "new_password", type=str, help="password of the user to be created."
    )
    user_create_parser.add_argument(
        "--email", type=str, help="email of the user to be created."
    )
    user_create_parser.add_argument(
        "--first-name", type=str, help="first name of the user to be created."
    )
    user_create_parser.add_argument(
        "--last-name", type=str, help="last name of the user to be created."
    )
    user_create_parser.add_argument(
        "--is-superuser",
        help="make a superuser.",
        action="store_true",
        default=False,
    )
    user_create_parser.add_argument("--groups", type=str, help="add user to a group.")
    user_create_parser.set_defaults(function="user create")

    # 'user delete' subcommand
    user_delete_parser = user_subparser.add_parser("delete")
    user_delete_parser.add_argument(
        "user_to_delete", type=str, help="username of the user to be deleted."
    )
    user_delete_parser.set_defaults(function="user delete")


def test(command_to_test):
    parser = argparse.ArgumentParser(prog="galaxykit")
    subparsers = parser.add_subparsers()

    parser.add_argument("-i", "--ignore", default=False, action="store_true")
    parser.add_argument("-u", "--username", default="admin", type=str, action="store")
    parser.add_argument("-p", "--password", default="admin", type=str, action="store")
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

    # parsing for subcommands
    parse_collections(subparsers)
    parse_containers(subparsers)
    parse_groups(subparsers)
    parse_namespaces(subparsers)
    parse_user(subparsers)

    args = parser.parse_args(command_to_test)
    breakpoint()
    args.function(args)


command_to_test = "user list".split(" ")
test(command_to_test)

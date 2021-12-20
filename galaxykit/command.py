import argparse
import sys
import json


def parse_collections(subparsers):
    return None


def parse_containers(subparsers):
    return None


def parse_groups(subparsers):
    return None


def parse_namespaces(subparsers):
    """
    # these three only take 1 positional argument, which is the name of the namespace
    "get":
    "list-collections":
    "create":

    # these take 2 positional arguments, name and group
    "addgroup":
    "removegroup":

    # all the below just raise NotImplementedError
    # TODO: implement these down the line
    "delete":
    "groups":
    "addgroupperm":
    "removegroupperm":
    """

    namespace_parser = subparsers.add_parser("namespace", help="namespace help")
    namespace_subparser = namespace_parser.add_subparsers()

    # 'namespace list' subcommand
    namespace_create_parser = namespace_subparser.add_parser("get")
    namespace_create_parser.add_argument(
        "namespace", type=str, help="Namespace to be listed."
    )


def parse_user(subparsers):
    user_parser = subparsers.add_parser("user", help="user help")
    user_subparser = user_parser.add_subparsers()

    # 'user list' subcommand
    user_create_parser = user_subparser.add_parser("list")
    user_create_parser.set_defaults(function="list")

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
        "--is-superuser", help="make a superuser.", action='store_true', default=False,
    )
    user_create_parser.add_argument(
        "--groups", type=str, help="add user to a group."
    )
    user_create_parser.set_defaults(function="create")

    # 'user delete' subcommand
    user_delete_parser = user_subparser.add_parser("delete")
    user_delete_parser.add_argument(
        "user_to_delete", type=str, help="username of the user to be deleted."
    )
    user_delete_parser.set_defaults(function="delete")


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
    print(args)


command_to_test = "user create newusername newpasswd --email '$jdoe@redhat.com' --last-name Doe".split(
    " "
)
test(command_to_test)

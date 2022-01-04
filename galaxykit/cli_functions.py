from client import GalaxyClient, GalaxyClientError
import containers
import collections
import groups
import namespaces
import users


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


def get_client(args):
    ignore = args.ignore
    https_verify = not args.ignore_certs
    return GalaxyClient(
        args.server, (args.username, args.password), https_verify=https_verify
    )


## users
def user_list(args):
    client = get_client(args)
    resp = users.get_user_list(client)
    print(format_list(resp["data"], "username"))
    return resp


def user_create(args):
    client = get_client(args)
    if args.group:
        args.group = groups.get_group(client, args.group)
    created, resp = users.get_or_create_user(
        client,
        args.new_user,
        args.new_password,
        args.group,
        fname=args.first_name,
        lname=args.last_name,
        email=args.email,
        superuser=args.is_superuser,
    )
    if created:
        print("Created user", args.username)
    else:
        print(f"User {args.username} already existed")
    return resp


def user_delete(args):
    client = get_client(args)
    users.delete_user(client, args.user_to_delete)
    # there's no response from the above call, so we need to explicitly
    # add a return that indicates success or failure here.
    try:
        users.get_user(client, args.user_to_delete)
        print(f"Unable to delete user {args.user_to_delete}")
        return False
    except:
        print(f"Successfully deleted user {args.user_to_delete}")
        return True


# containers

##groups

##collections

##namespaces

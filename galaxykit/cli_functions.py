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
def list_users(args):
    client = get_client(args)
    resp = users.get_user_list(client)
    print(format_list(resp["data"], "username"))


#containers

##groups

##collections

##namespaces

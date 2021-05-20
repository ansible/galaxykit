from . import groups

def create_namespace(client, name, group):
    group_id = groups.get_group_id(client, group)
    create_body = {
        "name": name,
        "groups": [
            {
                "id": group_id,
                "name": group,
                "object_permissions": ["change_namespace", "upload_to_namespace"],
            }
        ],
    }

    return client.post("v3/namespaces/", create_body)

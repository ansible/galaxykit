## Version 0.10.1
* Handle an RBAC version check case where the property is checked before the first request
* Debug logging for external commands (docker/podman)
## Version 0.10.0
* Support for RBAC in galaxy_ng 4.6.0dev and greater
* Refresh JWT tokens when expired
* Remove set_permissions
* Add object_roles parameter to namespace creation
* Add role commands
* Add get_collection
* Replace perm subcommand with role subcommand
* Add get_container_images command
* Add add_owner_to_ee command
* Replace all groups commands to handle roles instead of permissions
* Add remotes module
* Add roles module
## Version 0.8.0
* Remove references to GalaxyError (#55)
* commit utils.py (#54)
* added methods for sync testing
* Keep python3.8 compatibility - argparse.BooleanOptionalAction is 3.9+; fix superuser creation
* Merge pull request #49 from ShaiahWren/add-extra-fields-user-create
* Merge pull request #47 from himdel/command-parse
* command: create subparsers from data
* Merge pull request #45 from ansible/add-repo-options
* Add support for listing and deleting all collections
* Delete Collections - add ability to delete collections in different repositories (#25)
* Merge pull request #44 from ansible/add-version-upload
* Added support for upload exact collection version
* collection info, collection delete - use v3/plugin/ansible/ URLs (#42)
* Use user+pass to fetch an auth_token from Keycloak  (#41)
* Merge pull request #40 from himdel/ee_include_tags_latest
* container create: add include_tags=latest
* Add a default tag to the new collections to pass cloud requirements. (#38)
* fix sso auth for collection uploads (#37)
* Add CONTRIBUTE.md for guidance (#32)
* Fix github action - allow the workflow to add suggestions, not just warnings
* Added support for Keycloak and collection signing (#28)
* Create container exclude and include tags addition
* Remove username and password from create registry
* Create EE container
* User remove group + regitry create
* Add github action to run black and suggest the changes
* Run black, commit results
## Version 0.7.0
* Add CLI command and function for listing namespaces.
* Support for deletion of Collections (both versions and whole), Namespaces, Containers, Container Images, Execution Enviroments Registry.
## Version 0.6.0
* Add collection move function - accessible via `galaxykit collection move <namespace> <name>` which assumes collection version = 1.0.0 and the source repo = staging and the destination repo = published. Alternatively those arguments can be supplied, in that order (e.g. `galaxykit collection move admin collection_dep_a_asdfasdf 1.2.0 rejected published`.
* Addition of `--ignore-certs` (short version is `-c`) to enable running against insecure instances of galaxy.
* Expand return values from some functions to have more valuable information.
## Version 0.5.2
Bugfix: fix double-slash in content URL
## Version 0.5.1
Bugfix: fix login to handle missing container utilities.
## Version 0.5.0
Updates to namespaces and add collection functionality
* List the metadata of a namespace
* List all the collections in a namespace
* Upload test collections with a given name to a given namespace
* Rename dockerUtils to containerUtils to avoid using Docker trademark.
## Version 0.4.0
Allow passing both a simple username/password tuple or a {username, password, token} dict.
* Allows re-use of token from another client
* Uses username/password for container registry login
## Version 0.1.0
A command-line wrapper has been added to Galaxykit, enabling it to be used by non-Python
code including Javascript UI tests.
* namespace module was added to create test namespaces
* Installing the galaxy-kit package now installs a galaxykit command in your PATH
* HTTP request and response handling has been centralized in GalaxyClient
* module functions now take the GalaxyClient object directly, instead of the root URL and headers

## Version 0.0.1
An initial prototype implementing basic functionality:
* Creation, fetch, and delete of user accounts
* Creation, deletion, and permission setting of groups
* Utilities to push tagged containers into the services container registry
* Authentication support

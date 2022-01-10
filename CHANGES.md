## Version 0.6.1
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

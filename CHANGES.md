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
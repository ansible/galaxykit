import os


RBAC_VERSION = "4.6.0dev"
EE_ENDPOINTS_CHANGE_VERSION = "4.7.0dev"

SLEEP_SECONDS_POLLING = int(os.environ.get('GALAXYKIT_SLEEP_SECONDS_POLLING', 10))
SLEEP_SECONDS_ONETIME = int(os.environ.get('GALAXYKIT_SLEEP_SECONDS_ONETIME', 10))
POLLING_MAX_ATTEMPTS = int(os.environ.get('GALAXYKIT_POLLING_MAX_ATTEMPTS', 10))

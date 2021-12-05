import logging

DB_PATH = "test.db"
DEFAULT_DB_VERSION = "1.0.0"
SUPPORTED_DB_VERSION = [
    DEFAULT_DB_VERSION,
]

KEYRING_SERVICE_NAME = "onetimepass"
KEYRING_USERNAME = "master key"

LOG_LEVEL = (
    logging.DEBUG
)  # TODO change this for the production version OR implement CLI option for that

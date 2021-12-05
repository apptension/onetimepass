import logging

DB_PATH = "test.db"
DEFAULT_DB_VERSION = "1.0.0"
SUPPORTED_DB_VERSION = [
    DEFAULT_DB_VERSION,
]
DEFAULT_HASH_ALGORITHM = "sha1"
DEFAULT_DIGITS_COUNT = 6
DEFAULT_TIME_STEP_SECONDS = 30
DEFAULT_HOTP_COUNTER = 0

KEYRING_SERVICE_NAME = "onetimepass"
KEYRING_USERNAME = "master key"

LOG_LEVEL = (
    logging.DEBUG
)  # TODO change this for the production version OR implement CLI option for that

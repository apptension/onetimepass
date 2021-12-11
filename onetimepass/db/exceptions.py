import pathlib

from onetimepass import settings


class BaseDBException(Exception):
    pass


class DBCorruption(BaseDBException):
    def __init__(self):
        super().__init__("Database is corrupted")


class DBDoesNotExist(BaseDBException):
    pass


class DBAlreadyInitialized(BaseDBException):
    def __init__(self, path: pathlib.Path):
        super().__init__(f"The local database `{path}` is already initialized")


class DBUnsupportedVersion(BaseDBException):
    def __init__(self, version: str):
        super().__init__(
            f"Database version {version} is not supported."
            f" Supported versions: {settings.SUPPORTED_DB_VERSION}"
        )


class DBMergeConflict(BaseDBException):
    pass


class DBUnsupportedMigration(DBMergeConflict):
    pass

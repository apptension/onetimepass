import functools
import getpass

from onetimepass import settings


try:
    import keyring  # noqa 'keyring' in the try block with 'except ImportError' should also be defined in the except block
except ImportError:
    KEYRING_INSTALLED = False
else:
    KEYRING_INSTALLED = True
    KEYRING_PARAMS = {
        "service_name": settings.KEYRING_SERVICE_NAME,
        "username": settings.KEYRING_USERNAME,
    }
    keyring_set = functools.partial(keyring.set_password, **KEYRING_PARAMS)
    keyring_get = functools.partial(keyring.get_password, **KEYRING_PARAMS)


class BaseMasterKeyException(Exception):
    pass


class KeyringException(BaseMasterKeyException):
    pass


class KeyringNotInstalledException(KeyringException):
    def __init__(self):
        super().__init__("Keyring not installed")


class InvalidMasterKeyFormat(BaseMasterKeyException):
    pass


class EmptyKeyException(InvalidMasterKeyFormat):
    def __init__(self):
        super().__init__("Provided master key must be non-empty")


class MasterKey:
    def __init__(self, *, use_keyring=True):
        key = (
            self._get_key_from_keyring()
            if use_keyring
            else self._get_key_from_user_input()
        )

        if not key:
            raise EmptyKeyException

        self._key: str = key

    @classmethod
    def create_in_keyring(cls, key: str) -> "MasterKey":
        if not cls.keyring_available():
            raise KeyringNotInstalledException

        keyring_set(password=key)
        return cls(use_keyring=True)

    @classmethod
    def _get_key_from_keyring(cls) -> str:
        if not cls.keyring_available():
            raise KeyringNotInstalledException
        return keyring_get()

    @classmethod
    def _get_key_from_user_input(cls) -> str:
        return getpass.getpass("Enter master key: ")

    @staticmethod
    def keyring_available() -> bool:
        return KEYRING_INSTALLED

    def __str__(self):
        return self._key

    def __bytes__(self):
        return self._key.encode()

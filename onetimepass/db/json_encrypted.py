from __future__ import annotations

import json
import pathlib

from cryptography.fernet import Fernet

from .base import BaseDB
from .exceptions import DBAlreadyInitialized
from .exceptions import DBDoesNotExist
from .models import DatabaseSchema


class JSONEncryptedDB(BaseDB):
    def __init__(self, path: pathlib.Path, key: bytes):
        self.path = path
        self.key = key
        self.fernet = Fernet(key)

    @classmethod
    def initialize(cls, path: pathlib.Path) -> JSONEncryptedDB:
        """Generate key and initialize empty database"""
        if path.exists():
            raise DBAlreadyInitialized(path)
        key = Fernet.generate_key()
        db = cls(path=path, key=key)
        data = DatabaseSchema.initialize()
        db.path.parent.mkdir(parents=True, exist_ok=True)
        db.write(data)
        return db

    def read(self) -> DatabaseSchema:
        if not self.path.exists():
            raise DBDoesNotExist()
        with self.path.open("rb") as f:
            data = self.fernet.decrypt(f.read())
        return DatabaseSchema(**json.loads(data))

    def write(self, data: DatabaseSchema):
        with self.path.open("wb") as f:
            f.write(self.fernet.encrypt(data.json().encode()))

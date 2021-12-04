from __future__ import annotations

import json
import pathlib

from cryptography.fernet import Fernet

from .base import BaseDB
from .exceptions import DBDoesNotExist
from .models import DatabaseSchema


class JSONEncryptedDB(BaseDB):
    def __init__(self, path: str, key: bytes):
        self.path = path
        self.key = key
        self.fernet = Fernet(key)

    @classmethod
    def initialize(cls, path: str) -> JSONEncryptedDB:
        """Generate key and initialize empty database"""
        key = Fernet.generate_key()
        db = cls(path=path, key=key)
        data = DatabaseSchema.initialize()
        db.write(data)
        return db

    @classmethod
    def exists(cls, path: str) -> bool:
        return pathlib.Path(path).exists()

    def read(self) -> DatabaseSchema:
        if not self.exists(self.path):
            raise DBDoesNotExist()
        with open(self.path, "rb") as f:
            data = self.fernet.decrypt(f.read())
        return DatabaseSchema(**json.loads(data))

    def write(self, data: DatabaseSchema):
        with open(self.path, "wb") as f:
            f.write(self.fernet.encrypt(json.dumps(data.dict()).encode()))

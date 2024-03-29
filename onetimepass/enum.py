from __future__ import annotations

import enum
from typing import Any


class StrEnum(str, enum.Enum):
    pass


class CaseInsensitiveStrEnum(StrEnum):
    @classmethod
    def _missing_(cls, value: Any) -> CaseInsensitiveStrEnum | None:
        for member in cls:
            if member.value.casefold() == str(value).casefold():
                return member
        return None


class OTPType(CaseInsensitiveStrEnum):
    HOTP = "HOTP"
    TOTP = "TOTP"


class HashAlgorithm(CaseInsensitiveStrEnum):
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA512 = "SHA512"


class ExportFormat(CaseInsensitiveStrEnum):
    JSON = "json"

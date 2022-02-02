from __future__ import annotations

import datetime
import enum
import typing

from pydantic import validator

from onetimepass import settings
from onetimepass.base_model import BaseModel
from onetimepass.db import exceptions

"""
# Example database schema

## If just initialized

```json
{
  "otp": {},
  "version": "<DB_VERSION>",
}
```

## After adding some secrets

```json
}
  "otp": {
    "keeper": {
      "secret": "",
      "digits_count": 0,
      "hash_algorithm": "",
      "params": {
        otp_type: "HOTP|TOTP",
        // if otp_type == HOTP
        "counter": 0,

        // if otp_type == TOTP
        "initial_time": "1970-01-01T00:00:00+00:00",
        "time_step_seconds": 30
      }
    }
  },
  "version": "<DB_VERSION>"
}
```
"""


class EmptyDict(typing.TypedDict):
    pass


class HOTPParams(BaseModel):
    counter: int


class TOTPParams(BaseModel):
    initial_time: datetime.datetime
    time_step_seconds: int


OTPParams = typing.Union[HOTPParams, TOTPParams]


class StrEnum(str, enum.Enum):
    pass


class CaseInsensitiveStrEnum(StrEnum):
    @classmethod
    def _missing_(cls, value: typing.Any) -> CaseInsensitiveStrEnum | None:
        for member in cls:
            if member.value == str(value).upper():
                return member
        return None


class OTPType(CaseInsensitiveStrEnum):
    HOTP = "HOTP"
    TOTP = "TOTP"


class OTPAlgorithm(CaseInsensitiveStrEnum):
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA512 = "SHA512"


class AliasSchema(BaseModel):
    secret: str
    digits_count: int
    hash_algorithm: OTPAlgorithm
    otp_type: OTPType
    params: typing.Union[
        HOTPParams, TOTPParams
    ]  # Type depends on the value of `otp_type`, see the validator
    label: typing.Optional[str]
    issuer: typing.Optional[str]

    @validator("params")
    def valid_params_for_otp_type(cls, v, values):
        otp_type = values["otp_type"]
        required_param_type_by_otp_type = {
            OTPType.HOTP: HOTPParams,
            OTPType.TOTP: TOTPParams,
        }
        for key, value in required_param_type_by_otp_type.items():
            if otp_type == key and not isinstance(v, value):
                raise TypeError(f"{otp_type=} requires params of type {HOTPParams}")
        return v


class DatabaseSchema(BaseModel):
    otp: typing.Union[dict[str, AliasSchema], EmptyDict]
    version: str

    @validator("version")
    def supported_version(cls, v):
        if v not in settings.SUPPORTED_DB_VERSION:
            raise exceptions.DBUnsupportedVersion(v)
        return v

    @classmethod
    def initialize(cls) -> DatabaseSchema:
        return cls(otp=EmptyDict(), version=settings.DEFAULT_DB_VERSION)

    def add_alias(self, name: str, data: AliasSchema):
        self.otp[name] = data

    def add_totp_alias(
        self,
        name: str,
        label: str,
        issuer: str,
        secret: str,
        digits_count: int,
        hash_algorithm: OTPAlgorithm,
        initial_time: datetime.datetime,
        time_step_seconds: int = settings.DEFAULT_TIME_STEP_SECONDS,
    ):
        self.otp[name] = AliasSchema(
            secret=secret,
            label=label,
            issuer=issuer,
            digits_count=digits_count,
            hash_algorithm=hash_algorithm,
            otp_type=OTPType.TOTP,
            params=TOTPParams(
                initial_time=initial_time, time_step_seconds=time_step_seconds
            ),
        )

    def merge(self, other: DatabaseSchema):
        if other.version != self.version:
            raise exceptions.DBUnsupportedMigration(
                "Database version migration is currently not supported"
            )

        common_aliases = set(other.otp.keys()).intersection(self.otp.keys())
        if common_aliases:
            common_aliases_str = ", ".join(common_aliases)
            raise exceptions.DBMergeConflict(
                f"There are conflicting aliases between the current and imported database: {common_aliases_str}."
                " Consider renaming them in the current database, using `otp mv`, before the import."
            )

        self.otp |= other.otp


def get_params_by_type(
    type_: OTPType,
) -> typing.Type[HOTPParams] | typing.Type[TOTPParams]:
    return {OTPType.HOTP: HOTPParams, OTPType.TOTP: TOTPParams}[type_]


def create_alias_schema(
    otp_type: OTPType,
    label: str,
    issuer: str,
    secret: str,
    digits_count: int,
    hash_algorithm: str,
    params: OTPParams,
):
    return AliasSchema(
        otp_type=otp_type,
        label=label,
        issuer=issuer,
        secret=secret,
        digits_count=digits_count,
        hash_algorithm=hash_algorithm,
        params=params,
    )

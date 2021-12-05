from __future__ import annotations

import datetime
import enum
import typing

from pydantic import BaseModel
from pydantic import validator

from onetimepass import settings
from onetimepass.settings import DB_VERSION


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


class OTPType(str, enum.Enum):
    HOTP = "HOTP"
    TOTP = "TOTP"


class OTPAlgorithm(str, enum.Enum):
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"


class AliasSchema(BaseModel):
    secret: str
    digits_count: int
    hash_algorithm: OTPAlgorithm
    otp_type: OTPType
    params: typing.Union[
        HOTPParams, TOTPParams
    ]  # Type depends on the value of `otp_type`, see the validator

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

    @classmethod
    def initialize(cls) -> DatabaseSchema:
        return cls(otp=EmptyDict(), version=DB_VERSION)

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
        time_step_seconds: int = settings.DB_DEFAULT_TIME_STEP_SECONDS,
    ):
        self.otp[name] = AliasSchema(
            secret=secret,
            label=label,
            issuer=issuer,
            digits_count=digits_count,
            hash_algorithm=hash_algorithm,
            otp_type=OTPType.TOTP,
            params=TOTPParams(
                initial_time=initial_time, time_step_seconds=time_step_seconds,
            ),
        )


def get_params_by_type(
    typ: OTPType,
) -> typing.Type[HOTPParams] | typing.Type[TOTPParams]:
    return {OTPType.HOTP: HOTPParams, OTPType.TOTP: TOTPParams,}[typ]


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

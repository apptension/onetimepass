from __future__ import annotations

import datetime
import enum
import typing

from pydantic import BaseModel
from pydantic import validator

from onetimepass.settings import DEFAULT_DB_VERSION


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


class OTPType(str, enum.Enum):
    HOTP = "HOTP"
    TOTP = "TOTP"


class AliasSchema(BaseModel):
    secret: str
    digits_count: int
    hash_algorithm: str
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
        return cls(otp=EmptyDict(), version=DEFAULT_DB_VERSION)

    def add_totp_alias(
        self,
        name: str,
        secret: str,
        digits_count: int,
        hash_algorithm: str,
        initial_time: datetime.datetime,
        time_step_seconds: int = 30,
    ):
        self.otp[name] = AliasSchema(
            secret=secret,
            digits_count=digits_count,
            hash_algorithm=hash_algorithm,
            otp_type=OTPType.TOTP,
            params=TOTPParams(
                initial_time=initial_time, time_step_seconds=time_step_seconds,
            ),
        )

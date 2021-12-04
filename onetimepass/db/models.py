from __future__ import annotations

import typing

from pydantic import BaseModel

from onetimepass.settings import DB_VERSION


"""
Example database schema
{
  "otp": {},
  "version": "<DB_VERSION>",

  or

  "otp": {
    "keeper": {
      "secret": "",
      "digits_count": 0,
      "hash_algorithm": "",
      "params": {
        // hopt
        "counter": 0,

        // topt
        "initial_time": 0,
        "time_step_seconds": 30
      }
    }
  },
  "version": "<DB_VERSION>"
}
"""


class EmptyDict(typing.TypedDict):
    pass


class HOTPParams(BaseModel):
    counter: int


class TOTPParams(BaseModel):
    initial_time: int
    time_step_seconds: int


class AliasSchema(BaseModel):
    secret: str
    digits_count: int
    hash_algorithm: str
    params: typing.Union[HOTPParams, TOTPParams]


class DatabaseSchema(BaseModel):
    otp: typing.Union[dict[str, AliasSchema], EmptyDict]
    version: str

    @classmethod
    def initialize(cls) -> DatabaseSchema:
        return cls(otp=EmptyDict(), version=DB_VERSION)

    def add_totp_alias(
        self,
        name: str,
        secret: str,
        digits_count: int,
        hash_algorithm: str,
        initial_time: int,
        time_step_seconds: int = 30,
    ):
        self.otp[name] = AliasSchema(
            secret=secret,
            digits_count=digits_count,
            hash_algorithm=hash_algorithm,
            params=TOTPParams(
                initial_time=initial_time, time_step_seconds=time_step_seconds,
            ),
        )

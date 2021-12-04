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


class EmptyDict(BaseModel):
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
    otp: typing.Union[EmptyDict, AliasSchema]
    version: str

    @classmethod
    def initialize(cls) -> DatabaseSchema:
        return cls(otp=EmptyDict(), version=DB_VERSION)

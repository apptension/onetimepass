from __future__ import annotations
import typing

from pydantic import BaseModel

VERSION = "1.0.0"


"""
Example database schema
{
  "otp": {},
  "version": "1.0.0",

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
  "version": "1.0.0"
}
"""


class EmptyDict(BaseModel):
    pass


class HOTPSchema(BaseModel):
    counter: int


class TOTPDSchema(BaseModel):
    initial_time: int
    time_step_seconds: int


class AliasSchema(BaseModel):
    secret: str
    digits_count: int
    hash_algorithm: str
    params: typing.Union[HOTPSchema, TOTPDSchema]


class DatabaseSchema(BaseModel):
    otp: typing.Union[EmptyDict, AliasSchema]
    version: str

    @classmethod
    def initialize(cls) -> DatabaseSchema:
        return cls(
            otp=EmptyDict(),
            version=VERSION
        )

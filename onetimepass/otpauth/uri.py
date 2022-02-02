import urllib.parse
from typing import Union

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import ValidationError

from .errors import ParsingError
from .schemas import HOTPUriSchema
from .schemas import TOTPUriSchema


class Uri(BaseModel, extra=Extra.forbid):
    schema_: Union[HOTPUriSchema, TOTPUriSchema] = Field(..., discriminator="type")

    @property
    def type(self):
        return self.schema_.type

    @property
    def label(self):
        return self.schema_.label

    @property
    def parameters(self):
        return self.schema_.parameters

    @classmethod
    def parse(cls, uri: str) -> "Uri":
        # TODO extract to the separate module `parser.py`?
        parsed_uri = urllib.parse.urlparse(uri)
        type_ = parsed_uri.netloc
        label = parsed_uri.path.lstrip("/")
        try:
            parameters = dict(
                urllib.parse.parse_qsl(parsed_uri.query, strict_parsing=True)
            )
        except ValueError as e:
            raise ParsingError(e) from e

        try:
            return cls.parse_obj(
                {
                    "schema_": {
                        "scheme": parsed_uri.scheme,
                        "type": type_,
                        "urlencoded_label": label,
                        "parameters": parameters,
                    }
                }
            )
        except ValidationError as e:
            raise ParsingError(e) from e


def main():
    from rich.pretty import pprint

    # TODO reimplement as unit tests
    uri = "otpauth://hotp/Big%20Corporation%3A%20alice%40bigco.com?algorithm=SHA1&counter=0&secret=foo&secret=bar&issuer=Big%20Corporation"
    key_uri = Uri.parse(uri)
    pprint(key_uri)
    pprint(key_uri.dict())


if __name__ == "__main__":
    main()

import urllib.parse
from typing import Literal
from typing import Union

from pydantic import BaseModel
from pydantic import constr
from pydantic import Extra
from pydantic import validator

from .errors import InvalidURLScheme


class BaseUriParameters(BaseModel, extra=Extra.forbid):
    secret: str
    issuer: str | None
    algorithm: Literal["SHA1", "SHA256", "SHA512"] = "SHA1"
    digits: Literal[6, 8] = 6

    @validator("issuer")
    def issuer_must_match_pattern(cls, v):
        # As defined in
        # <https://github.com/google/google-authenticator/wiki/Key-Uri-Format#label>
        # > Neither issuer nor account name may themselves contain a colon
        #
        # As defined in
        # <https://github.com/google/google-authenticator/wiki/Key-Uri-Format#issuer>
        # > The issuer parameter is a string value […], URL-encoded according to
        # > RFC 3986

        # v_ = urllib.parse.quote(v, safe=":")
        # rule = rfc3986.Rule.create("issuer = segment-nz-nc")
        # try:
        #     rule.parse_all(v_)
        # except abnf.ParseError as e:
        #     raise ABNFParsingError(parsed_value=v, parse_error=e)
        # return v

        if ":" in v:
            raise ValueError("colon")
        return v


class HOTPUriParameters(BaseUriParameters):
    counter: int


class TOTPUriParameters(BaseUriParameters):
    period: int | None = 30


# def extract_parsed_value(node: abnf.Node, name: str) -> str | None:
#     """Do a breadth-first search of the tree for node identified by `name`.
#     If found, return its value.
#     """
#     # Based on the
#     # <https://github.com/declaresub/abnf#extract-the-actual-address-from-an-email-address>
#     queue = [node]
#     while queue:
#         n, queue = queue[0], queue[1:]
#         if n.name == name:
#             return n.value
#         else:
#             queue.extend(n.children)
#     return None


class LabelSchema(BaseModel, extra=Extra.forbid):
    accountname: constr(min_length=1)
    issuer: constr(min_length=1) | None

    @classmethod
    def parse(cls, urlencoded_label: str) -> "LabelSchema":
        # label = accountname / issuer (":" / "%3A") *"%20" accountname'
        decoded = urllib.parse.unquote(urlencoded_label)
        if (colon_count := decoded.count(":")) > 1:
            raise ValueError("colon")  # TODO
        elif colon_count == 1:
            issuer, accountname = decoded.split(":")
        else:
            issuer = None
            accountname = decoded

        return cls(accountname=accountname, issuer=issuer)

    @validator("accountname")
    def strip_leading_spaces(cls, v: str):
        return v.lstrip(" ")

    def __str__(self):
        if self.issuer is not None:
            return f"{self.issuer}: {self.accountname}"
        return self.accountname


class _BaseUriSchema(BaseModel, extra=Extra.forbid):
    scheme: str
    urlencoded_label: constr(min_length=1)
    label: LabelSchema = None
    parameters: Union[HOTPUriParameters, TOTPUriParameters]

    @validator("scheme")
    def scheme_must_be_otpauth(cls, v):
        if v != "otpauth":
            raise InvalidURLScheme(scheme=v)
        return v

    @validator("label", pre=True, always=True)
    def set_label(cls, v, values):
        return LabelSchema.parse(values["urlencoded_label"])

    @validator("parameters")
    def parameters_issuer_equals_label_issuer(
        cls, v: Union[HOTPUriParameters, TOTPUriParameters], values
    ):
        label: LabelSchema = values["label"]
        if v.issuer is not None and label.issuer != v.issuer:
            raise ValueError("issuer mismatch")
        return v

    # @validator("label")
    # def label_must_match_pattern(cls, v):
    #     # As defined in
    #     # <https://github.com/google/google-authenticator/wiki/Key-Uri-Format#label>
    #     # > It contains an account name, which is a URI-encoded string
    #     # and
    #     # > Neither issuer nor account name may themselves contain a colon
    #     #
    #     # As defined in
    #     # <https://github.com/google/google-authenticator/wiki/Key-Uri-Format#issuer>
    #     # > The issuer parameter is a string value […], URL-encoded according to
    #     # > RFC 3986
    #     rfc3986.Rule.create("accountname = segment-nz-nc")
    #     rfc3986.Rule.create("issuer = segment-nz-nc")
    #     rule = rfc3986.Rule.create(
    #         'label = accountname / issuer (":" / "%3A") *"%20" accountname'
    #     )
    #     try:
    #         rule.parse_all(v)
    #     except abnf.ParseError as e:
    #         raise ABNFParsingError(parsed_value=v, parse_error=e)
    #     return v

    # _url_decode_label = validator("label", allow_reuse=True)(url_decode)


class HOTPUriSchema(_BaseUriSchema):
    type: Literal["hotp"]
    parameters: HOTPUriParameters


class TOTPUriSchema(_BaseUriSchema):
    type: Literal["totp"]
    parameters: TOTPUriParameters

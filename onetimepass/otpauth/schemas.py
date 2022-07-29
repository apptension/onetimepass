import urllib.parse
from typing import Literal
from typing import Union

from pydantic import BaseModel
from pydantic import constr
from pydantic import Extra
from pydantic import validator

from .errors import IllegalColon
from .errors import InvalidURLScheme
from .errors import IssuerMismatch


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

        if ":" in v:
            raise IllegalColon
        return v


class HOTPUriParameters(BaseUriParameters):
    counter: int


class TOTPUriParameters(BaseUriParameters):
    period: int | None = 30


class LabelSchema(BaseModel, extra=Extra.forbid):
    accountname: constr(min_length=1)
    issuer: constr(min_length=1) | None

    @classmethod
    def parse(cls, urlencoded_label: str) -> "LabelSchema":
        # As defined in
        # <https://github.com/google/google-authenticator/wiki/Key-Uri-Format#label>
        # > Represented in ABNF according to RFC 5234:
        # > label = accountname / issuer (":" / "%3A") *"%20" accountname'
        # and
        # > Neither issuer nor account name may themselves contain a colon
        #
        # ---
        #
        # First approach to implement the parsing logic was to use the `abnf` library:
        # <https://pypi.org/project/abnf/>
        #
        # However, the above ABNF rule for `label` is more of a pseudorule, as
        # there's no explicit ABNF rule for neither `accountname` nor `issuer`,
        # which requires defining the custom rules for both.
        # That proved to be non-trivial, especially this part:
        # > Neither issuer nor account name may themselves contain a colon
        #
        # At some point, the implementation looked similar to:
        # ```
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
        # ```
        # Which was an incomplete solution, as the `segment-nz-nc` does _not_
        # exclude the URL-encoded colon, `%3A`.
        # We have tried to implement the custom rule instead, however, there
        # are limitations in defining exclusion for a fixed _string_ of
        # characters.
        #
        # The considered workaround was to URL-decode the label and only then
        # parse it using ABNF. However, such manual step would reduce the
        # convenience of using ABNF parser.
        #
        # In the end, it was decided that the fully manual solution (the
        # current one), not relying on ABNF parser at all, is much simpler and
        # straightforward to implement.
        decoded = urllib.parse.unquote(urlencoded_label)
        if (colon_count := decoded.count(":")) > 1:
            raise IllegalColon
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
        try:
            label: LabelSchema = values["label"]
        except KeyError:
            # `set_label` failed w/ the validation error, therefore `label` is
            # not available, and we cannot evaluate issuer equality
            return v
        if v.issuer is not None and label.issuer != v.issuer:
            raise IssuerMismatch(parameters_issuer=v.issuer, label_issuer=label.issuer)
        return v


class HOTPUriSchema(_BaseUriSchema):
    type: Literal["hotp"]
    parameters: HOTPUriParameters


class TOTPUriSchema(_BaseUriSchema):
    type: Literal["totp"]
    parameters: TOTPUriParameters

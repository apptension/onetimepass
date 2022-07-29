from pydantic import PydanticValueError


class ParsingError(Exception):
    pass


class InvalidURLScheme(PydanticValueError):
    code = "invalid_url_scheme"
    msg_template = "expected scheme 'otpauth', got: '{scheme}'"

    def __init__(self, *, scheme: str):
        super().__init__(scheme=scheme)


class IllegalColon(PydanticValueError):
    code = "illegal_colon"
    msg_template = "neither accountname nor issuer can contain a colon"


class IssuerMismatch(PydanticValueError):
    code = "issuer_mismatch"
    msg_template = "issuer mismatch, got: '{parameters_issuer}' != '{label_issuer}'"

    def __init__(self, *, parameters_issuer: str, label_issuer: str):
        super().__init__(parameters_issuer=parameters_issuer, label_issuer=label_issuer)

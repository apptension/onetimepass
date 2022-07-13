from pydantic import PydanticValueError


class ParsingError(Exception):
    pass


class InvalidURLScheme(PydanticValueError):
    code = "invalid_url_scheme"
    msg_template = "expected scheme 'otpauth', got: '{scheme}'"

    def __init__(self, *, scheme: str):
        super().__init__(scheme=scheme)

from pydantic import PydanticValueError


class ParsingError(Exception):
    pass


class InvalidURLScheme(PydanticValueError):
    code = "invalid_url_scheme"
    msg_template = "expected scheme 'otpauth', got: '{scheme}'"

    def __init__(self, *, scheme: str):
        super().__init__(scheme=scheme)


# class ABNFParsingError(PydanticValueError):
#     code = "abnf_parsing_error"
#     msg_template = "parsing error of ABNF rule at '{error_position}'"
#
#     def __init__(self, *, parsed_value: str, parse_error: abnf.ParseError):
#         super().__init__(
#             parsed_value=parsed_value,
#             parse_error=parse_error,
#             error_position=f"{parsed_value[parse_error.start:]}",
#         )

import datetime
import typing
import urllib.parse

from pydantic import BaseModel

from onetimepass import settings
from onetimepass.db.models import get_params_by_type
from onetimepass.db.models import HOTPParams
from onetimepass.db.models import OTPAlgorithm
from onetimepass.db.models import OTPType
from onetimepass.db.models import TOTPParams

SCHEMA = "otpauth"


class OTPAuthURI(BaseModel):
    otp_type: OTPType
    label: str
    issuer: str
    secret: str
    algorithm: OTPAlgorithm
    digits: int
    params: typing.Union[HOTPParams, TOTPParams]


def __get_query_string_value(
    parsed_query_string: dict[str, list[str]],
    param: str,
    default: typing.Optional[typing.Any] = None,
) -> str:
    try:
        return parsed_query_string.get(param, [default])[0]
    except (KeyError, TypeError):
        raise ValueError("Invalid schema")


def parse(uri: str) -> OTPAuthURI:
    uri_parsed = urllib.parse.urlparse(uri)
    if uri_parsed.scheme != SCHEMA:
        raise ValueError(f"Invalid schema got: {uri_parsed.scheme}, expected: {SCHEMA}")
    otp_type = OTPType(uri_parsed.netloc.upper())
    label = urllib.parse.unquote(uri_parsed.path.lstrip("/"))
    query_parsed = urllib.parse.parse_qs(uri_parsed.query)

    algorithm = OTPAlgorithm(query_parsed.get("algorithm")[0].lower())
    params = (
        {
            "initial_time": datetime.datetime.fromtimestamp(
                0, tz=datetime.timezone.utc
            ),
            "time_step_seconds": __get_query_string_value(
                query_parsed, "period", settings.DEFAULT_TIME_STEP_SECONDS
            ),
        }
        if otp_type == OTPType.TOTP
        else {"counter": __get_query_string_value(query_parsed, "counter"),}
    )
    return OTPAuthURI(
        otp_type=otp_type,
        label=label,
        algorithm=algorithm,
        secret=__get_query_string_value(query_parsed, "secret"),
        issuer=__get_query_string_value(query_parsed, "issuer"),
        digits=__get_query_string_value(
            query_parsed, "digits", settings.DEFAULT_DIGITS_COUNT
        ),
        params=get_params_by_type(otp_type)(**params),
    )

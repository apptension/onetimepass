import dataclasses
import datetime
import hmac


def _get_hmac_result(key: bytes, msg: bytes, hash_algorithm: str) -> bytes:
    return hmac.digest(key, msg, hash_algorithm)


def _dynamic_truncation(hmac_result: bytes) -> int:
    offset = hmac_result[-1] & 0xF
    bin_code = (
        (hmac_result[offset] & 0x7F) << 24
        | (hmac_result[offset + 1] & 0xFF) << 16
        | (hmac_result[offset + 2] & 0xFF) << 8
        | (hmac_result[offset + 3] & 0xFF)
    )
    return bin_code


def _truncate(hmac_result: bytes, digits_count: int) -> int:
    return _dynamic_truncation(hmac_result) % 10 ** digits_count


def _counter_to_bytes(counter: int) -> bytes:
    # As defined in https://tools.ietf.org/html/rfc4226#section-5.1,
    # counter (symbol C) is a _8_-byte value.
    counter_length = 8
    return counter.to_bytes(counter_length, "big")


def _tz_aware_utcnow() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


@dataclasses.dataclass
class BaseOTPParameters:
    secret: bytes
    digits_count: int
    hash_algorithm: str


@dataclasses.dataclass
class HOTPParameters(BaseOTPParameters):
    counter: int


@dataclasses.dataclass
class TOTPParameters(BaseOTPParameters):
    initial_time: datetime.datetime = datetime.datetime.fromtimestamp(
        0, tz=datetime.timezone.utc
    )
    time_step_seconds: int = 30
    current_time: datetime.datetime = dataclasses.field(
        default_factory=_tz_aware_utcnow
    )

    def to_hotp_parameters(self) -> HOTPParameters:
        # TOTP is just a HOTP where counter is time-based
        time_counter = int(
            (self.current_time.timestamp() - self.initial_time.timestamp())
            / self.time_step_seconds
        )
        return HOTPParameters(
            secret=self.secret,
            digits_count=self.digits_count,
            hash_algorithm=self.hash_algorithm,
            counter=time_counter,
        )


def hotp(parameters: HOTPParameters) -> int:
    """HMAC-Based One-Time Password

    As defined in https://tools.ietf.org/html/rfc4226.
    """
    hmac_result = _get_hmac_result(
        parameters.secret,
        _counter_to_bytes(parameters.counter),
        parameters.hash_algorithm,
    )
    return _truncate(hmac_result, parameters.digits_count)


def totp(parameters: TOTPParameters) -> int:
    """Time-Based One-Time Password

    As defined in https://tools.ietf.org/html/rfc6238.
    """
    return hotp(parameters.to_hotp_parameters())

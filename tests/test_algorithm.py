from __future__ import annotations

import dataclasses
import datetime
import hashlib
import itertools
import unittest

from onetimepass import algorithm


def get_secret(hash_algorithm: str) -> bytes:
    """Generate a secret based on specified hash algorithm

    <https://tools.ietf.org/html/rfc6238#appendix-B> specifies that every test
    vector uses the secret "12345678901234567890", but that is not true (it is
    impossible to reproduce the specified TOTP values).

    The reference implementation in
    <https://tools.ietf.org/html/rfc6238#page-13> suggests, that every hash
    algorithm should have the secret with appropriate length:
    - HMAC-SHA1 generates 20-bytes value, and the defined secret (or seed) is
      also 20-bytes;
    - HMAC-SHA256 generates 32-bytes value, and the defined secret (or seed) is
      also 32-bytes;
    etc.

    The <https://crypto.stackexchange.com/a/27499> seems to confirm that.
    """
    base = "1234567890"
    length = hashlib.new(hash_algorithm).digest_size
    return "".join(itertools.islice(itertools.cycle(base), length)).encode()


class TestHOTP(unittest.TestCase):
    def test_hotp(self):
        # Based on https://tools.ietf.org/html/rfc4226#page-32
        counter_start = 0
        expected_hotps = [
            755224,
            287082,
            359152,
            969429,
            338314,
            254676,
            287922,
            162583,
            399871,
            520489,
        ]
        for counter, expected_hotp in enumerate(expected_hotps, start=counter_start):
            with self.subTest(i=counter):
                hotp = algorithm.hotp(
                    algorithm.HOTPParameters(
                        secret=get_secret("sha1"),
                        digits_count=6,
                        hash_algorithm="sha1",
                        counter=counter,
                    )
                )
                self.assertEqual(hotp, expected_hotp)


class TestTOTP(unittest.TestCase):
    # Based on https://tools.ietf.org/html/rfc6238#appendix-B

    @dataclasses.dataclass
    class TestTOTPParameters(algorithm.TOTPParameters):
        secret: bytes = dataclasses.field(init=False)
        digits_count: int = 8
        hash_algorithm: str = "sha1"

        def __post_init__(self):
            self.secret = get_secret(self.hash_algorithm)

    @dataclasses.dataclass
    class TestVector:
        parameters: TestTOTPParameters
        expected_counter: int
        expected_totp: int

    test_vectors = [
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    1970, 1, 1, 0, 0, 59, tzinfo=datetime.timezone.utc
                )
            ),
            expected_counter=int("1", 16),
            expected_totp=94287082,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    1970, 1, 1, 0, 0, 59, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha256",
            ),
            expected_counter=int("1", 16),
            expected_totp=46119246,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    1970, 1, 1, 0, 0, 59, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha512",
            ),
            expected_counter=int("1", 16),
            expected_totp=90693936,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2005, 3, 18, 1, 58, 29, tzinfo=datetime.timezone.utc
                )
            ),
            expected_counter=int("23523EC", 16),
            expected_totp=7081804,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2005, 3, 18, 1, 58, 29, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha256",
            ),
            expected_counter=int("23523EC", 16),
            expected_totp=68084774,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2005, 3, 18, 1, 58, 29, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha512",
            ),
            expected_counter=int("23523EC", 16),
            expected_totp=25091201,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2009, 2, 13, 23, 31, 30, tzinfo=datetime.timezone.utc
                )
            ),
            expected_counter=int("273EF07", 16),
            expected_totp=89005924,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2009, 2, 13, 23, 31, 30, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha256",
            ),
            expected_counter=int("273EF07", 16),
            expected_totp=91819424,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2009, 2, 13, 23, 31, 30, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha512",
            ),
            expected_counter=int("273EF07", 16),
            expected_totp=93441116,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2033, 5, 18, 3, 33, 20, tzinfo=datetime.timezone.utc
                )
            ),
            expected_counter=int("3F940AA", 16),
            expected_totp=69279037,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2033, 5, 18, 3, 33, 20, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha256",
            ),
            expected_counter=int("3F940AA", 16),
            expected_totp=90698825,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2033, 5, 18, 3, 33, 20, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha512",
            ),
            expected_counter=int("3F940AA", 16),
            expected_totp=38618901,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2603, 10, 11, 11, 33, 20, tzinfo=datetime.timezone.utc
                )
            ),
            expected_counter=int("27BC86AA", 16),
            expected_totp=65353130,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2603, 10, 11, 11, 33, 20, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha256",
            ),
            expected_counter=int("27BC86AA", 16),
            expected_totp=77737706,
        ),
        TestVector(
            parameters=TestTOTPParameters(
                current_time=datetime.datetime(
                    2603, 10, 11, 11, 33, 20, tzinfo=datetime.timezone.utc
                ),
                hash_algorithm="sha512",
            ),
            expected_counter=int("27BC86AA", 16),
            expected_totp=47863826,
        ),
    ]

    def test_to_hotp_parameters(self):
        for test_vector in self.test_vectors:
            with self.subTest(i=test_vector.parameters.current_time):
                counter = test_vector.parameters.to_hotp_parameters().counter
                self.assertEqual(counter, test_vector.expected_counter)

    def test_totp(self):
        for test_vector in self.test_vectors:
            with self.subTest(i=test_vector.parameters.current_time):
                totp = algorithm.totp(test_vector.parameters)
                self.assertEqual(totp, test_vector.expected_totp)

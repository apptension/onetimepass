import base64
import functools

# > Optional casefold is a flag specifying whether a lowercase alphabet is
# > acceptable as input. For security purposes, the default is False.
# > —https://docs.python.org/3/library/base64.html#base64.b32decode
#
# We prefer to avoid using something that is disabled by default for security
# purposes, but some services, unfortunately, provide the secret in lowercase
# (e.g. Google!), so not doing that would make the application not working for
# those.
#
# The reason that they provide the secret in lowercase may come from the
# official spec being ambiguous:
#
# > The Base 32 encoding is designed to represent arbitrary sequences of octets
# > in a form that needs to be **case insensitive**
# > […]
# > These characters […] are selected from US-ASCII digits and **uppercase letters**.
# > —https://datatracker.ietf.org/doc/html/rfc3548#section-5
#
# It mentions using uppercase letters, but also the value being case-insensitive.
# The reason is just a guess, though
decode = functools.partial(base64.b32decode, casefold=True)

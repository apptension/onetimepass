"""A whitelist for `vulture` (dead code detector)

Generated via
```
$ vulture --make-whitelist >whitelist.py
```

See:
https://github.com/jendrikseipp/vulture/tree/v2.11?tab=readme-ov-file#whitelists
"""

valid_base32_secret  # unused function (onetimepass/db/models.py:80)
valid_params_for_otp_type  # unused function (onetimepass/db/models.py:88)
supported_version  # unused function (onetimepass/db/models.py:105)
_._missing_  # unused method (onetimepass/enum.py:12)
SHA256  # unused variable (onetimepass/enum.py:27)
SHA512  # unused variable (onetimepass/enum.py:28)
show  # unused function (onetimepass/otp.py:146)
init  # unused function (onetimepass/otp.py:220)
passwd  # unused function (onetimepass/otp.py:246)
delete  # unused function (onetimepass/otp.py:261)
list_  # unused function (onetimepass/otp.py:281)
export  # unused function (onetimepass/otp.py:302)
import_  # unused function (onetimepass/otp.py:316)
add_uri  # unused function (onetimepass/otp.py:351)
add_hotp  # unused function (onetimepass/otp.py:427)
add_totp  # unused function (onetimepass/otp.py:479)
rename  # unused function (onetimepass/otp.py:539)
msg_template  # unused variable (onetimepass/otpauth/errors.py:10)
msg_template  # unused variable (onetimepass/otpauth/errors.py:18)
msg_template  # unused variable (onetimepass/otpauth/errors.py:23)
issuer_must_match_pattern  # unused function (onetimepass/otpauth/schemas.py:24)
strip_leading_spaces  # unused function (onetimepass/otpauth/schemas.py:109)
scheme_must_be_otpauth  # unused function (onetimepass/otpauth/schemas.py:125)
set_label  # unused function (onetimepass/otpauth/schemas.py:131)
parameters_issuer_equals_label_issuer  # unused function (onetimepass/otpauth/schemas.py:135)

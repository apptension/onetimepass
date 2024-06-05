# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning's recommendation in regard to
initial development
phase](https://semver.org/spec/v2.0.0.html#how-should-i-deal-with-revisions-in-the-0yz-initial-development-phase).

<!--
Types of changes:
- Added for new features.
- Changed for changes in existing functionality.
- Deprecated for soon-to-be removed features.
- Removed for now removed features.
- Fixed for any bug fixes.
- Security in case of vulnerabilities.
-->

## [0.2.0] - 2024-06-05

### Added

- Documentation of the project's roadmap (PR [#50], [#70]).
- Command to echo database version and file path (issue [#32], PR [#67]).
- Command to echo the application's version (issue [#71], PR [#72]).
- Option `--debug/--no-debug`, which allows to enable or disable debug info (PR [#82]).
- Documentation of the project's version history AKA this changelog (PR [#83]).

[#32]: https://github.com/apptension/onetimepass/issues/32
[#50]: https://github.com/apptension/onetimepass/pull/50
[#67]: https://github.com/apptension/onetimepass/pull/67
[#70]: https://github.com/apptension/onetimepass/pull/70
[#71]: https://github.com/apptension/onetimepass/issues/71
[#72]: https://github.com/apptension/onetimepass/pull/72
[#82]: https://github.com/apptension/onetimepass/pull/82
[#83]: https://github.com/apptension/onetimepass/pull/83

### Changed

- The `black` pre-commit hook to the official faster mirror (PR [#73]).

[#73]: https://github.com/apptension/onetimepass/pull/73

### Removed

- Command `show-all` (issue [#27], PR [#40]).

[#27]: https://github.com/apptension/onetimepass/issues/27
[#40]: https://github.com/apptension/onetimepass/pull/40

### Fixed

- The app always reads/writes the database in the current directory. Now, the
  app stores a local database in the OS-specific data directory (issue [#26], PR
  [#31]).
- The counter in HOTP is incremented _after_ the OTP is shown. Now, it is
  correctly incremented _before_ the OTP is shown (issue [#39], PR [#41]).
- Command `add hotp` raises unhandled exception on missing option `-c,
  --counter`. Now, the option defaults to value `0` (issue [#33], PR [#42]).
- The app does not store parameters `label` and `issuer`. Now, it stores them
  (issue [#34], PR [#44]).
- Invalid type annotation of option `wait` (PR [#45]).
- Error message for invalid hash algorithm shows the implementation details.
  Now, it shows the possible values expected from the user (issue [#46], PR [#48]).
- Command `otp -k key` raises unhandled exception if the keyring is not
  installed. Now, it shows an appropriate error message (issue [#56], PR [#57]).
- Command `add uri` does not conform in 100% to the Key Uri Format
  specification: parameter `secret` is handled as plain text, not Base32; some
  parameters that are supposed to be optional according to the spec, are
  required by the application. Now, it conforms (issue [#37], PR [#58]).
- Redundant re-input of database password. Now, it is removed (PR [#58]).
- When entered manually (not as a part of the Key URI), parameter `secret` is
  handled as-is, not interpreted as the Base32. Now, it is interpreted as the
  Base32 (issue [#38], PR [#65]).
- Shadowed variable `algorithm`. Now, it is renamed, along with several other
  variables named `*algorithm` (issue [#47], PR [#68]).
- Regression after renaming `*algorithm` variables (issue [#75], PR [#76]).
- Parameter `digits` in Key URI not being optional. Now, it is optional (issue
  [#77], PR [#78]).
- Parameter `secret` not being case-insensitive. Now, it is case-insensitive
  (issue [#80], PR [#81]).
- CI/CD after periodic breakdowns (issue [#51], [#61]; PR [#52], [#62], [#66]).

[#26]: https://github.com/apptension/onetimepass/issues/26
[#31]: https://github.com/apptension/onetimepass/pull/31
[#33]: https://github.com/apptension/onetimepass/issues/33
[#34]: https://github.com/apptension/onetimepass/issues/34
[#37]: https://github.com/apptension/onetimepass/issues/37
[#38]: https://github.com/apptension/onetimepass/issues/38
[#39]: https://github.com/apptension/onetimepass/issues/39
[#41]: https://github.com/apptension/onetimepass/pull/41
[#42]: https://github.com/apptension/onetimepass/pull/42
[#44]: https://github.com/apptension/onetimepass/pull/44
[#45]: https://github.com/apptension/onetimepass/pull/45
[#46]: https://github.com/apptension/onetimepass/issues/46
[#47]: https://github.com/apptension/onetimepass/issues/47
[#48]: https://github.com/apptension/onetimepass/pull/48
[#51]: https://github.com/apptension/onetimepass/issues/51
[#52]: https://github.com/apptension/onetimepass/pull/52
[#56]: https://github.com/apptension/onetimepass/issues/56
[#57]: https://github.com/apptension/onetimepass/pull/57
[#58]: https://github.com/apptension/onetimepass/pull/58
[#61]: https://github.com/apptension/onetimepass/issues/61
[#62]: https://github.com/apptension/onetimepass/pull/62
[#65]: https://github.com/apptension/onetimepass/pull/65
[#66]: https://github.com/apptension/onetimepass/pull/66
[#68]: https://github.com/apptension/onetimepass/pull/68
[#75]: https://github.com/apptension/onetimepass/issues/75
[#76]: https://github.com/apptension/onetimepass/pull/76
[#77]: https://github.com/apptension/onetimepass/issues/77
[#78]: https://github.com/apptension/onetimepass/pull/78
[#80]: https://github.com/apptension/onetimepass/issues/80
[#81]: https://github.com/apptension/onetimepass/pull/81

## [0.1.0] - 2021-12-06

### Added

- All the basic commands
- All the nice-to-have commands

[unreleased]: https://github.com/apptension/onetimepass/compare/0.1.0...HEAD
[0.1.0]: https://github.com/apptension/onetimepass/releases/tag/0.1.0

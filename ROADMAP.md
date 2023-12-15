# Roadmap

## 0.1.0

Initial release after the hackathon

- [x] All the basic commands
- [x] All the nice-to-have commands

## 0.2.0

- [x] Fix all the critical bugs

Optionally:
- [x] Add command to echo db version and path
- [ ] Add `otp --version` option to echo the application's version (if not here,
  then a must in one of later versions)

## 0.3.0

Code quality release

- [ ] Add flake8 + plugins (see
      <https://github.com/psf/black/blob/main/.pre-commit-config.yaml>)
- [ ] Add mypy or other type checker
- [ ] Add more pre-commit hooks AKA Fix [#28][]
- [ ] Fix [#60][]

Optionally:
- [ ] Add tool to find unused code (vulture?)
- [ ] Add tool to audit security. Candidates:
    - <https://pycharm-security.readthedocs.io/en/latest/github.html>
    - <https://bandit.readthedocs.io/en/latest/>
    - <https://github.com/features/security>
    - <https://snyk.io/>
    - <https://aquasecurity.github.io/trivy/v0.32/>
- [ ] Add [pyroma][]

[#28]: https://github.com/apptension/onetimepass/issues/28
[#60]: https://github.com/apptension/onetimepass/issues/60
[pyroma]: https://pypi.org/project/pyroma/

## 0.4.0

Unit tests release

See [#30][]

Part of 0.3.0 instead?

- [ ] Add unit tests (possibly full coverage)
- [ ] Add coverage checker to the CI/CD
- [ ] Add per platform testing (Linux, macOS, Windows)

[#30]: https://github.com/apptension/onetimepass/issues/30

## 0.5.0

Better docs release

May be swapped in order with **Publish package release**

- [ ] Fix [#29][]
- [ ] Fix [#55][]
- [ ] Fix [#59][]
- [ ] Consider the general rewrite

[#29]: https://github.com/apptension/onetimepass/issues/29
[#55]: https://github.com/apptension/onetimepass/issues/55
[#59]: https://github.com/apptension/onetimepass/issues/59

## 0.6.0

Publish package release

May be swapped in order with **Better docs release**

- [ ] Publish automatically on tag to PyPI AKA Fix [#35][]
- [ ] Implement PKGBUILD for Arch Linux (see
      <https://wiki.archlinux.org/title/Python_package_guidelines>)
- [ ] Implement Homebrew formula for macOS
- [ ] Zipapp or similar for Windows (research required)
- [ ] Document how to install the app on the mobile phone AKA Fix [#36][]

[#35]: https://github.com/apptension/onetimepass/issues/35
[#36]: https://github.com/apptension/onetimepass/issues/36

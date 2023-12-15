# Roadmap

## 0.1.0

Initial release after the hackathon

- [x] All the basic commands
- [x] All the nice-to-have commands

## 0.2.0

Fixes all the critical bugs

Optionally:
- [x] Add command to echo db version and path

## 0.3.0

Code quality release

- [ ] Add flake8 + plugins (see <https://github.com/psf/black/blob/main/.pre-commit-config.yaml>)
- [ ] Add mypy or other type checker
- [ ] Add more pre-commit hooks
- [ ] Tool to find unused code (vulture?)

Optionally:
- [ ] Tool to audit security. Candidates:
    - <https://pycharm-security.readthedocs.io/en/latest/github.html>

## 0.4.0

Unit tests release

Part of 0.3.0 instead?

- [ ] Unit tests
- [ ] coverage tool
- [ ] Per platform testing (Linux, macOS, Windows)

## 0.?.0

Publish package release

- [ ] Publish automatically on tag to PyPI
- [ ] Implement PKGBUILD for Arch Linux (see <https://wiki.archlinux.org/title/Python_package_guidelines>)
- [ ] Implement Homebrew formula for macOS
- [ ] Zipapp or similar for Windows (research required)

# One Time Password (OTP, TOTP/HOTP)

[![Python 3.10](https://img.shields.io/badge/python-3.10.0-green.svg)](https://www.python.org/downloads/release/python-3100/)

---
OTP serves as additional protection in case of password leaks.
Onetimepassword allows you to manage OTP codes and generate a master key.
The master key allows the base to be decrypted and encrypted. Make sure to keep it in a safe place, otherwise it will not be possible to recover the data.
Onetimepassword supports as an additional dependency the integration with the system keychain (cross-platform) in which the application saves the master key

## Requirements

Python 3.10.0+

PDM 1.11+

## Installation

```console
$ pdm install
```

or with keyring support:
```console
$ pdm install -G keyring
```



## Usage

### Initialize database

At the very beginning, the database must be initialised, which additionally creates the master key.
It will save it to the keychain if this has been installed.

```console
pdm run otp init
```

### Adding new OTP alias

Onetimepassword allows you to add OTP codes using aliases in two ways. Via URI and via two dedicated commands which add an alias for TOTP and HOTP.

#### Adding via URI:
```console
pdm run otp add uri AWS-root
```

Example URIs:

* TOTP: [otpauth://totp/ACME%20Co:john@example.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30]()
* HOTP: [otpauth://totp/ACME%20Co:john@example.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30]()

#### Adding via totp/hotp subcommand (command will ask for secret):
```console
pdm run otp add totp AWS-root
pdm run otp add hotp AWS-root
```

### Removing OTP alias

```console
pdm run otp rm <alias>
```

Deletion requires additional confirmation

### Showing OTP code

Show single OTP by alias

```console
pdm run otp show <alias>
```

![Alt text](docs/show-alias.png?raw=true)

Show single OTP code by alias and wait for code valid at least X seconds

```console
pdm run otp show -m -w X <alias>
```

![Alt text](docs/show-alias-wait.png?raw=true)

The value returned by the command can be used to copy it straight to the clipboard or be otherwise automated.

Show all codes (using external watcher):
```console
watch -c -p -n 1 pdm run otp show-all
```

![Alt text](https://j.gifs.com/oZ6kPz.gif "Showing all codes with watcher")

### Shell Completion

Onetimepassword can provide tab completion for commands, options, and choice values. Bash, Zsh, and Fish are supported

```console
$ pdm run zsh
$ eval "$(_OTP_COMPLETE=zsh_source otp)"
```

![Alt text](docs/otp-shell-completion.png?raw=true "Shell Completion")

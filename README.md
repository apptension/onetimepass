# One Time Password (OTP, TOTP/HOTP)

[![Python 3.10](https://img.shields.io/badge/python-3.10-green.svg)](https://www.python.org/downloads/release/python-3100/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

---
OTP serves as additional protection in case of password leaks.

`onetimepass` allows you to manage OTP codes and generate a master key.
The master key allows the base to be decrypted and encrypted. Make sure to keep it in a safe place, otherwise it will
not be possible to recover the data.

`onetimepass` supports as an optional dependency the integration with the system keychain (cross-platform) in which the
application saves the master key.

## Requirements

- Python 3.10+
- PDM 1.11+

## Installation

```console
$ pdm install
```

To include the optional keychain support:
```console
$ pdm install -G keyring
```

## Usage

![](docs/usage.png)

### Initialize database

At the very beginning, the database must be initialised, which additionally creates the master key.
It will save it to the keychain if this has been installed.

By default, it will print the generated key to the STDOUT. You need this behavior if you don't use the optional keychain
integration.

If you do, you can pass the `-q, --quiet` option to silence the output.

![](docs/master-key-init.png)

### Keychain integration

The application will automatically detect if you have the keychain integration installed, however, if you want to force
enable/disable it, you can by using respectively the `-k, --keyring` and `-K, --no-keyring` options.

Although, if you don't have the keychain integration installed, enabling it won't work:
![](docs/keyring-not-installed.png)


### Print the master key

It is possible to print the current master key stored in the keychain (if you need this for e.g. migrating the app to
the different device).

This of course won't work if you don't use the keychain integration.

![](docs/master-key-show.png)

### Adding new OTP alias

`onetimepass` identifies the added OTP codes via the user-specified _aliases_, which should be short, easy-to-remember
names.

`onetimepass` allows you to add new alias in two ways, either by specifying all the parameters manually,
using `add hotp` or `add totp` commands (depending on which type of the OTP you want to add), or by providing
the [de facto standard URI](https://github.com/google/google-authenticator/wiki/Key-Uri-Format) invented by the Google.

#### Adding via URI (command will aks interactively for the URI)
```console
$ pdm run otp add uri AWS-root
Enter URI:
Repeat for confirmation:
```

Example URIs

* TOTP: [otpauth://totp/ACME%20Co:john@example.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30]()
* HOTP: [otpauth://totp/ACME%20Co:john@example.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30]()

#### Adding via totp/hotp subcommand (command will ask interactively for the secret):
```console
$ pdm run otp add totp AWS-root
Enter secret:
Repeat for confirmation:
$ pdm run otp add hotp AWS-root
Enter secret:
Repeat for confirmation:
```

### Removing OTP alias

```console
$ pdm run otp rm <alias>
Are you sure? [y/N]:
```

To omit the interactive confirmation (⚠️ **unsafe!**), pas the `--yes` option.

### Showing OTP code

#### Show single OTP identified by alias

```console
$ pdm run otp show <alias>
```

![](docs/show-alias.png)

You can force the app to wait until the new OTP code is valid, in case the current one will be invalid in a short period
of time (so you won't have to rush with copy-pasting the code, or wait manually), using `-w, --wait-for-next` option.

```console
$ pdm run otp show -w <seconds> <alias>
```

This will accept the _seconds_ of tolerance (if the remaining time of the current code to be valid is less than
_seconds_, the app will wait, otherwise it will show the current code).

![](docs/wait-for-next-otp.gif)

You can easily automate it even more:

```console
$ pdm run otp show -w 10 <alias> | cut -d' ' -f2 | pbcopy; alert
```

To extract the code when it's ready, then copy it to the system clipboard (`pbcopy` for macOS, `xclip` for Linux), and
send the system notification to yourself when it's all finished (assuming you have the `alert` alias configured,
available by default e.g. on Ubuntu Linux).

#### Show all codes

```console
$ pdm run otp show-all
```

You can emulate the view known from the Google Authenticator (list of all the codes, refreshed dynamically) by wrapping
the application in the external watcher (e.g. `watch`):
```console
$ watch -c -p -n 1 pdm run otp show-all
```

![](docs/watch-show-all.gif)

### Database import/export

In case you want to migrate the application to the different device, you can export the local database to the format of
choice (currently only the `json` is supported) and then import it.

![](docs/database-import.png)

![](docs/database-import-conflict.png)

You can use this not only to transfer the application between the devices, but also to create backups:
because `onetimepass` is a CLI-based tool, you can even implement the cronjob that will periodically run the `export` in
the background (⚠️ just remember to encrypt the resulting file and store it somewhere safe).

### Shell Completion

`onetimepass` can provide tab completion for commands, options, and choice values. Bash, Zsh, and Fish are supported

```console
$ pdm run zsh
$ eval "$(_OTP_COMPLETE=zsh_source otp)"
```

```console
$ pdm run bash
$ eval "$(_OTP_COMPLETE=bash_source otp)"
```

![](docs/otp-shell-completion.png)

## Rationale

As the `onetimepass` have multiple alternatives, you may ask why bother with reinventing the wheel instead of using any
existing solution.  
This section addresses that.

### Existing alternatives

#### [Google Authenticator](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)

The main issue with this app is that it does not offer any way to backup the secrets, and synchronize them between the
devices.

If you don't have the backup of the original QR codes, and you'll lose your mobile phone, you're screwed. Yes, services
that provide the 2FA often offer the backup codes, but not every one of them, and this is not the optimal solution.

In theory, if you root the device, you can access the local database, but not everyone wants or can root their mobile
phone, as this can e.g. void a device's warranty.

Besides, if you root the device, you can see the local database is stored in the plain text, which is a big security
risk.

#### [Authy](https://authy.com/)

It does allow synchronizing secrets between the devices, but this happens through the provider servers. The
application [neither sent nor store your backup password](https://support.authy.com/hc/en-us/articles/115001750008-Backups-and-Sync-in-Authy), but
it can still be non-optimal for some people to trust the external provider to handle such sensitive data.

Also, Authy
[does not support export or import](https://support.authy.com/hc/en-us/articles/1260805179070-Export-or-Import-Tokens-in-the-Authy-app)
of the secrets.

#### [pass](https://www.passwordstore.org/) or [gopass](https://www.gopass.pw/)

`pass` is an extensible CLI-based password manager, and there is a [pass-otp](https://github.com/tadfisher/pass-otp)
plugin to handle TOTP (although, HOTP is not supported).

One issue is that it uses GnuPG for encrypting the local database, which can be tedious to configure:
> To be honest, a few first times I tried to configure it, I failed miserably. This should be much easier and faster.
~ [Daniel Staśczak](https://github.com/Toreno96)

The second issue is that, as mentioned above, `pass` is _primarily_ the password manager.
If one wants only the TOTP client, it's a little bit of an overkill to install the whole password manager for that.

### The GUI clients in general

This is more of a personal preference, but if you use the GUI-based OTP client, especially on your mobile phone, there
are some extra steps everytime you need to use it:
1. You have to get your phone.
2. You have to open the app.
3. You have to type the code manually, if you need to enter the code on another device (e.g. to authorize on the
   desktop).

This is _not_ very inconvenient, but I bet there were at least few times when you didn't had your phone with you while
you had to authorize into the AWS account while working on something urgent, or get your phone out of the pocket every
few hours, because the Keeper logged out you out of a sudden once again in a day.

If you're CLI power-user, using the CLI-based tool is just much quicker and convenient. And you can create some crazy
pipelines (see the examples in the **Usage** section).

### Security

While `onetimepass` does reinvent a wheel in general, one of the main goals of the project is to still be a secure
solution, and do _not_ reinvent the wheel in regard to the security. Because of this reason, for generating the master
key and encrypting the local database, the [high-level cryptographic library](https://cryptography.io/en/latest/) is
used.

The main algorithm for the HOTP/TOTP is implemented based on the official RFC and the reference implementation.

There are some functionalities which can be a security hole if used in an irresponsible manner (e.g. `export`, `key`),
but the same can be said about the `sudo rm -rf --np-preserve-root /`, right?

Nevertheless, if you see any security issue, please feel free to report it, we're more than happy to consider it.

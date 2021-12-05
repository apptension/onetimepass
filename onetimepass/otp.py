import datetime
import enum
import functools
import pathlib
import secrets
from typing import Dict

import click

from onetimepass import algorithm
from onetimepass import settings
from onetimepass.db import BaseDB
from onetimepass.db import DatabaseSchema
from onetimepass.db import DBDoesNotExist
from onetimepass.db import JSONEncryptedDB
from onetimepass.exceptions import UnhandledFormatException


def get_db_data(db: BaseDB) -> DatabaseSchema:
    try:
        return db.read()
    except DBDoesNotExist:
        raise click.UsageError(
            "Database does not exist. Try to initialize it first `opt init`"
        )


try:
    import keyring  # noqa 'keyring' in the try block with 'except ImportError' should also be defined in the except block
except ImportError:
    KEYRING_INSTALLED = False
else:
    KEYRING_INSTALLED = True
    KEYRING_PARAMS = {
        "service_name": settings.KEYRING_SERVICE_NAME,
        "username": settings.KEYRING_USERNAME,
    }
    keyring_set = functools.partial(keyring.set_password, **KEYRING_PARAMS)
    keyring_get = functools.partial(keyring.get_password, **KEYRING_PARAMS)


def echo_alias(alias: str, code: int, seconds_remaining: int, color: bool):
    seconds_remaining_str = f"{seconds_remaining:0>2}s"
    if color:
        if seconds_remaining <= 10:
            seconds_remaining_str = click.style(
                seconds_remaining_str, fg="red", bold=True
            )
    click.echo(f"{alias}: {code} {seconds_remaining_str}")


def handle_conflicting_options(options: Dict[str, bool]):
    conflicting_options = {k: v for k, v in options.items() if v}
    if len(conflicting_options) > 1:
        options_list = "; ".join([str(k) for k in conflicting_options])
        raise click.UsageError(f"conflicting options: {options_list}")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("color", "-c/-C", "--color/--no-color", default=True, show_default=True)
@click.option("quiet", "-q", "--quiet", is_flag=True)
@click.option(
    "keyring_",
    "-k/-K",
    "--keyring/--no-keyring",
    default=KEYRING_INSTALLED,
    show_default="True if keyring installed, False otherwise",
)
@click.pass_context
def otp(ctx: click.Context, color: bool, quiet: bool, keyring_: bool):
    ctx.ensure_object(dict)
    ctx.obj.update({"color": color, "quiet": quiet, "keyring_": keyring_})


@otp.command(help="Print the one-time password for the specified ALIAS.")
@click.argument("alias")
@click.pass_context
def show(ctx: click.Context, alias: str):
    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = db.read()
    try:
        alias_data = data.otp[alias]
    except KeyError:
        raise click.UsageError(f"Alias: {alias} does not exist")
    params = algorithm.TOTPParameters(
        secret=alias_data.secret.encode(),
        digits_count=alias_data.digits_count,
        hash_algorithm=alias_data.hash_algorithm,
        time_step_seconds=alias_data.params.time_step_seconds,
    )
    echo_alias(
        alias,
        algorithm.totp(params),
        algorithm.get_seconds_remaining(params),
        ctx.obj["color"],
    )


@otp.command(help="Print the one-time password for all ALIASes.")
@click.pass_context
def show_all(ctx: click.Context):
    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    for alias, alias_data in data.otp.items():
        params = algorithm.TOTPParameters(
            secret=alias_data.secret.encode(),
            digits_count=alias_data.digits_count,
            hash_algorithm=alias_data.hash_algorithm,
            time_step_seconds=alias_data.params.time_step_seconds,
        )
        echo_alias(
            alias,
            algorithm.totp(params),
            algorithm.get_seconds_remaining(params),
            ctx.obj["color"],
        )


@otp.command(help="Initialize the master key and local database.")
@click.pass_context
def init(ctx: click.Context):
    try:
        quiet = ctx.obj["quiet"]
        keyring_ = ctx.obj["keyring_"]

        handle_conflicting_options(
            {"-q, --quiet": quiet, "-K, --no-keyring": not keyring_}
        )

        if JSONEncryptedDB.exists(settings.DB_PATH):
            raise click.UsageError(
                f"The local database `{settings.DB_PATH}` is already initialized"
            )

        db = JSONEncryptedDB.initialize(settings.DB_PATH)
        key_ = db.key.decode()

        if keyring_ and KEYRING_INSTALLED:
            keyring_set(password=key_)

        if not quiet:
            click.echo(key_)
    except click.ClickException as e:
        raise e
    except Exception as e:
        pathlib.Path(settings.DB_PATH).unlink(missing_ok=True)
        raise e


@otp.command(help="Print the master key.")
@click.pass_context
def key(ctx: click.Context):
    quiet = ctx.obj["quiet"]
    keyring_ = ctx.obj["keyring_"]

    if keyring_:
        if KEYRING_INSTALLED:
            key_ = keyring_get()
        else:
            raise click.UsageError("keyring not installed")
    else:
        raise click.UsageError("cannot show key, keyring disabled, try -k, --keyring")

    click.echo(key_)


@otp.command(help="Remove the secret for the specified ALIAS.")
@click.argument("alias")
@click.confirmation_option(prompt="Are you sure?")
@click.pass_context
def delete(ctx: click.Context, alias: str):
    quiet = ctx.obj["quiet"]
    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    try:
        del data.otp[alias]
    except KeyError:
        raise click.UsageError(f"Alias: {alias} does not exist")
    db.write(data)

    if not quiet:
        click.echo(f"{alias} deleted")


@otp.command("ls", help="List all added ALIASes.")
@click.pass_context
def list_(ctx: click.Context):
    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    for alias in data.otp.keys():
        click.echo(alias)


class ExportFormat(str, enum.Enum):
    JSON = "json"


EXPORT_FORMAT_OPTION = click.option(
    "format_",
    "-f",
    "--format",
    type=click.Choice(list(ExportFormat), case_sensitive=False),
    default=ExportFormat.JSON.value,
    show_default=True,
)


@otp.command("export", help="Export the local database to STDOUT.")
@EXPORT_FORMAT_OPTION
@click.pass_context
def export(ctx: click.Context, format_: str):
    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    if format_ == ExportFormat.JSON:
        click.echo(data.json())
        return None
    raise UnhandledFormatException(format_)


@otp.command("import", help="Import the local database from FILE.")
@click.argument("file", type=click.File())
@EXPORT_FORMAT_OPTION
@click.pass_context
def import_(ctx: click.Context, file, format_: str):
    pass


@otp.command(help="Add the new secret as the specified ALIAS.")
@click.argument("alias")
@click.option("uri", "-u", "--uri", is_flag=True)
@click.option("label", "-l", "--label")
@click.option("period", "-p", "--period", type=click.INT)
@click.option("issuer", "-i", "--issuer")
@click.pass_context
def add(
    ctx: click.Context, alias: str, uri: bool, label: str, period: int, issuer: str
):
    # TODO(khanek) POC
    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    data.add_totp_alias(
        name=alias,
        secret=secrets.token_hex(),
        digits_count=6,
        hash_algorithm="sha1",
        initial_time=datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc),
        time_step_seconds=30,
    )
    db.write(data)
    return  # TODO(khanek) Remove after POC

    quiet = ctx.obj["quiet"]

    if uri:
        handle_conflicting_options(
            {
                "-u, --uri": uri,
                "-l, --label": label,
                "-p, --period": period,
                "-i, --issuer": issuer,
            }
        )
        input_uri = click.prompt("Enter URI", confirmation_prompt=True, hide_input=True)
    else:
        input_secret = click.prompt(
            "Enter secret", confirmation_prompt=True, hide_input=True
        )

    if not quiet:
        click.echo(f"{alias} added")


def main():
    otp()


if __name__ == "__main__":
    main()

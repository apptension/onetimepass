import datetime
import enum
import functools
import json
import pathlib
from typing import Dict
from typing import Optional

import click
import pydantic

from onetimepass import algorithm
from onetimepass import otp_auth_uri
from onetimepass import settings
from onetimepass.db import BaseDB
from onetimepass.db import DatabaseSchema
from onetimepass.db import DBCorruption
from onetimepass.db import DBDoesNotExist
from onetimepass.db import DBMergeConflict
from onetimepass.db import DBUnsupportedVersion
from onetimepass.db import JSONEncryptedDB
from onetimepass.db.models import AliasSchema
from onetimepass.db.models import create_alias_schema
from onetimepass.db.models import HOTPParams
from onetimepass.db.models import OTPAlgorithm
from onetimepass.db.models import OTPType
from onetimepass.db.models import TOTPParams
from onetimepass.exceptions import UnhandledFormatException


class ClickUsageError(click.UsageError):
    """Wrapper on the `click.UsageError that automatically wraps the error message"""

    def __init__(self, message: str, ctx: Optional[click.Context] = None) -> None:
        super().__init__(click.wrap_text(str(message)), ctx)


def get_db_data(db: BaseDB) -> DatabaseSchema:
    try:
        return db.read()
    except DBDoesNotExist:
        raise ClickUsageError(
            "Database does not exist. Try to initialize it first `opt init`"
        )
    except pydantic.ValidationError as e:
        raise DBCorruption from e


def get_default_initial_time():
    return datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)


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


def echo_hotp_alias(alias: str, code: int):
    click.echo(f"{alias}: {code}")


def handle_conflicting_options(options: Dict[str, bool]):
    conflicting_options = {k: v for k, v in options.items() if v}
    if len(conflicting_options) > 1:
        options_list = "; ".join([str(k) for k in conflicting_options])
        raise ClickUsageError(f"conflicting options: {options_list}")


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
        raise ClickUsageError(f"Alias: {alias} does not exist")
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
    need_db_save = False
    for alias, alias_data in data.otp.items():
        if alias_data.otp_type == OTPType.TOTP:
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
        elif alias_data.otp_type == OTPType.HOTP:
            params = algorithm.HOTPParameters(
                secret=alias_data.secret.encode(),
                digits_count=alias_data.digits_count,
                hash_algorithm=alias_data.hash_algorithm,
                counter=alias_data.params.counter,
            )
            echo_hotp_alias(
                alias, algorithm.hotp(params),
            )
            alias_data.params.counter += 1
            need_db_save = True
        else:
            raise NotImplementedError
    if need_db_save:
        db.write(data)


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
            raise ClickUsageError(
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
            raise ClickUsageError("keyring not installed")
    else:
        raise ClickUsageError("cannot show key, keyring disabled, try -k, --keyring")

    click.echo(key_)


@otp.command("rm", help="Remove the secret for the specified ALIAS.")
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
        raise ClickUsageError(f"Alias: {alias} does not exist")
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
    if format_ == ExportFormat.JSON:
        try:
            imported_data = json.load(file)
        except json.JSONDecodeError as e:
            raise ClickUsageError(f"Invalid JSON: {e}")
    else:
        raise UnhandledFormatException(format_)
    try:
        imported_data = DatabaseSchema(**imported_data)
    except DBUnsupportedVersion as e:
        raise ClickUsageError(e)

    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)

    try:
        data.merge(imported_data)
    except DBMergeConflict as e:
        raise ClickUsageError(click.wrap_text(str(e)))
    db.write(data)


@otp.group(help="Add the new secret as the specified ALIAS.")
@click.pass_context
def add(ctx: click.Context):
    pass


@add.command("uri", help="Add the new secret as the specified ALIAS.")
@click.argument("alias")
@click.pass_context
def add_uri(ctx: click.Context, alias: str):
    quiet = ctx.obj["quiet"]

    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    if alias in data.otp:
        raise click.UsageError(f"Alias {alias} exists. Consider renaming it")

    input_uri = click.prompt("Enter URI", confirmation_prompt=True, hide_input=True)
    uri_parsed = otp_auth_uri.parse(input_uri)
    alias_data = create_alias_schema(
        otp_type=uri_parsed.otp_type,
        label=uri_parsed.label,
        issuer=uri_parsed.issuer,
        secret=uri_parsed.secret,
        digits_count=uri_parsed.digits,
        hash_algorithm=uri_parsed.algorithm,
        params=uri_parsed.params,
    )

    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    data.add_alias(alias, alias_data)
    db.write(data)
    if not quiet:
        click.echo(f"{alias} added")


@add.command("hotp")
@click.argument("alias")
@click.option("label", "-l", "--label")
@click.option("issuer", "-i", "--issuer")
@click.option(
    "algorithm",
    "-a",
    "--algorithm",
    show_default=True,
    type=click.Choice(OTPAlgorithm),
    default=OTPAlgorithm.SHA1.value,
)
@click.option(
    "digits_count",
    "-dc",
    "--digits-count",
    show_default=True,
    type=click.INT,
    default=settings.DEFAULT_DIGITS_COUNT,
)
@click.option(
    "counter",
    "-p",
    "--counter",
    type=click.INT,
    show_default=True,
    default=settings.DEFAULT_HOTP_COUNTER,
)
@click.pass_context
def add_hotp(
    ctx: click.Context,
    alias: str,
    label: str,
    issuer: str,
    algorithm: str,
    digits_count: int,
    counter: int,
):
    quiet = ctx.obj["quiet"]
    input_secret = click.prompt(
        "Enter secret", confirmation_prompt=True, hide_input=True
    )

    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    if alias in data.otp:
        raise click.UsageError(f"Alias {alias} exists. Consider renaming it")

    alias_data = AliasSchema(
        otp_type=OTPType.HOTP,
        label=label,
        issuer=issuer,
        secret=input_secret,
        digits_count=digits_count,
        hash_algorithm=algorithm,
        params=HOTPParams(counter=counter),
    )

    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    data.add_alias(alias, alias_data)
    db.write(data)
    if not quiet:
        click.echo(f"{alias} added")


@add.command("totp")
@click.argument("alias")
@click.option("label", "-l", "--label")
@click.option("issuer", "-i", "--issuer")
@click.option(
    "algorithm",
    "-a",
    "--algorithm",
    show_default=True,
    type=click.Choice(OTPAlgorithm),
    default=OTPAlgorithm.SHA1.value,
)
@click.option(
    "digits_count",
    "-dc",
    "--digits-count",
    show_default=True,
    type=click.INT,
    default=settings.DEFAULT_DIGITS_COUNT,
)
@click.option(
    "period",
    "-p",
    "--period",
    type=click.INT,
    show_default=True,
    default=settings.DEFAULT_TIME_STEP_SECONDS,
)
@click.option(
    "initial_time",
    "-t",
    "--initial-time",
    type=click.DateTime(),
    default=get_default_initial_time,
)
@click.pass_context
def add_totp(
    ctx: click.Context,
    alias: str,
    label: str,
    issuer: str,
    algorithm: str,
    digits_count: int,
    period: int,
    initial_time: datetime.datetime,
):
    quiet = ctx.obj["quiet"]
    input_secret = click.prompt(
        "Enter secret", confirmation_prompt=True, hide_input=True
    )

    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    if alias in data.otp:
        raise click.UsageError(f"Alias {alias} exists. Consider renaming it")

    alias_data = AliasSchema(
        otp_type=OTPType.TOTP,
        label=label,
        issuer=issuer,
        secret=input_secret,
        digits_count=digits_count,
        hash_algorithm=algorithm,
        params=TOTPParams(initial_time=initial_time, time_step_seconds=period),
    )

    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = get_db_data(db)
    data.add_alias(alias, alias_data)
    db.write(data)
    if not quiet:
        click.echo(f"{alias} added")


@otp.command("mv", help="Rename the specified ALIAS.")
@click.argument("old_alias")
@click.argument("new_alias")
@click.pass_context
def rename(ctx: click.Context, old_alias: str, new_alias: str):
    db = JSONEncryptedDB(path=settings.DB_PATH, key=keyring_get().encode())
    data = db.read()
    try:
        data.otp[new_alias] = data.otp.pop(old_alias)
        db.write(data)
    except KeyError:
        raise ClickUsageError(f"Alias: {old_alias} does not exist")


def main():
    otp()


if __name__ == "__main__":
    main()

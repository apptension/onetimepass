import binascii
import datetime
import functools
import json
import logging
import pathlib
import time
from typing import Dict

import click
import cryptography.fernet
import pydantic
from rich.console import Console

from onetimepass import base32
from onetimepass import master_key
from onetimepass import otp_algorithm
from onetimepass import settings
from onetimepass.db import BaseDB
from onetimepass.db import DatabaseSchema
from onetimepass.db import DBAlreadyInitialized
from onetimepass.db import DBCorruption
from onetimepass.db import DBDoesNotExist
from onetimepass.db import DBMergeConflict
from onetimepass.db import DBUnsupportedVersion
from onetimepass.db import JSONEncryptedDB
from onetimepass.db.models import AliasSchema
from onetimepass.db.models import HOTPParams
from onetimepass.db.models import TOTPParams
from onetimepass.enum import ExportFormat
from onetimepass.enum import HashAlgorithm
from onetimepass.enum import OTPType
from onetimepass.exceptions import UnhandledFormatException
from onetimepass.exceptions import UnhandledOTPTypeException
from onetimepass.logging import logger
from onetimepass.logging import logging_basic_config
from onetimepass.otpauth import ParsingError
from onetimepass.otpauth import Uri


class ClickUsageError(click.UsageError):
    """Wrapper on the `click.UsageError that automatically wraps the error message"""

    def __init__(
        self, message: str | Exception, ctx: click.Context | None = None
    ) -> None:
        super().__init__(click.wrap_text(str(message)), ctx)


def get_db_data(db: BaseDB) -> DatabaseSchema:
    try:
        return db.read()
    except DBDoesNotExist:
        raise ClickUsageError(
            "Database does not exist. Try to initialize it first `opt init`"
        )
    except cryptography.fernet.InvalidToken:
        raise ClickUsageError(
            "Provided master key is different than the one used during the `otp init`"
        )
    except pydantic.ValidationError as e:
        raise DBCorruption from e


def get_decrypted_db(use_keyring: bool) -> JSONEncryptedDB:
    try:
        try:
            key_ = bytes(master_key.MasterKey(use_keyring=use_keyring))
        except master_key.EmptyKeyException:
            # Fallback in case there is no master key in the keyring; this is
            # possible during a migration of the application to another device
            # if it's done by copying encrypted database into another device
            key_ = bytes(master_key.MasterKey(use_keyring=False))

        try:
            return JSONEncryptedDB(path=settings.DB_PATH, key=key_)
        except binascii.Error as e:
            raise master_key.InvalidMasterKeyFormat(
                f"Provided master key is not a valid base64: {e}"
            )
    except master_key.BaseMasterKeyException as e:
        raise ClickUsageError(e)


def get_default_initial_time():
    return datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)


def echo_alias(
    alias: str, code: int, seconds_remaining: int, color: bool, digits_count: int
):
    seconds_remaining_str = f"{seconds_remaining:0>2}s"
    if color:
        if seconds_remaining <= 10:
            seconds_remaining_str = click.style(
                seconds_remaining_str, fg="red", bold=True
            )
    click.echo(f"{alias}: {code:0{digits_count}} {seconds_remaining_str}")


def echo_hotp_alias(alias: str, code: int, digits_count: int):
    click.echo(f"{alias}: {code:0{digits_count}}")


def handle_conflicting_options(options: Dict[str, bool]):
    conflicting_options = {k: v for k, v in options.items() if v}
    if len(conflicting_options) > 1:
        options_list = "; ".join([str(k) for k in conflicting_options])
        raise ClickUsageError(f"conflicting options: {options_list}")


def validation_error_to_str(error: pydantic.ValidationError) -> str:
    error_messages: list[str] = [str(i.exc) for i in error.args[0]]

    if len(error_messages) == 1:
        return error_messages[0]

    error_messages.insert(0, "")
    bullet_list = "\n- ".join(error_messages)
    return bullet_list


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option()
@click.option("color", "-c/-C", "--color/--no-color", default=True, show_default=True)
@click.option("quiet", "-q", "--quiet", is_flag=True)
@click.option(
    "keyring_",
    "-k/-K",
    "--keyring/--no-keyring",
    default=master_key.MasterKey.keyring_available(),
    show_default="True if keyring installed, False otherwise",
)
@click.option(
    "debug",
    "-d/-D",
    "--debug/--no-debug",
    default=False,
    show_default=True,
    help="Enable/disable debug info.",
)
@click.pass_context
def otp(ctx: click.Context, color: bool, quiet: bool, keyring_: bool, debug: bool):
    ctx.ensure_object(dict)
    ctx.obj.update({"color": color, "quiet": quiet, "keyring_": keyring_})

    if debug:
        logging_basic_config(level=logging.DEBUG)
    else:
        logging_basic_config()


@otp.command(help="Print the one-time password for the specified ALIAS.")
@click.argument("alias")
@click.option(
    "wait",
    "-w",
    "--wait-for-next",
    type=click.IntRange(min=1, max=29),
    help="Wait for next code if remaining time is less than x seconds",
)
@click.option(
    "minimum_verbose",
    "-m",
    "--minimum-verbose",
    is_flag=True,
    help="Shows only OTP code",
)
@click.pass_context
def show(ctx: click.Context, alias: str, wait: int | None, minimum_verbose: bool):
    keyring = ctx.obj["keyring_"]

    db = get_decrypted_db(keyring)
    data = get_db_data(db)
    try:
        alias_data = data.otp[alias]
    except KeyError:
        raise ClickUsageError(f"Alias: {alias} does not exist")
    if alias_data.otp_type == OTPType.TOTP:
        if wait is not None:
            remaining_seconds = otp_algorithm.get_seconds_remaining(
                otp_algorithm.TOTPParameters(
                    secret=base32.decode(alias_data.secret),
                    digits_count=alias_data.digits_count,
                    hash_algorithm=alias_data.hash_algorithm,
                    time_step_seconds=alias_data.params.time_step_seconds,
                )
            )
            if remaining_seconds < wait:
                with Console().status("Waiting for the next OTP..."):
                    time.sleep(remaining_seconds)
        # Reinitialize parameters to get valid result
        params = otp_algorithm.TOTPParameters(
            secret=base32.decode(alias_data.secret),
            digits_count=alias_data.digits_count,
            hash_algorithm=alias_data.hash_algorithm,
            time_step_seconds=alias_data.params.time_step_seconds,
        )
        if minimum_verbose:
            click.echo(f"{otp_algorithm.totp(params):0{params.digits_count}}")
        else:
            echo_alias(
                alias,
                otp_algorithm.totp(params),
                otp_algorithm.get_seconds_remaining(params),
                ctx.obj["color"],
                params.digits_count,
            )
    elif alias_data.otp_type == OTPType.HOTP:
        alias_data.params.counter += 1
        params = otp_algorithm.HOTPParameters(
            secret=base32.decode(alias_data.secret),
            digits_count=alias_data.digits_count,
            hash_algorithm=alias_data.hash_algorithm,
            counter=alias_data.params.counter,
        )
        echo_hotp_alias(alias, otp_algorithm.hotp(params), alias_data.digits_count)
        # This have to be the last step of the command, to make sure the
        # database is not modified if there is any unexpected exception.
        # Alternatively, there should be commit/rollback mechanism added to the
        # database handler.
        db.write(data)
    else:
        raise NotImplementedError


@otp.command(help="Initialize the master key and local database.")
@click.pass_context
def init(ctx: click.Context):
    quiet = ctx.obj["quiet"]
    keyring_ = ctx.obj["keyring_"]

    handle_conflicting_options({"-q, --quiet": quiet, "-K, --no-keyring": not keyring_})

    try:
        db = JSONEncryptedDB.initialize(settings.DB_PATH)
    except DBAlreadyInitialized as e:
        raise ClickUsageError(e)

    try:
        key_ = db.key.decode()
        if keyring_:
            key_ = master_key.MasterKey.create_in_keyring(key_)

        if not quiet:
            click.echo(key_)
    except Exception as e:
        # Rollback partially created database
        pathlib.Path(settings.DB_PATH).unlink(missing_ok=True)
        raise e


@otp.command(help="Change the master key for the local database.")
# Until we implement a rollback mechanism, let's make it a responsibility of a user
@click.confirmation_option(prompt="Did you make a backup of your local database?")
@click.pass_context
def passwd(ctx: click.Context):
    quiet = ctx.obj["quiet"]
    keyring_ = ctx.obj["keyring_"]

    handle_conflicting_options({"-q, --quiet": quiet, "-K, --no-keyring": not keyring_})

    old_db = get_decrypted_db(keyring_)
    data = get_db_data(old_db)

    key_ = cryptography.fernet.Fernet.generate_key()
    new_db = JSONEncryptedDB(path=old_db.path, key=key_)

    # TODO make a backup of the old database in case of an exception
    new_db.write(data)

    try:
        key_ = key_.decode()
        if keyring_:
            key_ = master_key.MasterKey.create_in_keyring(key_)

        if not quiet:
            click.echo(key_)
    except Exception as e:
        # TODO rollback
        raise e


@otp.command(help="Print the master key.")
@click.pass_context
def key(ctx: click.Context):
    keyring_ = ctx.obj["keyring_"]

    if not keyring_:
        raise ClickUsageError("cannot show key, keyring disabled, try -k, --keyring")

    try:
        key_ = master_key.MasterKey(use_keyring=keyring_)
    except master_key.BaseMasterKeyException as e:
        raise ClickUsageError(e)
    click.echo(key_)


@otp.command("rm", help="Remove the secret for the specified ALIAS.")
@click.argument("alias")
@click.confirmation_option(prompt="Are you sure?")
@click.pass_context
def delete(ctx: click.Context, alias: str):
    quiet = ctx.obj["quiet"]
    keyring = ctx.obj["keyring_"]

    db = get_decrypted_db(keyring)
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
    keyring = ctx.obj["keyring_"]

    db = get_decrypted_db(keyring)
    data = get_db_data(db)
    for alias in data.otp.keys():
        click.echo(alias)


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
    keyring = ctx.obj["keyring_"]

    db = get_decrypted_db(keyring)
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
    keyring = ctx.obj["keyring_"]

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

    db = get_decrypted_db(keyring)
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


@add.command("uri", help="Add the new secret from URI as the specified ALIAS.")
@click.argument("alias")
@click.pass_context
def add_uri(ctx: click.Context, alias: str):
    quiet = ctx.obj["quiet"]
    keyring = ctx.obj["keyring_"]

    db = get_decrypted_db(keyring)
    data = get_db_data(db)
    if alias in data.otp:
        raise ClickUsageError(f"Alias {alias} exists. Consider renaming it")

    input_uri = click.prompt("Enter URI", confirmation_prompt=True, hide_input=True)
    try:
        uri_parsed = Uri.parse(input_uri)
    except ParsingError as e:
        logger.debug(e)
        raise ClickUsageError("invalid URI")

    otp_type = OTPType(uri_parsed.type)
    params: HOTPParams | TOTPParams
    if otp_type == OTPType.HOTP:
        params = HOTPParams(counter=uri_parsed.parameters.counter)
    elif otp_type == OTPType.TOTP:
        params = TOTPParams(
            initial_time=get_default_initial_time(),
            time_step_seconds=uri_parsed.parameters.period,
        )
    else:
        raise UnhandledOTPTypeException(otp_type)

    try:
        alias_data = AliasSchema(
            otp_type=otp_type,
            label=str(uri_parsed.label),
            issuer=uri_parsed.parameters.issuer or uri_parsed.label.issuer,
            secret=uri_parsed.parameters.secret,
            digits_count=uri_parsed.parameters.digits,
            hash_algorithm=uri_parsed.parameters.hash_algorithm,
            params=params,
        )
    except pydantic.ValidationError as e:
        raise ClickUsageError(validation_error_to_str(e))

    data.add_alias(alias, alias_data)
    db.write(data)
    if not quiet:
        click.echo(f"{alias} added")


def default_add_otp_options(fn):
    @functools.wraps(fn)
    @click.option("label", "-l", "--label")
    @click.option("issuer", "-i", "--issuer")
    @click.option(
        "hash_algorithm",
        "-a",
        "--hash_algorithm",
        show_default=True,
        type=click.Choice([i.value for i in HashAlgorithm]),
        default=HashAlgorithm.SHA1.value,
    )
    @click.option(
        "digits_count",
        "-d",
        "--digits-count",
        show_default=True,
        type=click.INT,
        default=settings.DEFAULT_DIGITS_COUNT,
    )
    def _wrapped(*args, **kwargs):
        return fn(*args, **kwargs)

    return _wrapped


@add.command("hotp", help="Add the new HOTP secret as the specified ALIAS.")
@click.argument("alias")
@click.option(
    "counter",
    "-c",
    "--counter",
    type=click.INT,
    show_default=True,
    default=settings.DEFAULT_INITIAL_HOTP_COUNTER,
)
@default_add_otp_options  # this must be after click.option line-wise
@click.pass_context
def add_hotp(
    ctx: click.Context,
    alias: str,
    label: str | None,
    issuer: str | None,
    hash_algorithm: str,
    digits_count: int,
    counter: int,
):
    quiet = ctx.obj["quiet"]
    keyring = ctx.obj["keyring_"]

    input_secret = click.prompt(
        "Enter secret", confirmation_prompt=True, hide_input=True
    )

    db = get_decrypted_db(keyring)
    data = get_db_data(db)
    if alias in data.otp:
        raise ClickUsageError(f"Alias {alias} exists. Consider renaming it")

    try:
        alias_data = AliasSchema(
            otp_type=OTPType.HOTP,
            label=label,
            issuer=issuer,
            secret=input_secret,
            digits_count=digits_count,
            hash_algorithm=HashAlgorithm(hash_algorithm),
            params=HOTPParams(counter=counter),
        )
    except pydantic.ValidationError as e:
        raise ClickUsageError(validation_error_to_str(e))

    data.add_alias(alias, alias_data)
    db.write(data)
    if not quiet:
        click.echo(f"{alias} added")


@add.command("totp", help="Add the new TOTP secret as the specified ALIAS.")
@click.argument("alias")
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
@default_add_otp_options  # this must be after click.option line-wise
@click.pass_context
def add_totp(
    ctx: click.Context,
    alias: str,
    label: str | None,
    issuer: str | None,
    hash_algorithm: str,
    digits_count: int,
    period: int,
    initial_time: datetime.datetime,
):
    quiet = ctx.obj["quiet"]
    keyring = ctx.obj["keyring_"]

    input_secret = click.prompt(
        "Enter secret", confirmation_prompt=True, hide_input=True
    )

    db = get_decrypted_db(keyring)
    data = get_db_data(db)
    if alias in data.otp:
        raise ClickUsageError(f"Alias {alias} exists. Consider renaming it")

    try:
        alias_data = AliasSchema(
            otp_type=OTPType.TOTP,
            label=label,
            issuer=issuer,
            secret=input_secret,
            digits_count=digits_count,
            hash_algorithm=HashAlgorithm(hash_algorithm),
            params=TOTPParams(initial_time=initial_time, time_step_seconds=period),
        )
    except pydantic.ValidationError as e:
        raise ClickUsageError(validation_error_to_str(e))

    data.add_alias(alias, alias_data)
    db.write(data)
    if not quiet:
        click.echo(f"{alias} added")


@otp.command("mv", help="Rename the specified ALIAS.")
@click.argument("old_alias")
@click.argument("new_alias")
@click.pass_context
def rename(ctx: click.Context, old_alias: str, new_alias: str):
    keyring = ctx.obj["keyring_"]

    db = get_decrypted_db(keyring)
    data = get_db_data(db)
    try:
        data.otp[new_alias] = data.otp.pop(old_alias)
        db.write(data)
    except KeyError:
        raise ClickUsageError(f"Alias: {old_alias} does not exist")


@otp.command(help="Print the database filepath and (optionally) its version.")
@click.option(
    "version",
    "--version",
    is_flag=True,
    help="Include the database version in the output (requires the master key).",
)
@click.pass_context
def db(ctx: click.Context, version: bool):
    keyring = ctx.obj["keyring_"]

    if version:
        db = get_decrypted_db(keyring)
        data = get_db_data(db)
        click.echo(f"{settings.DB_PATH} (version {data.version})")
    else:
        click.echo(settings.DB_PATH)


def main():
    otp()


if __name__ == "__main__":
    main()

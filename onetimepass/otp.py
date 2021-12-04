import enum
import random
import secrets
import string
from typing import Dict

import click


KEY = secrets.token_hex()


def keyring_installed():
    try:
        import keyring
    except ImportError:
        return False
    else:
        return True


def handle_conflicting_options(options: Dict[str, bool]):
    conflicting_options = {k: v for k, v in options.items() if v}
    if len(conflicting_options) > 1:
        options_list = "; ".join([str(k) for k in conflicting_options])
        raise click.UsageError(f"conflicting options: {options_list}")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("color", "-c/-C", "--color/--no-color", default=True, show_default=True)
@click.option("quiet", "-q", "--quiet", is_flag=True)
@click.option(
    "keyring",
    "-k/-K",
    "--keyring/--no-keyring",
    default=keyring_installed,
    show_default="True if keyring installed, False otherwise",
)
@click.pass_context
def otp(ctx: click.Context, color: bool, quiet: bool, keyring: bool):
    ctx.ensure_object(dict)
    ctx.obj.update({"color": color, "quiet": quiet, "keyring": keyring})


@otp.command(help="Print the one-time password for the specified ALIAS.")
@click.argument("alias")
@click.pass_context
def show(ctx: click.Context, alias: str):
    color = ctx.obj["color"]

    code = "".join(random.choices(string.digits, k=6))
    seconds_remaining = random.randint(1, 30)

    seconds_remaining_str = f"{seconds_remaining:0>2}s"
    if color:
        if seconds_remaining <= 10:
            seconds_remaining_str = click.style(
                f"{seconds_remaining:0>2}s", fg="red", bold=True
            )

    click.echo(f"{alias}: {code} {seconds_remaining_str}")


@otp.command(help="Initialize the master key and local database.")
@click.pass_context
def init(ctx: click.Context):
    quiet = ctx.obj["quiet"]
    keyring = ctx.obj["keyring"]

    handle_conflicting_options({"-q, --quiet": quiet, "-K, --no-keyring": not keyring})

    key_ = KEY  # generated

    if not quiet:
        click.echo(key_)


@otp.command(help="Print the master key.")
@click.pass_context
def key(ctx: click.Context):
    quiet = ctx.obj["quiet"]
    keyring = ctx.obj["keyring"]

    if keyring:
        if keyring_installed():
            key_ = KEY  # got from keyring
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

    if not quiet:
        click.echo(f"{alias} deleted")


@otp.command("ls", help="List all added ALIASes.")
@click.pass_context
def list_(ctx: click.Context):
    pass


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
def export(ctx: click.Context, format_: list[str]):
    pass


@otp.command("import", help="Import the local database from FILE.")
@click.argument("file", type=click.File())
@EXPORT_FORMAT_OPTION
@click.pass_context
def import_(ctx: click.Context, file, format_: list[str]):
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

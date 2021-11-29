"""
This module provides the command line interface.

Usage: python -m putio.cli [OPTIONS] COMMAND [ARGS]...

Options:
    --help  Show this message and exit.

Commands:
    login   Login to Put.io.
    upload  Upload FOLDER to Put.io.
"""

import os
from pathlib import Path
from typing import Optional

import dotenv
import typer

import putio.auth
import putio.core
from putio._errors import CLIError


app = typer.Typer(add_completion=False)

dotenv.load_dotenv(".env.secret")
dotenv.load_dotenv(".env.shared")
dotenv.load_dotenv(".env")

ACCESS_TOKEN = os.environ.get("PUTIO_ACCESS_TOKEN")
CLIENT_ID = os.environ.get("PUTIO_CLIENT_ID")
CLIENT_SECRET = os.environ.get("PUTIO_CLIENT_SECRET")


@app.command(
    help=(
        "Login to Put.io.\n\n"
        "`--token` and `--prompt` options are mutually exclusive.\n\n"
        "When no option is given, OAuth 2.0 with Authorization Code flow will be used."
    )
)
def login(  # pylint: disable=[missing-raises-doc]
    token: Optional[str] = typer.Option(
        None, metavar="TOKEN", help="Use TOKEN to login."
    ),
    prompt: bool = typer.Option(
        False, "--prompt", help="Ask for username and password, and use them to login."
    ),
) -> None:
    """
    Usage: python -m putio.cli login [OPTIONS]

    Login to Put.io.

    `--token` and `--prompt` options are mutually exclusive.

    When no option is given, OAuth 2.0 with Authorization Code flow will be used.

    Options:
        --token TOKEN           Use TOKEN to login.
        --prompt                Ask for username and password, and use them to login.
        --help                  Show this message and exit.
    """
    if token and prompt:
        typer.echo("`--token` and `--prompt` options are mutually exclusive.")
        raise typer.Exit(1)

    if token:
        access_token = token
    elif prompt:
        access_token = putio.auth.get_token_from_credentials(CLIENT_ID, CLIENT_SECRET)
    elif ACCESS_TOKEN and (username := putio.auth.verify_token(ACCESS_TOKEN)):
        typer.echo(f"You are already logged in as `{username}`.")
        raise typer.Exit()
    else:
        access_token = putio.auth.get_token_from_oauth()

    if not access_token or not (username := putio.auth.verify_token(access_token)):
        typer.echo("User couldn't be authorized.")
        raise typer.Exit(1)

    dotenv.set_key(".env.secret", "PUTIO_ACCESS_TOKEN", access_token)
    typer.echo(f"You've been successfully logged in as `{username}`.")
    raise typer.Exit()


@app.command(help="Upload FOLDER to Put.io.", no_args_is_help=True)
def upload(  # pylint: disable=[missing-raises-doc]
    source: Path = typer.Argument(
        ...,
        exists=True,
        resolve_path=True,
        file_okay=False,
        metavar="FOLDER",
    ),
    target: Optional[str] = typer.Option(
        None,
        metavar="PATH",
        help="Upload FOLDER to PATH.",
    ),
    name: Optional[str] = typer.Option(
        None,
        metavar="NAME",
        help="Upload FOLDER as NAME.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Replace folders with the same name.",
    ),
    token: Optional[str] = typer.Option(
        None,
        metavar="TOKEN",
        help="Use TOKEN as access token.",
    ),
    verbose: bool = typer.Option(True, "--verbose/--quiet"),
) -> None:
    """
    Usage: python -m putio.cli upload [OPTIONS] FOLDER

        Upload FOLDER to Put.io.

    Arguments:
        FOLDER  [required]

    Options:
        --target PATH           Upload FOLDER to PATH.
        --name NAME             Upload FOLDER as NAME.
        -f, --force             Replace folders with the same name.
        --token TOKEN           Use TOKEN as access token.
        --verbose / --quiet     [default: verbose]
        --help                  Show this message and exit.
    """
    if token and putio.auth.verify_token(token):
        access_token = token
    elif ACCESS_TOKEN and putio.auth.verify_token(ACCESS_TOKEN):
        access_token = ACCESS_TOKEN
    else:
        typer.echo(
            "You're not logged in. Run `putio login --help` to see how to login."
        )
        raise typer.Exit(1)

    if target:
        target = target.strip("/")

    if not name:
        name = source.name

    try:
        putio.core.upload_folder(source, target, name, force, access_token, verbose)
    except (typer.Abort, typer.Exit) as err:
        raise err
    except CLIError as err:
        typer.echo(err)
        raise typer.Exit(1)
    except Exception as err:
        typer.echo(f"An unknown error occured: {err.__class__.__name__}.")
        raise typer.Exit(1) from err
    else:
        raise typer.Exit(0)


if __name__ == "__main__":
    app()

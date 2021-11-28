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

ACCESS_TOKEN = os.environ.get("PUTIO_ACCESS_TOKEN")


@app.command(help="Login to Put.io.")
def login(  # pylint: disable=[missing-raises-doc]
    token: Optional[str] = typer.Option(
        None, metavar="TOKEN", help="Use TOKEN to login."
    ),
) -> None:
    """
    Usage: python -m putio.cli login [OPTIONS]

    Login to Put.io.

    Options:
        --token TOKEN           Use TOKEN to login.
        --help                  Show this message and exit.
    """
    if token and (username := putio.auth.verify_token(token)):
        dotenv.set_key(".env.secret", "PUTIO_ACCESS_TOKEN", token)
        typer.echo(f"You've been successfully logged in as `{username}`.")
        raise typer.Exit()

    if ACCESS_TOKEN and (username := putio.auth.verify_token(ACCESS_TOKEN)):
        typer.echo(f"You are already logged in as `{username}`.")
        raise typer.Exit()

    typer.echo("User couldn't be authorized.")
    raise typer.Exit(1)


@app.command(help="Upload FOLDER to Put.io.", no_args_is_help=True)
def upload(  # pylint: disable=[missing-raises-doc]
    source: Path = typer.Argument(
        ...,
        exists=True,
        resolve_path=True,
        file_okay=False,
        metavar="FOLDER",
    ),
    token: Optional[str] = typer.Option(
        None,
        metavar="TOKEN",
        help="Use TOKEN as access token.",
    ),
) -> None:
    """
    Usage: python -m putio.cli upload [OPTIONS] FOLDER

        Upload FOLDER to Put.io.

    Arguments:
        FOLDER  [required]

    Options:
        --token TOKEN           Use TOKEN as access token.
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

    try:
        putio.core.upload_folder(source, access_token)
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

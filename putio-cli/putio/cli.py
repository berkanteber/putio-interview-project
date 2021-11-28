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
from typing import Optional

import dotenv
import typer

import putio.auth


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
def upload() -> None:
    pass


if __name__ == "__main__":
    app()

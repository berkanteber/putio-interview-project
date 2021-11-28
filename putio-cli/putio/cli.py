"""
This module provides the command line interface.

Usage: python -m putio.cli [OPTIONS] COMMAND [ARGS]...

Options:
    --help  Show this message and exit.

Commands:
    login   Login to Put.io.
    upload  Upload FOLDER to Put.io.
"""

import typer


app = typer.Typer(add_completion=False)


@app.command(help="Login to Put.io.")
def login() -> None:
    pass


@app.command(help="Upload FOLDER to Put.io.", no_args_is_help=True)
def upload() -> None:
    pass


if __name__ == "__main__":
    app()

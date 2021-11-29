"""This module provides authorization related functions."""

import os
import time
import uuid
import webbrowser
from typing import Optional
from urllib.parse import urlencode

import dotenv
import putiopy
import requests
import typer


requests.packages.urllib3.disable_warnings()  # type: ignore  # pylint: disable=[no-member]

dotenv.load_dotenv(".env.secret")
dotenv.load_dotenv(".env.shared")

APP_CLIENT_ID = os.environ["PUTIO_APP_CLIENT_ID"]

AUTHENTICATION_URL = os.environ["PUTIO_AUTHENTICATION_URL"]
APP_BASE_URL = os.environ["PUTIO_APP_BASE_URL"]

APP_OAUTH_TIMEOUT = int(os.environ["PUTIO_APP_OAUTH_TIMEOUT"])
APP_OAUTH_RETRY_PERIOD = int(os.environ["PUTIO_APP_OAUTH_RETRY_PERIOD"])


def get_token_from_oauth() -> str:
    """
    Gets access token using OAuth 2.0.

    Uses Autherization Code flow through an external server.

    If possible, a browser window is automatically launches.
    In some environments (e.g. Docker), this is not possible;
    so user is given a URL to open.

    When user is directed to the authorization URL, it starts polling
    callback server for access token. So user doesn't need to copy
    the access token.

    Returns:
        Access token.

    Raises:
        typer.Exit:
            - An error occured in authorizarion server.
            - Access token couldn't be received in X seconds.
    """

    state = uuid.uuid4().hex
    params = {
        "client_id": APP_CLIENT_ID,
        "redirect_uri": f"{APP_BASE_URL}/oauth-callback",
        "response_type": "code",
        "state": state,
    }
    authentication_url = f"{AUTHENTICATION_URL}?{urlencode(params)}"

    if not webbrowser.open(authentication_url):
        typer.echo(f"Please go to the link below to authorize:\n{authentication_url}")

    os.environ["CURL_CA_BUNDLE"] = ""
    typer.echo("Polling to get access token...")
    remaining, retry_period = APP_OAUTH_TIMEOUT, APP_OAUTH_RETRY_PERIOD
    while remaining:
        response = requests.get(
            f"{APP_BASE_URL}/get-access-token", params={"state": state}
        )

        if response.status_code == 200:
            access_token: str = response.text
            return access_token

        if response.status_code == 404:
            remaining -= retry_period
            time.sleep(retry_period)
        else:
            typer.echo("An error occured in authorization server.")
            raise typer.Exit(1)

    typer.echo(f"Access token couldn't be received in {APP_OAUTH_TIMEOUT} seconds.")
    raise typer.Exit(1)


def get_token_from_credentials(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """
    Gets token using Put.io app credentials and username & password.

    If Put.io app credentials are not given, access token is obtained by
    sending username and password to an external server and using its app credentials.

    If username and password is not given, user is prompted for input.

    Returns:
        Access token.

    Raises:
        typer.Abort:
            - Aborted during asking for username and password.
        typer.Exit:
            - An error occured in authorizarion server.
            - An error occured while creating access token.
    """
    if not (client_id and client_secret):
        username = typer.prompt("Username")
        password = typer.prompt("Password", hide_input=True)

        response = requests.post(
            f"{APP_BASE_URL}/create-access-token",
            json={"username": username, "password": password},
        )

        if response.status_code == 200:
            access_token: str = response.text
            return access_token

        typer.echo("An error occured in authorization server.")
        raise typer.Exit(1)

    if not (username and password):
        username = typer.prompt("Username")
        password = typer.prompt("Password", hide_input=True)

    try:
        access_token = putiopy.create_access_token(
            client_id, client_secret, username, password
        )
    except putiopy.APIError as err:
        typer.echo("An error occured while creating access token.")
        raise typer.Exit(1) from err

    return access_token


def verify_token(access_token: str) -> Optional[str]:
    """
    Verifies that access token is valid.

    Arguments:
        access_token: Access token.

    Returns:
        When successfully verified, username.
        Otherwise, None.
    """
    try:
        username: str = putiopy.Client(access_token).Account.info()["info"]["username"]
    except (putiopy.APIError, KeyError):
        return None

    return username

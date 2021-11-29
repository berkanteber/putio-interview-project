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

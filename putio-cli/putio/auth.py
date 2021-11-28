"""This module provides authorization related functions."""

from typing import Optional

import putiopy


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

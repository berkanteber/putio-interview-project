"""This module provides a Flask app to be used in Put.io authorization."""

import json
import os

import dotenv
import redis
import requests
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request


dotenv.load_dotenv(".env.secret")
dotenv.load_dotenv(".env.shared")

CLIENT_ID = os.environ["PUTIO_CLIENT_ID"]
CLIENT_SECRET = os.environ["PUTIO_CLIENT_SECRET"]

PORT = int(os.environ.get("PORT", 5500))
DEBUG = bool(os.environ.get("DEBUG", False))
DEV = bool(os.environ.get("DEV", False))

REDIRECT_BASE_URL = f"http://127.0.0.1:{PORT}" if DEV else os.environ["BASE_URL"]
REDIRECT_URL = f"{REDIRECT_BASE_URL}/oauth-callback"

HOME_URL = os.environ["HOME_URL"]

REDIS_URL = os.environ["REDIS_URL"]
REDIS_TIMEOUT = os.environ.get("REDIS_TIMEOUT", 300)

db = redis.from_url(REDIS_URL, decode_responses=True)

app = Flask(__name__)


@app.route("/", methods=("GET",))
def home():
    return redirect(HOME_URL)


@app.route("/oauth-callback", methods=("GET",))
def oauth_callback():
    """
    Callback method for OAuth 2.0 Authorization Code flow.

    Uses `state` to distinguish and verify users.
    Keeps access tokens in Redis for a period of time (default: 300 seconds).

    Finally, renders a page to display access token.
    """
    try:
        state = request.args["state"]
        code = request.args["code"]
    except KeyError:
        return "Request must include `state` and `code` as query parameters.", 400

    response = requests.get(
        "https://api.put.io/v2/oauth2/access_token",
        params={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URL,
            "grant_type": "authorization_code",
            "code": code,
        },
    )

    try:
        access_token = json.loads(response.content.decode("utf-8"))["access_token"]
        db.set(state, access_token, ex=300)
    except Exception:
        return "An unknown error occured.", 500

    return render_template("show_access_token.html", access_token=access_token), 200


@app.route("/get-access-token", methods=("GET",))
def get_access_token():
    """
    Returns access token to the user.

    Uses `state` to distinguish and verify users.
    When an access token is returned, it is deleted from Redis.
    """
    try:
        state = request.args["state"]
    except KeyError:
        return "Request must include `state` as a query parameter.", 400

    try:
        access_token = db.getdel(state)
    except Exception:
        return "An unknown error occured.", 500

    if not access_token:
        return "Access token couldn't be found", 404

    return access_token, 200


@app.route("/create-access-token", methods=("POST",))
def create_access_token():
    """Creates access token for the user with username and password."""
    try:
        username = request.get_json()["username"]
        password = request.get_json()["password"]
    except KeyError:
        return "Request must include `username` and `password` fields in its body.", 400

    response = requests.put(
        f"https://api.put.io/v2/oauth2/authorizations/clients/{CLIENT_ID}/",
        data={"client_secret": CLIENT_SECRET},
        auth=(username, password),
    )

    try:
        access_token = json.loads(response.content.decode("utf-8"))["access_token"]
    except Exception:
        return "An unknown error occured.", 500

    return access_token, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)

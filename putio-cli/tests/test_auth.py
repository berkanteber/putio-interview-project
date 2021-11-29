import pytest
from pytest import mark as m

import putiopy
import typer

import putio.auth
import putio.core


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code

    @property
    def text(self):
        if self.status_code == 200:
            return "access token"
        raise Exception


@m.context("Authorizing user")
@m.context("When getting access token using OAuth 2.0 Authorization Code flow.")
class TestOAuthAuthorizationCodeFlow:
    @pytest.fixture
    def apply_patches(self, mocker, fs):
        mocker.patch("putio.auth.AUTHENTICATION_URL", "https://example.com")
        mocker.patch("putio.auth.APP_CLIENT_ID", "123")
        mocker.patch("putio.auth.APP_BASE_URL", "https://example.com")
        mocker.patch("putio.auth.APP_OAUTH_TIMEOUT", 300)
        mocker.patch("putio.auth.APP_OAUTH_RETRY_PERIOD", 5)
        mocker.patch("webbrowser.open", side_effect=(False,))
        yield

    @m.context("When directing user to authorization page")
    @m.context("if browser cannot be opened")
    @m.it("Prints the link to redirect user to the URL")
    def test_oauth_browser_cannot_open(self, mocker, fs, apply_patches):
        mocked_open = mocker.patch("webbrowser.open", side_effect=(False,))
        mocked_echo = mocker.patch("typer.echo", side_effect=SystemExit)

        with pytest.raises(SystemExit):
            putio.auth.get_token_from_oauth()

        url = mocked_open.call_args[0][0]
        mocked_echo.assert_called_once_with(
            f"Please go to the link below to authorize:\n{url}"
        )

    @m.context("When directing user to authorizaion page")
    @m.context("if browser can be opened")
    @m.it("Doesn't print the link to redirect user to the URL")
    def test_oauth_browser_can_open(self, mocker, fs, apply_patches):
        mocker.patch("webbrowser.open", side_effect=(True,))
        mocked_echo = mocker.patch("typer.echo", side_effect=SystemExit)

        with pytest.raises(SystemExit):
            putio.auth.get_token_from_oauth()

        mocked_echo.assert_called_once_with("Polling to get access token...")

    @m.context("When receiving access token from the callback server")
    @m.context("If access token is received immediately")
    @m.it("Returns the received access token")
    def test_oauth_access_token_received(self, mocker, fs, apply_patches):
        mocker.patch("requests.get", side_effect=(FakeResponse(200),))
        mocker.spy(putio.auth, "get_token_from_oauth")

        putio.auth.get_token_from_oauth()

        assert putio.auth.get_token_from_oauth.return_value("access token")

    @m.context("When receiving access token from the callback server")
    @m.context("If access token is not received immediately")
    @m.it("Keeps polling server for access token until it is received")
    def test_oauth_access_token_polling_until_received(self, fs, mocker, apply_patches):
        mocked_request = mocker.patch(
            "requests.get",
            side_effect=(*(FakeResponse(404) for i in range(3)), FakeResponse(200)),
        )

        mocked_sleep = mocker.patch("time.sleep")
        mocker.spy(putio.auth, "get_token_from_oauth")

        putio.auth.get_token_from_oauth()

        assert mocked_request.call_count == 4
        assert mocked_sleep.call_count == 3
        assert putio.auth.get_token_from_oauth.spy_return == "access token"

    @m.context("When receiving access token from the callback server")
    @m.context("If the server doesn't return access token in X seconds")
    @m.it("Quits with saying 'Access token couldn't be received in X seconds.'")
    def test_oauth_server_timeout(self, mocker, fs, capsys, apply_patches):
        mocked_request = mocker.patch(
            "requests.get", side_effect=(FakeResponse(404) for i in range(60))
        )
        mocked_sleep = mocker.patch("time.sleep")
        mocker.spy(putio.auth, "get_token_from_oauth")

        with pytest.raises(typer.Exit):
            putio.auth.get_token_from_oauth()

        captured = capsys.readouterr()
        assert not captured.out.endswith("An error occured couldn't received in.\n")

        assert mocked_request.call_count == 60
        assert mocked_sleep.call_count == 60

    @m.context("When receiving access token from the callback server")
    @m.context("If the server returns an error")
    @m.it("Quits with saying 'An error occured in authorization server.'")
    def test_oauth_server_returned_error(self, mocker, fs, capsys, apply_patches):
        mocker.patch("requests.get", side_effect=(FakeResponse(500),))

        with pytest.raises(typer.Exit):
            putio.auth.get_token_from_oauth()

        captured = capsys.readouterr()
        assert captured.out.endswith("An error occured in authorization server.\n")


@m.context("Authorizing user")
@m.context("When getting access token using from credentials")
class TestCredentials:
    @m.context("When client ID and client secret is not given")
    @m.it("Asks user for username & password and sends it to the external server")
    def test_credentials_client_not_given_ask_input(self, mocker, fs):
        mocker.patch("putio.auth.APP_BASE_URL", "https://example.com")
        mocker.patch("typer.prompt", side_effect=("USER", "PWD"))

        mocked_request = mocker.patch("requests.post", side_effect=SystemExit)

        with pytest.raises(SystemExit):
            putio.auth.get_token_from_credentials()

        mocked_request.assert_called_once_with(
            "https://example.com/create-access-token",
            data={"username": "USER", "password": "PWD"},
        )

    @m.context("When client ID and client secret is not given")
    @m.context("If external server returns the access code")
    @m.it("Returns the received access code")
    def test_credentials_client_not_given_token_received(self, mocker, fs):
        mocker.patch("putio.auth.APP_BASE_URL", "https://example.com")
        mocker.patch("typer.prompt", side_effect=("USER", "PWD"))
        mocker.patch("requests.post", side_effect=(FakeResponse(200),))

        mocker.spy(putio.auth, "get_token_from_credentials")

        putio.auth.get_token_from_credentials()

        assert putio.auth.get_token_from_credentials.spy_return == "access token"

    @m.context("When client ID and client secret is not given")
    @m.context("If external server doesn't return access token")
    @m.it("Quits with saying 'An error occured in authorization server.'")
    def test_credentials_client_not_given_token_not_received(self, mocker, fs, capsys):
        mocker.patch("requests.get", side_effect=(FakeResponse(500),))
        mocker.patch("typer.prompt", side_effect=("USER", "PWD"))
        mocker.patch("requests.post", side_effect=(FakeResponse(500),))

        with pytest.raises(typer.Exit):
            putio.auth.get_token_from_credentials()

        captured = capsys.readouterr()
        assert captured.out.endswith("An error occured in authorization server.\n")

    @m.context("When client ID and client secret is given")
    @m.context("And username and password is not given")
    @m.it("Asks user for username & password and uses them directly")
    def test_credentials_client_given_ask_input(self, mocker, fs):
        mocker.patch("typer.prompt", side_effect=("USER", "PWD"))

        mocked_api_call = mocker.patch(
            "putiopy.create_access_token", side_effect=SystemExit
        )

        with pytest.raises(SystemExit):
            putio.auth.get_token_from_credentials("C_ID", "C_SCRT")

        mocked_api_call.assert_called_once_with("C_ID", "C_SCRT", "USER", "PWD")

    @m.context("When client ID and client secret is given")
    @m.context("And username and password is given")
    @m.it("Use given username and password directly")
    def test_credentials_client_given_username_password_given(self, mocker, fs):
        mocker.patch("putiopy.create_access_token", side_effect=SystemExit)

        with pytest.raises(SystemExit):
            putio.auth.get_token_from_credentials("C_ID", "C_SCRT", "USER", "PWD")

    @m.context("When client ID and client secret is given")
    @m.context("If API returns the access code")
    @m.it("Returns the received access code")
    def test_credentials_client_given_token_received(self, mocker, fs):
        mocker.patch("typer.prompt", side_effect=("USER", "PWD"))
        mocker.patch("putiopy.create_access_token", side_effect=("access token",))

        mocker.spy(putio.auth, "get_token_from_credentials")

        putio.auth.get_token_from_credentials("C_ID", "C_SCRT")

        assert putio.auth.get_token_from_credentials.spy_return == "access token"

    @m.context("When client ID and client secret is given")
    @m.context("If API returns an error")
    @m.it("Returns the received access code")
    def test_credentials_client_given_token_not_received(self, mocker, fs):
        mocker.patch("typer.prompt", side_effect=("USER", "PWD"))
        mocker.patch("putiopy.create_access_token", side_effect=putiopy.APIError)

        with pytest.raises(typer.Exit):
            putio.auth.get_token_from_credentials("C_ID", "C_SCRT")


@m.context("Authorizing user")
@m.context("When verifying an access code")
class TestVerification:
    @m.it("Returns username for the access code if access code is valid")
    def test_access_code_is_valid(self, mocker, fs):
        class FakeAccount:
            @classmethod
            def info(cls):
                return {"info": {"username": "username"}}

        class FakeClient:
            Account = FakeAccount

            def __init__(self, access_token):
                pass

        mocker.patch("putiopy.Client", FakeClient)

        mocker.spy(putio.auth, "verify_token")

        putio.auth.verify_token("access token")

        assert putio.auth.verify_token.spy_return == "username"

    @m.it("Returns `None` if access code is not valid")
    def test_access_code_is_not_valid(self, mocker, fs):
        class FakeAccount:
            @classmethod
            def info(cls):
                raise putiopy.APIError

        class FakeClient:
            Account = FakeAccount

            def __init__(self, access_token):
                pass

        mocker.patch("putiopy.Client", FakeClient)

        mocker.spy(putio.auth, "verify_token")

        putio.auth.verify_token("access token")

        assert putio.auth.verify_token.spy_return is None

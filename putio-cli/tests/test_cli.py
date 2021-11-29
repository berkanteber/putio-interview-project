import pathlib

import pytest
from pytest import mark as m

import typer
from typer.testing import CliRunner

import putio._errors
import putio.cli


runner = CliRunner()


@m.context("Using Command Line Interface")
@m.context("While logging in")
class TestLogin:
    @m.context("When using access token")
    @m.it("Logs user in with the access token if `dont_save` is set to `False`")
    def test_login_with_token(self, mocker, fs):
        mocker.patch("putio.auth.verify_token", side_effect=("username",))

        result = runner.invoke(putio.cli.app, ["login", "--token", "access-token"])

        assert result.stdout == ("You've been successfully logged in as `username`.\n")

    @m.context("When using access token")
    @m.it("Prints the access token if `dont_save` is set to `True`")
    def test_login_with_token_with_dont_save(self, mocker, fs):
        mocker.patch("putio.auth.verify_token", side_effect=("username",))

        result = runner.invoke(
            putio.cli.app, ["login", "--token", "access-token", "--dont-save"]
        )

        assert result.stdout == (
            "Your access token for user `username` is `access-token`.\n"
        )

    @m.context("When using prompt")
    @m.it("Gets access token from username and password")
    def test_login_with_prompt(self, mocker, fs):
        mocker.patch("putio.cli.CLIENT_ID", "C_ID")
        mocker.patch("putio.cli.CLIENT_SECRET", "C_SCRT")
        mocker.patch("putio.auth.get_token_from_credentials", side_effect=SystemExit)

        runner.invoke(putio.cli.app, ["login", "--prompt"])

        putio.auth.get_token_from_credentials.assert_called_once_with("C_ID", "C_SCRT")

    @m.context("When using both access token and promt")
    @m.it("Says '`--token` and `--prompt` options are mutually exclusive.' and exit.")
    def test_login_with_token_and_prompt(self, mocker, fs):
        result = runner.invoke(putio.cli.app, ["login", "--token", "TOKEN", "--prompt"])

        assert (
            result.stdout
            == "`--token` and `--prompt` options are mutually exclusive.\n"
        )
        assert result.exit_code == 1

    @m.context("When using neither token nor prompt")
    @m.context("If access token is in environment variables")
    @m.it("Says 'You are already logged in.' if access token verifies")
    def test_login_access_token_from_env_variables(self, mocker, fs):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=("username",))

        result = runner.invoke(putio.cli.app, ["login"])

        assert result.stdout == "You are already logged in as `username`.\n"

    @m.context("When using neither token nor prompt")
    @m.context("If access token is in environment variables")
    @m.it("Logs user in using OAuth of access token doesn't verify")
    def test_login_access_token_from_env_variables_not_verifies(self, mocker, fs):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=(None,))

        mocker.patch("putio.auth.get_token_from_oauth")

        runner.invoke(putio.cli.app, ["login"])

        putio.auth.get_token_from_oauth.assert_called_once_with()

    @m.context("When using neither token nor prompt")
    @m.context("If access token isn't in environment variables")
    @m.it("Logs user in using OAuth")
    def test_login_using_oauth(self, mocker, fs):
        mocker.patch("putio.cli.ACCESS_TOKEN", None)

        mocker.patch("putio.auth.get_token_from_oauth")

        runner.invoke(putio.cli.app, ["login"])

        putio.auth.get_token_from_oauth.assert_called_once_with()


@m.context("Using Command Line Interface")
@m.context("While uploading folder")
class TestUploadFolder:
    @m.context("When using access token")
    @m.it("Uses the access token if it verifies")
    def test_upload_folder_with_verifying_token(self, mocker, fs):
        mocker.patch("putio.auth.verify_token", side_effect=("username",))
        mocker.patch("putio.core.upload_folder")

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target=None,
                name=None,
                force=False,
                token="access-token",
                verbose=False,
            )

        putio.core.upload_folder.assert_called_once_with(
            path, None, "SOURCE", False, "access-token", False
        )

    @m.context("When using access token")
    @m.it("Directs user to login if ot doesn't verify")
    def test_upload_folder_with_nonverifying_token(self, mocker, fs, capsys):
        mocker.patch("putio.cli.ACCESS_TOKEN", None)
        mocker.patch("putio.auth.verify_token", side_effect=(None,))

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target=None,
                name=None,
                force=False,
                token="access-token",
                verbose=False,
            )

        captured = capsys.readouterr()
        assert captured.out == (
            "You're not logged in. Run `putio login --help` to see how to login.\n"
        )

    @m.context("When access token is in environment variables")
    @m.it("Uses the access token if it verifies")
    def test_upload_folder_with_verifying_token_from_envvar(self, mocker, fs):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=("username",))
        mocker.patch("putio.core.upload_folder")

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target=None,
                name=None,
                force=False,
                token=None,
                verbose=False,
            )

        putio.core.upload_folder.assert_called_once_with(
            path, None, "SOURCE", False, "access-token", False
        )

    @m.context("When access token is in environment variables")
    @m.it("Directs user to login if ot doesn't verify")
    def test_upload_folder_with_bad_token_from_envvar(self, mocker, fs, capsys):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=(None,))

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target=None,
                name=None,
                force=False,
                token=None,
                verbose=False,
            )

        captured = capsys.readouterr()
        assert captured.out == (
            "You're not logged in. Run `putio login --help` to see how to login.\n"
        )

    @m.context("When manipulating input data")
    @m.it("Corrects badly given target name")
    def test_target_name_correction(self, mocker, fs):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=("username",))
        mocker.patch("putio.core.upload_folder")

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target="/qwe/",
                name=None,
                force=False,
                token=None,
                verbose=False,
            )

        putio.core.upload_folder.assert_called_once_with(
            path, "qwe", "SOURCE", False, "access-token", False
        )

    @m.context("When manipulating input data")
    @m.it("Uses given name instead of source name")
    def test_source_name_override(self, mocker, fs):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=("username",))
        mocker.patch("putio.core.upload_folder")

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target=None,
                name="name",
                force=False,
                token=None,
                verbose=False,
            )

        putio.core.upload_folder.assert_called_once_with(
            path, None, "name", False, "access-token", False
        )

    @m.context("When handling errors")
    @m.it("Pass Typer errors as is")
    def test_typer_error(self, mocker, fs):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=("username",))

        mocker.patch("putio.core.upload_folder", side_effect=typer.Abort)

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Abort):
            putio.cli.upload(
                source=path,
                target=None,
                name=None,
                force=False,
                token=None,
                verbose=False,
            )

    @m.context("When handling errors")
    @m.it("Prints CLI errors correctly")
    def test_cli_error(self, mocker, fs, capsys):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=("username",))

        mocker.patch(
            "putio.core.upload_folder",
            side_effect=putio._errors.UnknownAPIError(context="context"),
        )

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target=None,
                name=None,
                force=False,
                token=None,
                verbose=False,
            )

        captured = capsys.readouterr()
        assert captured.out == "An unknown error occured while context.\n"

    @m.context("When handling errors")
    @m.it("Prints other errors correctly")
    def test_other_errors(self, mocker, fs, capsys):
        mocker.patch("putio.cli.ACCESS_TOKEN", "access-token")
        mocker.patch("putio.auth.verify_token", side_effect=("username",))

        mocker.patch("putio.core.upload_folder", side_effect=KeyError)

        path = pathlib.Path("SOURCE")

        with pytest.raises(typer.Exit):
            putio.cli.upload(
                source=path,
                target=None,
                name=None,
                force=False,
                token=None,
                verbose=False,
            )

        captured = capsys.readouterr()
        assert captured.out == "An unknown error occured: KeyError.\n"

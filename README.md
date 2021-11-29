# Put.io Interview Project

This project consists of 2 apps:

1. The main app is a CLI app providing 2 commands: `login` and `upload`. To make the CLI app, [Typer](https://github.com/tiangolo/typer) is used.
2. The second app is a small Flask app to use in authorization, it is currently deployed to Heroku.

## Installation

You can install [putio-cli](putio-cli) using Docker by following these steps:

```sh
$ git clone https://github.com/berkanteber/putio-interview-project.git
$ cd putio-interview-project/putio-cli
$ docker build -t putio-cli .
$ docker run -it putio-cli -v /path/to/mount:/app/data bash
````

In the last step, mount the directory containing your folders to upload.

## Usage

### Logging In

To login, run: `python -m putio.cli login`.

The default flow for login is OAuth 2.0 Authorization Code flow. In this flow, user will be directed to a URL to authorize.
If the program is running outside Docker, a browser will automatically open, otherwise user will be provided with a link.
Alternatively, users can log in using their usernames and passwords with `python -m putio.cli login --prompt`.

All the options can be found below:
```
Usage: python -m putio.cli login [OPTIONS]

    Login to Put.io.

    `--token` and `--prompt` options are mutually exclusive.

    When no option is given, OAuth 2.0 with Authorization Code flow will be used.

Options:
    --token TOKEN           Use TOKEN to login.
    --prompt                Ask for username and password, and use them to login.
    --dont-save             Don't save the access token, only print it.
    --help                  Show this message and exit.
```

### Uploading Folder

To upload a folder, run `python -m putio.cli upload PATH/TO/FOLDER`.

By default, the folder will be uploaded to the root directory. The target directory can be changed with the option `--target PATH/TO/TARGET`. If a target directory doesn't exist and if it's possible (i.e. there is no file on the path), it will be automatically created.

The name of the uploaded folder can be changed with the option `--name NAME`.

Overwriting existing folders is possible with `-f` or `--force` options. When used, this option will replace existings folders with the same name. This option doesn't overwrite files.

Finally, for more verbosity, `--verbose` option can be used. With this option, every folder created and every file uploaded is written so that progress can be seen. However, it is not recommended to use with folders with lots of small files.

All the options can be found below:
```
Usage: python -m putio.cli upload [OPTIONS] FOLDER

    Upload FOLDER to Put.io.

Arguments:
    FOLDER  [required]

Options:
    --target PATH           Upload FOLDER to PATH.
    --name NAME             Upload FOLDER as NAME.
    -f, --force             Replace folders with the same name.
    --token TOKEN           Use TOKEN as access token.
    --verbose / --quiet     [default: quiet]
    --help                  Show this message and exit.
```

### Authorization

Authorization is handled by the Flask app on [putio-auth](putio-auth). When a user authorizes through the given URL, the access token will be saved alongside a unique ID in Redis for 5 minutes. During this period, CLI app will regularly check with this unique ID to see if the user has authorized yet. Therefore, ideally, user doesn't have to do anything afterwards.

Alternatively, when a username and password is provided, it will return an access token directly.

The authorization server is currently deployed at [putio-auth.herokuapp.com](https://putio-auth.herokuapp.com).

## Advanced Usage

You can change the behaviour of the app through environment variables. To see the current environment variables, see [.env.shared](putio-cli/.env.shared) and [.env.secret.example](putio-cli/.env.secret.example) files. Logging in also utilizes these files.

## Development

For local development, [Tox](https://github.com/tox-dev/tox) is used:
- To run tests, run `tox -e py310`.
- For type checking, run `tox -e mypy`.
- For linting, run `tox -e pylint`.
- For auto-formatting, run `tox -e isort` and `tox -e black`.

For configuration of these tools, see [tox.ini](putio-cli/tox.ini).

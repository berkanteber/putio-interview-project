import os
import uuid
from pathlib import Path

import pytest
from pytest import mark as m

import dotenv

import putio._errors
import putio.auth
import putio.core


dotenv.load_dotenv(".env.secret")
dotenv.load_dotenv(".env.shared")
dotenv.load_dotenv(".env")

os.environ["CURL_CA_BUNDLE"] = ""

PUTIO_ACCESS_TOKEN = os.environ.get("PUTIO_ACCESS_TOKEN")
if not putio.auth.verify_token(PUTIO_ACCESS_TOKEN):
    pytest.skip(
        "Skip integration tests, because no access token is found.",
        allow_module_level=True,
    )


@m.context("While verifying uploads by trying to upload it twice")
class TestIntegraion:
    @m.context("When a folder is uploaded once")
    @m.it("It doesn't upload again because of the name clash")
    def test_upload_folder(self, mocker, fs):
        guid = uuid.uuid4().hex
        path = Path(guid)
        path.mkdir()

        putio.core.upload_folder(
            source=path,
            target=None,
            name=path.name,
            force=False,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        with pytest.raises(putio._errors.NameClashError):
            putio.core.upload_folder(
                source=path,
                target=None,
                name=path.name,
                force=False,
                access_token=PUTIO_ACCESS_TOKEN,
                verbosity=2,
            )

    @m.context("When a folder is uploaded once")
    @m.it("It uploads again if `force` is set to `True`")
    def test_upload_folder_with_force(self, mocker, fs):
        guid = uuid.uuid4().hex
        path = Path(guid)
        path.mkdir()

        putio.core.upload_folder(
            source=path,
            target=None,
            name=path.name,
            force=False,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        putio.core.upload_folder(
            source=path,
            target=None,
            name=path.name,
            force=True,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        with pytest.raises(putio._errors.NameClashError):
            putio.core.upload_folder(
                source=path,
                target=None,
                name=path.name,
                force=False,
                access_token=PUTIO_ACCESS_TOKEN,
                verbosity=2,
            )

    @m.context("When a folder is uploaded once")
    @m.it("It uploads if `name` is set to something else")
    def test_upload_folder_with_name(self, mocker, fs):
        guid = uuid.uuid4().hex
        path = Path(guid)
        path.mkdir()

        putio.core.upload_folder(
            source=path,
            target=None,
            name=path.name,
            force=False,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        new_guid = uuid.uuid4().hex

        putio.core.upload_folder(
            source=path,
            target=None,
            name=new_guid,
            force=False,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        with pytest.raises(putio._errors.NameClashError):
            putio.core.upload_folder(
                source=path,
                target=None,
                name=new_guid,
                force=False,
                access_token=PUTIO_ACCESS_TOKEN,
                verbosity=2,
            )

    @m.context("When a folder with a file is uploaded once")
    @m.it(
        "It doesn't upload to the path of file because of name clash even with `force`"
    )
    def test_upload_folder_with_file(self, mocker, fs):
        guid = uuid.uuid4().hex
        path = Path(guid)
        path.mkdir()
        file_path = path.joinpath("file")
        file_path.touch()

        putio.core.upload_folder(
            source=path,
            target=None,
            name=path.name,
            force=False,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        with pytest.raises(putio._errors.NameClashWithFileError):
            putio.core.upload_folder(
                source=path,
                target=str(file_path),
                name=path.name,
                force=True,
                access_token=PUTIO_ACCESS_TOKEN,
                verbosity=2,
            )

    @m.context("When a non-existing target is given")
    @m.it("It creates missing path components to the target")
    def test_upload_folder_with_file(self, mocker, fs):
        guid = uuid.uuid4().hex
        path = Path(guid)
        inner_path = path.joinpath("a/few/levels/deeper")
        inner_path.mkdir(parents=True, exist_ok=True)
        file_path = inner_path.joinpath("file")
        file_path.touch()

        putio.core.upload_folder(
            source=path,
            target=str(inner_path),
            name=path.name,
            force=False,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        with pytest.raises(putio._errors.NameClashWithFileError):
            putio.core.upload_folder(
                source=path,
                target=str(inner_path.joinpath(file_path)),
                name=path.name,
                force=True,
                access_token=PUTIO_ACCESS_TOKEN,
                verbosity=2,
            )

    @m.context("When a complex folder structure is given")
    @m.it("It uploads all files correctly")
    def test_upload_nested_folders_and_files(self, mocker, fs, capsys):
        """
        `guid`/
            folder-1/
                folder-2/
                    file
                folder-3/
                    folder-4/
                        file
                file-1
                file-2
            file
        """

        guid = uuid.uuid4().hex
        path = Path(guid)
        file_paths = (
            path.joinpath("folder-1/folder-2/file"),
            path.joinpath("folder-1/folder-3/folder-4/file"),
            path.joinpath("folder-1/file-1"),
            path.joinpath("folder-1/file-2"),
            path.joinpath("file"),
        )
        for file_path in file_paths:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()

        putio.core.upload_folder(
            source=path,
            target=None,
            name=path.name,
            force=False,
            access_token=PUTIO_ACCESS_TOKEN,
            verbosity=2,
        )

        captured = capsys.readouterr()
        assert captured.out == (
            f"Folder `{guid}` is created at root folder.\n"
            "Uploading 5 files (0 B).\n"
            f"Folder `{guid}/folder-1` is created.\n"
            f"File `{guid}/file` is uploaded.\n"
            "Uploaded 1 of 5 files (0 B / 0 B).\n"
            f"Folder `{guid}/folder-1/folder-2` is created.\n"
            f"Folder `{guid}/folder-1/folder-3` is created.\n"
            f"File `{guid}/folder-1/file-1` is uploaded.\n"
            "Uploaded 2 of 5 files (0 B / 0 B).\n"
            f"File `{guid}/folder-1/file-2` is uploaded.\n"
            "Uploaded 3 of 5 files (0 B / 0 B).\n"
            f"File `{guid}/folder-1/folder-2/file` is uploaded.\n"
            "Uploaded 4 of 5 files (0 B / 0 B).\n"
            f"Folder `{guid}/folder-1/folder-3/folder-4` is created.\n"
            f"File `{guid}/folder-1/folder-3/folder-4/file` is uploaded.\n"
            "Uploaded 5 of 5 files (0 B / 0 B).\n"
            f"Uploaded `{guid}` (5 files (0 B)).\n"
        )

        for file_path in file_paths:
            with pytest.raises(putio._errors.NameClashWithFileError):
                putio.core.upload_folder(
                    source=path,
                    target=str(file_path),
                    name=path.name,
                    force=True,
                    access_token=PUTIO_ACCESS_TOKEN,
                    verbosity=2,
                )

import os
from pathlib import Path

import pytest
from pytest import mark as m

import putiopy

import putio._errors
import putio.core


class FakeRequest:
    method = None
    url = None


class FakeResponse:
    request = FakeRequest
    status_code = 0


class FakeFile:
    def __init__(self, id=0, file_type=None, name=None):
        self.id = id
        self.file_type = file_type
        self.name = name
        self.size = 0


@m.context("Uhile uploading folder")
@m.context("When creating target")
class TestTargetCreation:
    @m.it("Returns `0` as target ID if there is no target")
    def test_get_target_id_when_none(self, mocker, fs):
        assert putio.core.get_target_id(target=None) == 0

    @m.it("Creates path components as folders if there is no name clash")
    def test_create_components(self, mocker, fs):
        mocker.patch(
            "putio.core.create_folder",
            side_effect=(FakeFile(1), FakeFile(2), FakeFile(3)),
        )

        putio.core.get_target_id(target="path/to/something")

        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("path", parent_id=0),
                mocker.call("to", parent_id=1),
                mocker.call("something", parent_id=2),
            ]
        )

    @m.it("Creates missing path components if there is a name clash with a folder")
    def test_continue_to_create_paths(self, mocker, fs):
        mocker.patch(
            "putio.core.create_folder",
            side_effect=(
                putio._errors.NameClashError("path", 0),
                putio._errors.NameClashError("to", 1),
                FakeFile(3),
            ),
        )

        mocker.patch("putio.core.get_folder", side_effect=(FakeFile(1), FakeFile(2)))

        putio.core.get_target_id(target="path/to/something")

        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("path", parent_id=0),
                mocker.call("to", parent_id=1),
                mocker.call("something", parent_id=2),
            ]
        )

        putio.core.get_folder.assert_has_calls(
            [mocker.call("path", parent_id=0), mocker.call("to", parent_id=1)]
        )

    @m.it("Raises `NameClashWithFileError` if there is a name clash with a file")
    def test_raise_name_clash_with_file_error(self, mocker, fs):
        mocker.patch(
            "putio.core.create_folder",
            side_effect=(
                putio._errors.NameClashError("path", 0),
                putio._errors.NameClashError("to", 1),
                FakeFile(3),
            ),
        )

        mocker.patch("putio.core.get_folder", side_effect=(FakeFile(1), None))

        with pytest.raises(putio._errors.NameClashWithFileError):
            putio.core.get_target_id(target="path/to/something")

        putio.core.create_folder.assert_has_calls(
            [mocker.call("path", parent_id=0), mocker.call("to", parent_id=1)]
        )

        putio.core.get_folder.assert_has_calls(
            [mocker.call("path", parent_id=0), mocker.call("to", parent_id=1)]
        )


@m.context("Uhile uploading folder")
@m.context("When creating folder")
class TestFolderCreation:
    @m.context("If there is a name clash and `force` is set to `False`")
    @m.it("Raises `NameClashWithError` without checking folder type")
    def test_raise_name_clash_error(self, mocker, fs):
        def raise_error(*args, **kwargs):
            raise putiopy.APIError(FakeResponse, "NAME_ALREADY_EXIST", None)

        FakeFile.create_folder = classmethod(raise_error)

        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_folder")
        mocker.spy(putio.core, "create_folder")

        with pytest.raises(putio._errors.NameClashError):
            putio.core.create_folder("folder", parent_id=0, force=False)

        putio.core.get_folder.assert_not_called()

    @m.context("If there is a name clash and `force` is set to `True`")
    @m.it("Raises `NameClashWithFileError` if the name clash is with a file")
    def test_raise_name_clash_with_file_error(self, mocker, fs):
        def raise_error(*args, **kwargs):
            raise putiopy.APIError(FakeResponse, "NAME_ALREADY_EXIST", None)

        FakeFile.create_folder = classmethod(raise_error)

        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_folder", side_effect=(FakeFile(1, "FILE"),))
        mocker.spy(putio.core, "create_folder")

        with pytest.raises(putio._errors.NameClashWithFileError):
            putio.core.create_folder("folder", parent_id=0, force=True)

        putio.core.get_folder.assert_called_once_with("folder", parent_id=0)

    @m.context("If there is a name clash and `force` is set to `True`")
    @m.it("Replaces folder if the name clash is with a folder")
    def test_replace_folder(self, mocker, fs):
        def raise_error_once(cls, *args, **kwargs):
            if cls.flag:
                cls.flag = False
                raise putiopy.APIError(FakeResponse, "NAME_ALREADY_EXIST", None)
            return FakeFile(1)

        FakeFile.flag = True
        FakeFile.create_folder = classmethod(raise_error_once)
        FakeFile.delete = lambda self: None

        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_folder", side_effect=(FakeFile(1, "FOLDER"),))
        mocker.spy(putio.core, "create_folder")

        putio.core.create_folder("folder", parent_id=0, force=True)

        putio.core.get_folder.assert_called_once_with("folder", parent_id=0)
        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("folder", parent_id=0, force=True),
                mocker.call("folder", parent_id=0),
            ]
        )

    @m.it("Quits if there is an API error when creating folder")
    def test_api_error_creating_folder(self, mocker, fs):
        fake_error = putiopy.APIError(None, "SOME_OTHER_ERROR")
        mocker.patch(
            "putio.core.putio_client.File.create_folder", side_effect=fake_error
        )

        with pytest.raises(putio.core.UnknownAPIError):
            putio.core.create_folder("folder", parent_id=0, force=True)


@m.context("Uhile uploading folder")
@m.context("When geting folder")
class TestGettingFolder:
    @m.it("Returns folder if a folder is found")
    def test_success_while_getting_folder(self, mocker, fs):
        fake_file = FakeFile(name="folder", file_type="FOLDER")

        mocker.patch("putio.core.putio_client.File.list", side_effect=([fake_file],))

        mocker.spy(putio.core, "get_folder")

        putio.core.get_folder("folder", parent_id=0)

        assert putio.core.get_folder.spy_return == fake_file

    @m.it("Returns `None` if a folder is not found")
    def test_no_folder_while_getting_folder(self, mocker, fs):
        mocker.patch("putio.core.putio_client.File.list", side_effect=([],))

        mocker.spy(putio.core, "get_folder")

        putio.core.get_folder("folder", parent_id=0)

        assert putio.core.get_folder.spy_return is None

    @m.it("Quits if there is an API error when getting folder")
    def test_api_error_while_getting_folder(self, mocker, fs):
        fake_error = putiopy.APIError(None, "SOME_OTHER_ERROR")
        mocker.patch("putio.core.putio_client.File.list", side_effect=fake_error)

        with pytest.raises(putio.core.UnknownAPIError):
            putio.core.get_folder("folder", parent_id=0)


@m.context("Uhile uploading folder")
@m.context("When uploading file")
class TestUploadingFile:
    @m.it("Returns file if upload is successful")
    def test_success_while_uploading_file(self, mocker, fs):
        fake_file = FakeFile(1)

        mocker.patch("putio.core.putio_client.File.upload", side_effect=(fake_file,))

        mocker.spy(putio.core, "upload_file")

        putio.core.upload_file("file", parent_id=0)

        assert putio.core.upload_file.spy_return == fake_file

    @m.it("Quits if there is an API error when uploading file")
    def test_api_error_while_uploading_file(self, mocker, fs):
        fake_error = putiopy.APIError(None, "SOME_OTHER_ERROR")
        mocker.patch("putio.core.putio_client.File.upload", side_effect=fake_error)

        with pytest.raises(putio.core.UnknownAPIError):
            putio.core.upload_file("folder/file", parent_id=0)


@m.context("Uhile uploading folder")
class TestFolderUpload:
    def set_folder_structure(self):
        """
        folder/                                         ID:  1 (0)
            level-1-1/                                  ID:  2 (1)
                level-2-1/                              ID:  4 (2)
                    level-3-1/                          ID:  8 (4)
                        [empty]
                    level-3-2/                          ID:  9 (4)
                        file                                            ID: 12 (9)
                    file-1                                              ID: 10 (4)
                    file-2                                              ID: 11 (4)
                level-2-2/                              ID:  5 (2)
                    level-3-1/                          ID: 13 (5)
                        file-1                                          ID: 14 (13)
                        file-2                                          ID: 15 (13)
                file-1                                                  ID:  6 (2)
                file-2                                                  ID:  7 (2)
            level-1-2/                                  ID:  3 (1)
                level-2-1/                              ID: 16 (3)
                    file                                                ID: 18 (16)
                file                                                    ID: 17 (3)
        """

        Path("folder/level-1-1/level-2-1/level-3-1").mkdir(parents=True, exist_ok=True)
        Path("folder/level-1-1/level-2-1/level-3-2").mkdir(parents=True, exist_ok=True)
        Path("folder/level-1-1/level-2-1/level-3-2/file").touch()
        Path("folder/level-1-1/level-2-1/file-1").touch()
        Path("folder/level-1-1/level-2-1/file-2").touch()
        Path("folder/level-1-1/level-2-2/level-3-1").mkdir(parents=True, exist_ok=True)
        Path("folder/level-1-1/level-2-2/level-3-1/file-1").touch()
        Path("folder/level-1-1/level-2-2/level-3-1/file-2").touch()
        Path("folder/level-1-1/file-1").touch()
        Path("folder/level-1-1/file-2").touch()
        Path("folder/level-1-2/level-2-1").mkdir(parents=True, exist_ok=True)
        Path("folder/level-1-2/level-2-1/file").touch()
        Path("folder/level-1-2/file").touch()

    @m.context("When a folder is in the working directory")
    @m.it("Uploads a simple folder to root")
    def test_folder_upload_from_cwd_simple(self, mocker, fs, capsys):
        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_target_id", side_effect=(0,))
        mocker.patch("putio.core.create_folder", side_effect=(FakeFile(1),))

        Path("folder").mkdir()

        putio.core.upload_folder(
            source=Path("folder"),
            target=None,
            name="folder",
            force=False,
            access_token="",
            verbosity=True,
        )

        putio.core.create_folder.assert_called_once_with(
            "folder", parent_id=0, force=False
        )

        captured = capsys.readouterr()
        assert captured.out == (
            "Folder `folder` is created at root folder.\nUploaded `folder`.\n"
        )

    @m.context("When a folder is in the working directory")
    @m.it("Uploads a complex folder to root")
    def test_folder_upload_from_cwd(self, mocker, fs, capsys):
        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_target_id", side_effect=(0,))

        mocker.patch(
            "putio.core.create_folder",
            side_effect=(FakeFile(i) for i in (1, 2, 3, 4, 5, 8, 9, 13, 16)),
        )

        mocker.patch(
            "putio.core.upload_file",
            side_effect=(FakeFile(i) for i in (6, 7, 10, 11, 12, 14, 15, 17, 18)),
        )

        self.set_folder_structure()

        putio.core.upload_folder(
            source=Path("folder"),
            target=None,
            name="folder",
            force=False,
            verbosity=True,
            access_token="",
        )

        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("folder", parent_id=0, force=False),
                mocker.call("level-1-1", parent_id=1),
                mocker.call("level-1-2", parent_id=1),
                mocker.call("level-2-1", parent_id=2),
                mocker.call("level-2-2", parent_id=2),
                mocker.call("level-3-1", parent_id=4),
                mocker.call("level-3-2", parent_id=4),
                mocker.call("level-3-1", parent_id=5),
                mocker.call("level-2-1", parent_id=3),
            ]
        )

        # fmt: off
        putio.core.upload_file.assert_has_calls(
            [
                mocker.call("folder/level-1-1/file-1", parent_id=2),
                mocker.call("folder/level-1-1/file-2", parent_id=2),
                mocker.call("folder/level-1-1/level-2-1/file-1", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/file-2", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/level-3-2/file", parent_id=9),
                mocker.call("folder/level-1-1/level-2-2/level-3-1/file-1", parent_id=13),
                mocker.call("folder/level-1-1/level-2-2/level-3-1/file-2", parent_id=13),
                mocker.call("folder/level-1-2/file", parent_id=3),
                mocker.call("folder/level-1-2/level-2-1/file", parent_id=16),
            ]
        )
        # fmt: on

        captured = capsys.readouterr()
        assert captured.out == (
            "Folder `folder` is created at root folder.\n"
            "Uploading 9 files (0 B).\n"
            "Folder `folder/level-1-1` is created.\n"
            "Folder `folder/level-1-2` is created.\n"
            "Folder `folder/level-1-1/level-2-1` is created.\n"
            "Folder `folder/level-1-1/level-2-2` is created.\n"
            "File `folder/level-1-1/file-1` is uploaded.\n"
            "Uploaded 1 of 9 files (0 B / 0 B).\n"
            "File `folder/level-1-1/file-2` is uploaded.\n"
            "Uploaded 2 of 9 files (0 B / 0 B).\n"
            "Folder `folder/level-1-1/level-2-1/level-3-1` is created.\n"
            "Folder `folder/level-1-1/level-2-1/level-3-2` is created.\n"
            "File `folder/level-1-1/level-2-1/file-1` is uploaded.\n"
            "Uploaded 3 of 9 files (0 B / 0 B).\n"
            "File `folder/level-1-1/level-2-1/file-2` is uploaded.\n"
            "Uploaded 4 of 9 files (0 B / 0 B).\n"
            "File `folder/level-1-1/level-2-1/level-3-2/file` is uploaded.\n"
            "Uploaded 5 of 9 files (0 B / 0 B).\n"
            "Folder `folder/level-1-1/level-2-2/level-3-1` is created.\n"
            "File `folder/level-1-1/level-2-2/level-3-1/file-1` is uploaded.\n"
            "Uploaded 6 of 9 files (0 B / 0 B).\n"
            "File `folder/level-1-1/level-2-2/level-3-1/file-2` is uploaded.\n"
            "Uploaded 7 of 9 files (0 B / 0 B).\n"
            "Folder `folder/level-1-2/level-2-1` is created.\n"
            "File `folder/level-1-2/file` is uploaded.\n"
            "Uploaded 8 of 9 files (0 B / 0 B).\n"
            "File `folder/level-1-2/level-2-1/file` is uploaded.\n"
            "Uploaded 9 of 9 files (0 B / 0 B).\n"
            "Uploaded `folder` (9 files (0 B)).\n"
        )

    @m.context("When a folder is not in the working directory")
    @m.it("Uploads a simple folder to root")
    def test_folder_upload_from_not_cwd_simple(self, mocker, fs, capsys):
        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_target_id", side_effect=(0,))
        mocker.patch("putio.core.create_folder", side_effect=(FakeFile(1),))

        Path("folder").mkdir()
        Path("folder/another-folder").mkdir()

        putio.core.upload_folder(
            source=Path("folder/another-folder"),
            target=None,
            name="another-folder",
            force=False,
            access_token="",
            verbosity=True,
        )

        putio.core.create_folder.assert_called_once_with(
            "another-folder", parent_id=0, force=False
        )

        captured = capsys.readouterr()
        assert captured.out == (
            "Folder `another-folder` is created at root folder.\n"
            "Uploaded `another-folder`.\n"
        )

    @m.context("When a folder is not in the working directory")
    @m.it("Uploads a complex folder to root")
    def test_folder_upload_from_not_cwd(self, mocker, fs, capsys):
        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_target_id", side_effect=(0,))

        mocker.patch(
            "putio.core.create_folder",
            side_effect=(FakeFile(i) for i in (2, 4, 5, 8, 9, 13)),
        )

        mocker.patch(
            "putio.core.upload_file",
            side_effect=(FakeFile(i) for i in (6, 7, 10, 11, 12, 14, 15)),
        )

        self.set_folder_structure()

        putio.core.upload_folder(
            source=Path("folder/level-1-1"),
            target=None,
            name="level-1-1",
            force=False,
            access_token="",
            verbosity=True,
        )

        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("level-1-1", parent_id=0, force=False),
                mocker.call("level-2-1", parent_id=2),
                mocker.call("level-2-2", parent_id=2),
                mocker.call("level-3-1", parent_id=4),
                mocker.call("level-3-2", parent_id=4),
                mocker.call("level-3-1", parent_id=5),
            ]
        )

        # fmt: off
        putio.core.upload_file.assert_has_calls(
            [
                mocker.call("folder/level-1-1/file-1", parent_id=2),
                mocker.call("folder/level-1-1/file-2", parent_id=2),
                mocker.call("folder/level-1-1/level-2-1/file-1", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/file-2", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/level-3-2/file", parent_id=9),
                mocker.call("folder/level-1-1/level-2-2/level-3-1/file-1", parent_id=13),
                mocker.call("folder/level-1-1/level-2-2/level-3-1/file-2", parent_id=13),
            ]
        )
        # fmt: on

        captured = capsys.readouterr()
        assert captured.out == (
            "Folder `level-1-1` is created at root folder.\n"
            "Uploading 7 files (0 B).\n"
            "Folder `level-1-1/level-2-1` is created.\n"
            "Folder `level-1-1/level-2-2` is created.\n"
            "File `level-1-1/file-1` is uploaded.\n"
            "Uploaded 1 of 7 files (0 B / 0 B).\n"
            "File `level-1-1/file-2` is uploaded.\n"
            "Uploaded 2 of 7 files (0 B / 0 B).\n"
            "Folder `level-1-1/level-2-1/level-3-1` is created.\n"
            "Folder `level-1-1/level-2-1/level-3-2` is created.\n"
            "File `level-1-1/level-2-1/file-1` is uploaded.\n"
            "Uploaded 3 of 7 files (0 B / 0 B).\n"
            "File `level-1-1/level-2-1/file-2` is uploaded.\n"
            "Uploaded 4 of 7 files (0 B / 0 B).\n"
            "File `level-1-1/level-2-1/level-3-2/file` is uploaded.\n"
            "Uploaded 5 of 7 files (0 B / 0 B).\n"
            "Folder `level-1-1/level-2-2/level-3-1` is created.\n"
            "File `level-1-1/level-2-2/level-3-1/file-1` is uploaded.\n"
            "Uploaded 6 of 7 files (0 B / 0 B).\n"
            "File `level-1-1/level-2-2/level-3-1/file-2` is uploaded.\n"
            "Uploaded 7 of 7 files (0 B / 0 B).\n"
            "Uploaded `level-1-1` (7 files (0 B)).\n"
        )

    @m.context("When a name or a target is specified")
    @m.it("Uploads a folder with a different name to root")
    def test_folder_upload_to_root_with_rename(self, mocker, fs, capsys):
        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_target_id", side_effect=(0,))

        mocker.patch(
            "putio.core.create_folder",
            side_effect=(FakeFile(i) for i in (4, 8, 9)),
        )

        mocker.patch(
            "putio.core.upload_file",
            side_effect=(FakeFile(i) for i in (10, 11, 12)),
        )
        self.set_folder_structure()

        putio.core.upload_folder(
            source=Path("folder/level-1-1/level-2-1"),
            target=None,
            name="new-name",
            force=False,
            access_token="",
            verbosity=True,
        )

        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("new-name", parent_id=0, force=False),
                mocker.call("level-3-1", parent_id=4),
                mocker.call("level-3-2", parent_id=4),
            ]
        )

        putio.core.upload_file.assert_has_calls(
            [
                mocker.call("folder/level-1-1/level-2-1/file-1", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/file-2", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/level-3-2/file", parent_id=9),
            ]
        )

        captured = capsys.readouterr()
        assert captured.out == (
            "Folder `new-name` is created at root folder.\n"
            "Uploading 3 files (0 B).\n"
            "Folder `new-name/level-3-1` is created.\n"
            "Folder `new-name/level-3-2` is created.\n"
            "File `new-name/file-1` is uploaded.\n"
            "Uploaded 1 of 3 files (0 B / 0 B).\n"
            "File `new-name/file-2` is uploaded.\n"
            "Uploaded 2 of 3 files (0 B / 0 B).\n"
            "File `new-name/level-3-2/file` is uploaded.\n"
            "Uploaded 3 of 3 files (0 B / 0 B).\n"
            "Uploaded `level-2-1` as `new-name` (3 files (0 B)).\n"
        )

    @m.context("When a name or a target is specified")
    @m.it("Uploads a folder with the same name to a target")
    def test_folder_to_target_without_rename(self, mocker, fs, capsys):
        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_target_id", side_effect=(1,))
        mocker.patch(
            "putio.core.create_folder",
            side_effect=(FakeFile(i) for i in (4, 8, 9)),
        )

        mocker.patch(
            "putio.core.upload_file",
            side_effect=(FakeFile(i) for i in (10, 11, 12)),
        )

        self.set_folder_structure()

        putio.core.upload_folder(
            source=Path("folder/level-1-1/level-2-1"),
            target="target",
            name="level-2-1",
            force=False,
            access_token="",
            verbosity=True,
        )

        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("level-2-1", parent_id=1, force=False),
                mocker.call("level-3-1", parent_id=4),
                mocker.call("level-3-2", parent_id=4),
            ]
        )

        putio.core.upload_file.assert_has_calls(
            [
                mocker.call("folder/level-1-1/level-2-1/file-1", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/file-2", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/level-3-2/file", parent_id=9),
            ]
        )

        captured = capsys.readouterr()
        assert captured.out == (
            "Folder `level-2-1` is created at `target`.\n"
            "Uploading 3 files (0 B).\n"
            "Folder `level-2-1/level-3-1` is created.\n"
            "Folder `level-2-1/level-3-2` is created.\n"
            "File `level-2-1/file-1` is uploaded.\n"
            "Uploaded 1 of 3 files (0 B / 0 B).\n"
            "File `level-2-1/file-2` is uploaded.\n"
            "Uploaded 2 of 3 files (0 B / 0 B).\n"
            "File `level-2-1/level-3-2/file` is uploaded.\n"
            "Uploaded 3 of 3 files (0 B / 0 B).\n"
            "Uploaded `level-2-1` into `target` (3 files (0 B)).\n"
        )

    @m.context("When a name or a target is specified")
    @m.it("Uploads a folder with a different name to a target")
    def test_folder_upload_to_target_with_rename(self, mocker, fs, capsys):
        mocker.patch("putio.core.putio_client.File", FakeFile)

        mocker.patch("putio.core.get_target_id", side_effect=(1,))
        mocker.patch(
            "putio.core.create_folder",
            side_effect=(FakeFile(i) for i in (4, 8, 9)),
        )

        mocker.patch(
            "putio.core.upload_file",
            side_effect=(FakeFile(i) for i in (10, 11, 12)),
        )

        self.set_folder_structure()

        putio.core.upload_folder(
            source=Path("folder/level-1-1/level-2-1"),
            target="target",
            name="new-name",
            force=False,
            access_token="",
            verbosity=True,
        )

        putio.core.create_folder.assert_has_calls(
            [
                mocker.call("new-name", parent_id=1, force=False),
                mocker.call("level-3-1", parent_id=4),
                mocker.call("level-3-2", parent_id=4),
            ]
        )

        putio.core.upload_file.assert_has_calls(
            [
                mocker.call("folder/level-1-1/level-2-1/file-1", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/file-2", parent_id=4),
                mocker.call("folder/level-1-1/level-2-1/level-3-2/file", parent_id=9),
            ]
        )

        captured = capsys.readouterr()
        assert captured.out == (
            "Folder `new-name` is created at `target`.\n"
            "Uploading 3 files (0 B).\n"
            "Folder `new-name/level-3-1` is created.\n"
            "Folder `new-name/level-3-2` is created.\n"
            "File `new-name/file-1` is uploaded.\n"
            "Uploaded 1 of 3 files (0 B / 0 B).\n"
            "File `new-name/file-2` is uploaded.\n"
            "Uploaded 2 of 3 files (0 B / 0 B).\n"
            "File `new-name/level-3-2/file` is uploaded.\n"
            "Uploaded 3 of 3 files (0 B / 0 B).\n"
            "Uploaded `level-2-1` into `target` as `new-name` (3 files (0 B)).\n"
        )


@m.context("Converting size in bytes to human-readable format")
class TestHumanReadableSize:
    @m.parametrize(
        "input,expected",
        [
            (15_200_000_000, "15.2 GB"),
            (1_400_000_000, "1.4 GB"),
            (800_000_000, "800 MB"),
            (450_120_000, "450 MB"),
            (320_480, "320 KB"),
            (80, "80 B"),
        ],
    )
    @m.it("Converts size correctly")
    def test_gb(self, input, expected):
        assert putio.core.human_size(input) == expected

"""This module provides functions for core actions."""

import os
from pathlib import Path

import putiopy
import typer

from putio._errors import NameClashError
from putio._errors import UnknownAPIError
from putio._types import File
from putio._types import PutioClient


putio_client: PutioClient = putiopy.Client("")


def upload_folder(
    source: Path,
    access_token: str,
) -> None:
    """
    Uploads folder.

    Arguments:
        source: Path of the folder to upload.
        access_token: Access token.

    Raises:
        NameClashError: A file or folder with the same exists.
        NameClashWithFileError: A file with the same name exists.
        UnknownAPIError: An unknown error occured.
    """
    global putio_client  # pylint: disable=[global-statement,invalid-name]
    putio_client = putiopy.Client(access_token, timeout=None)

    source_id = create_folder(source.name, parent_id=0).id
    source_prefix = f"{source.parent}/"

    typer.echo(f"Folder `{source.name}` is created.")

    file_sizes = [path.stat().st_size for path in source.rglob("*") if path.is_file()]
    total_count, total_size = len(file_sizes), sum(file_sizes)
    total_size_human = human_size(total_size)

    if total_count:
        typer.echo(f"Uploading {total_count} files ({total_size_human}).")

    dir_ids = {str(source): source_id}
    uploaded_count = uploaded_size = 0
    for path, folders, files in os.walk(source):
        folders.sort()
        for folder_name in folders:
            folder_path = os.path.join(path, folder_name)
            folder_id = create_folder(folder_name, parent_id=dir_ids[str(path)]).id
            dir_ids[str(folder_path)] = folder_id

            typer.echo(f"Folder {folder_path.removeprefix(source_prefix)} is created.")

        files.sort()
        for file_name in files:
            file_path = os.path.join(path, file_name)
            uploaded_file: File = upload_file(file_path, parent_id=dir_ids[str(path)])

            uploaded_count += 1
            uploaded_size += uploaded_file.size  # pylint: disable=[no-member]

            typer.echo(f"File `{file_path.removeprefix(source_prefix)}` is uploaded.")
            typer.echo(
                f"Uploaded {uploaded_count} of {total_count} files "
                f"({human_size(uploaded_size)} / {total_size_human})."
            )

    files_str = ""
    if total_count:
        files_str = f" ({total_count} files ({total_size_human}))"

    typer.echo(f"Uploaded `{source.name}`{files_str}.")


def create_folder(name: str, *, parent_id: int) -> File:
    """
    Creates a folder in the specified location.

    Arguments:
        name: Name of the folder to create.
        parent_id: Location to create folder in.

    Returns:
        Created folder.

    Raises:
        NameClashError: A file or folder with the same exists.
        UnknownAPIError: An unknown error occured.
    """
    try:
        folder = putio_client.File.create_folder(name, parent_id=parent_id)
    except putiopy.APIError as err:
        if err.type != "NAME_ALREADY_EXIST":
            raise UnknownAPIError(
                context=f"Creating folder `{name}` in `{parent_id}`"
            ) from err

        raise NameClashError(name, parent_id) from None

    return folder


def upload_file(file_path: str, *, parent_id: int = 0) -> File:
    """
    Uploads file to the specified location.

    Arguments:
        file_path: File path.
        parent_id: Location to upload file to.

    Returns:
        Created file.

    Raises:
        UnknownAPIError: Unknown API error.
    """
    try:
        file = putio_client.File.upload(file_path, parent_id=parent_id)
    except putiopy.APIError as err:
        raise UnknownAPIError(
            context=f"Uploading file at `{file_path}` to `{parent_id}`"
        ) from err

    return file


def human_size(size: int) -> str:
    """Converts size in bytes to a human-friendly format."""
    if size > 1_000_000_000:
        return f"{size / 1_000_000_000:.1f} GB"
    if size > 1_000_000:
        return f"{size // 1_000_000} MB"
    if size > 1_000:
        return f"{size // 1_000} KB"
    return f"{size} B"

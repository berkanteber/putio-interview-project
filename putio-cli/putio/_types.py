from typing import Protocol


class PutioClient(Protocol):
    @property
    def File(self) -> "File":
        ...


class File(Protocol):
    @property
    def id(self) -> int:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def file_type(self) -> str:
        ...

    @property
    def size(self) -> int:
        ...

    @classmethod
    def list(cls, parent_id: int = 0) -> list["File"]:
        ...

    @classmethod
    def create_folder(cls, name: str, parent_id: int = 0) -> "File":
        ...

    @classmethod
    def upload(cls, path: str, parent_id: int = 0) -> "File":
        ...

    def delete(self) -> dict[str, (None | int | str)]:
        ...

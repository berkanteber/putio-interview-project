class CLIError(Exception):
    pass


class UnknownAPIError(CLIError):
    def __init__(self, context: str) -> None:
        context = context[0].lower() + context[1:]
        super().__init__(f"An unknown error occured while {context}.")


class NameClashError(CLIError):
    def __init__(
        self,
        name: str,
        parent_id: int,
    ) -> None:
        super().__init__(
            f"A file or folder with name `{name}` in `{parent_id}` already exists.\n\n"
            "Run command with:\n"
            "    `--target TARGET` to upload to a different location\n"
            "    `--name NAME` to upload with a different name\n"
        )


class NameClashWithFileError(CLIError):
    def __init__(self, name: str, parent_id: int) -> None:
        super().__init__(
            f"A file with name `{name}` in `{parent_id}` already exists.\n\n"
            f"Run command with:\n"
            "    `--target TARGET` to upload to a different location\n"
            "    `--name NAME` to upload with a different name"
        )

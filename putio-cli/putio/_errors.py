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
            f"A file or folder with name `{name}` in `{parent_id}` already exists."
        )

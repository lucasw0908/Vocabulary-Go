from beartype import beartype
from typing import Literal


@beartype
def library_checker(_: dict[str, str | list[dict[str, str]]]) -> None: ...

@beartype
def word_checker(_: list[dict[Literal["Chinese", "English"], str]]) -> None: ...

@beartype
def email_checker(_: str) -> None: 
    """Check if the provided email is valid."""
    import re

    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, _):
        raise ValueError("Invalid email format.")
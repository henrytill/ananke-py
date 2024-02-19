"""Input/output utilities."""

from pathlib import Path
from typing import Optional


def file_reader(path: Path) -> Optional[str]:
    """Reads a file into a string.

    Args:
        path: The path to the file to read.

    Returns:
        The contents of the file or None if the file does not exist.
    """
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as file:
        ret = file.read()
        return ret


def file_writer(path: Path, contents: str) -> None:
    """Writes a string into a file.

    Args:
        path: The path to the file to write.
        contents: The contents to write to the file.
    """
    with open(path, "w", encoding="utf-8") as file:
        file.write(contents)

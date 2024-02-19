"""Schema management."""

from pathlib import Path
from typing import Callable, Optional, Self

from .. import io


class SchemaVersion:
    """Schema version.

    Attributes:
        value: The version number.
    """

    value: int

    def __init__(self, value: int) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SchemaVersion):
            return False
        return self.value.__eq__(other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SchemaVersion):
            raise TypeError(f"'<' not supported between instances of 'SchemaVersion' and '{type(other).__name__}'")
        return self.value.__lt__(other.value)

    def __str__(self) -> str:
        return self.value.__str__()

    def __repr__(self) -> str:
        return f"SchemaVersion({self.value!r})"

    @classmethod
    def from_str(cls, version: str) -> Self:
        """Creates a SchemaVersion object from a string.

        Args:
            version: The string.

        Returns:
            The SchemaVersion object.

        Raises:
            ValueError: If the version is in an invalid format.
        """
        return cls(int(version))


CURRENT_SCHEMA_VERSION = SchemaVersion(3)


def get_schema_version(
    schema_file: Path,
    reader: Callable[[Path], Optional[str]] = io.file_reader,
    writer: Callable[[Path, str], None] = io.file_writer,
) -> SchemaVersion:
    """Read the schema version from a file.

    If the file does not exist, write the current schema version to the file.

    Args:
        schema_file: The file to read from and write to.
        reader: A function that reads a file and returns its string representation.
        writer: A function that writes a string to a file.

    Returns:
        The schema version.
    """
    maybe_schema_version_str = reader(schema_file)
    if maybe_schema_version_str is None:
        writer(schema_file, str(CURRENT_SCHEMA_VERSION))
        return CURRENT_SCHEMA_VERSION
    return SchemaVersion.from_str(maybe_schema_version_str)

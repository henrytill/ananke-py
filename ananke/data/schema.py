"""Schema management."""

from pathlib import Path
from typing import Self


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


CURRENT_SCHEMA_VERSION = SchemaVersion(4)


def get_schema_version(schema_file: Path) -> SchemaVersion:
    """Read the schema version from a file.

    If the file does not exist, write the current schema version to the file.

    Args:
        schema_file: The file to read from and write to.
        reader: A function that reads a file and returns its string representation.
        writer: A function that writes a string to a file.

    Returns:
        The schema version.
    """
    if not schema_file.exists():
        schema_file.write_text(str(CURRENT_SCHEMA_VERSION), encoding="utf-8")
        return CURRENT_SCHEMA_VERSION
    schema_version_str = schema_file.read_text(encoding="utf-8")
    return SchemaVersion.from_str(schema_version_str)

"""Schema management."""

from pathlib import Path
from typing import Callable, Optional, Self


class SchemaVersion:
    """Schema version."""

    def __init__(self, version: int) -> None:
        self.version = version

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, SchemaVersion):
            return False
        return self.version.__eq__(value.version)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SchemaVersion):
            raise TypeError(f"'<' not supported between instances of 'SchemaVersion' and '{type(other).__name__}'")
        return self.version.__lt__(other.version)

    @property
    def value(self) -> int:
        """Returns the schema version value."""
        return self.version

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

    def __str__(self) -> str:
        return str(self.version)


CURRENT_SCHEMA_VERSION = SchemaVersion(3)


def get_schema_version(
    schema_file: Path, read: Callable[[Path], Optional[str]], write: Callable[[Path, str], None]
) -> SchemaVersion:
    """Read the schema version from a file.

    If the file does not exist, write the current schema version to the file.

    Args:
        schema_file: The file to read from and write to.
        read: The file reader.
        write: The file writer.

    Returns:
        The schema version.
    """
    maybe_schema_version_str = read(schema_file)
    if maybe_schema_version_str is None:
        write(schema_file, str(CURRENT_SCHEMA_VERSION))
        return CURRENT_SCHEMA_VERSION
    return SchemaVersion.from_str(maybe_schema_version_str)
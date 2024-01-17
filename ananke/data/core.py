"""Core datatypes and related functions."""
import secrets
import string
from datetime import datetime, timezone
from typing import Any, NewType, Optional, Self

KeyId = NewType("KeyId", str)
"""A Cryptographic Key Id."""

Description = NewType("Description", str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType("Identity", str)
"""An identifying value, such as the username in a username/password pair."""

Metadata = NewType("Metadata", str)
"""Contains additional non-specific information for an 'Entry'."""


class Timestamp:
    """A UTC timestamp."""

    def __init__(self, timestamp: datetime) -> None:
        self.timestamp = timestamp

    @classmethod
    def now(cls) -> Self:
        """Creates a Timestamp object with the current time."""
        return cls(datetime.now(timezone.utc))

    @classmethod
    def fromisoformat(cls, timestamp: str) -> Self:
        """Creates a Timestamp object from an ISO 8601 string.

        Args:
            timestamp: The ISO 8601 string.

        Returns:
            The Timestamp object.

        Raises:
            ValueError: If the timestamp is in an invalid format.
        """
        return cls(datetime.fromisoformat(timestamp))

    def isoformat(self) -> str:
        """Returns the timestamp as an ISO 8601 string."""
        return self.timestamp.isoformat().replace("+00:00", "Z")

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Timestamp):
            return False
        return self.timestamp.__eq__(value.timestamp)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Timestamp):
            raise TypeError(f"'<' not supported between instances of 'Timestamp' and '{type(other).__name__}'")
        return self.timestamp.__lt__(other.timestamp)

    @property
    def value(self) -> datetime:
        """Returns the timestamp value."""
        return self.timestamp


class Plaintext(str):
    """A plaintext value."""

    def __new__(cls, value: str) -> Self:
        return super().__new__(cls, value)

    @classmethod
    def random(
        cls,
        length: int,
        use_uppercase: bool = True,
        use_digits: bool = True,
        use_punctuation: bool = False,
    ) -> Self:
        """Generates a random Plaintext of a given length.

        Args:
            length: The length of the generated string.
            use_lowercase: Whether to use lowercase letters.
            use_uppercase: Whether to use uppercase letters.
            use_digits: Whether to use digits.
            use_punctuation: Whether to use punctuation.

        Returns:
            A random Plaintext of the specified length.
        """
        chars = string.ascii_lowercase
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_digits:
            chars += string.digits
        if use_punctuation:
            chars += string.punctuation

        ret = cls("".join(secrets.choice(chars) for _ in range(length)))

        return cls(ret)


def remap_keys(mapping: dict[str, str], data: dict[str, Any]) -> dict[str, Any]:
    """Maps the keys of a dictionary to a new set of keys.

    If a key is not present in the mapping, it is left unchanged.

    Args:
        mapping: A dictionary that maps the old keys to the new keys.
        data: The dictionary to transform.

    Returns:
        A new dictionary where the keys have been replaced according to the mapping.

    Examples:
    >>> remap_keys({"a": "b"}, {"a": 1})
    {'b': 1}
    >>> remap_keys({"a": "b"}, {"a": 1, "c": 2})
    {'b': 1, 'c': 2}
    >>> remap_keys({"a": "b"}, {"c": 1})
    {'c': 1}
    """
    return {mapping.get(key, key): value for key, value in data.items()}


def get_required(d: dict[Any, Any], key: Any, value_type: type) -> Any:
    """Gets a required value from a dictionary.

    Args:
        d: The dictionary to get the value from.
        key: The key to get the value for.
        value_type: The type of the value.

    Returns:
        The value.
    """
    value = d.get(key)
    if value is None:
        raise ValueError(f'Invalid entry format: missing required key "{key}"')
    if not isinstance(value, value_type):
        raise TypeError(f"Invalid {key}: expected a value of type {value_type}")
    return value


def get_optional(d: dict[Any, Any], key: Any, value_type: type) -> Optional[Any]:
    """Gets an optional value from a dictionary.

    Args:
        d: The dictionary to get the value from.
        key: The key to get the value for.
        value_type: The type of the value.

    Returns:
        The value, or None if the key is not present.
    """
    value = d.get(key)
    if value is None:
        return None
    if not isinstance(value, value_type):
        raise TypeError(f"Invalid {key}: expected a value of type {value_type}")
    return value

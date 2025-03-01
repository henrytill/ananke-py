"""Common datatypes and related functions."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, NewType, Optional, Protocol, Self
from uuid import UUID

from ..cipher import KeyId, Plaintext

Description = NewType("Description", str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType("Identity", str)
"""An identifying value, such as the username in a username/password pair."""

Metadata = NewType("Metadata", str)
"""Contains additional non-specific information for an 'Entry'."""


class Timestamp:
    """A UTC timestamp.

    Attributes:
        value: The datetime object.
    """

    value: datetime

    def __init__(self, value: datetime) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timestamp):
            return False
        return self.value.__eq__(other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Timestamp):
            raise TypeError(f"'<' not supported between instances of 'Timestamp' and '{type(other).__name__}'")
        return self.value.__lt__(other.value)

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
        return self.value.isoformat().replace("+00:00", "Z")


class EntryId:
    """Uniquely identifies an 'Entry'.

    Attributes:
        value: The entry id.
    """

    value: UUID

    def __init__(self, value: UUID | str) -> None:
        if isinstance(value, UUID):
            self.value = value
        else:
            self.value = UUID(value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EntryId):
            return False
        return self.value.__eq__(other.value)

    def __str__(self) -> str:
        return self.value.__str__()

    def __repr__(self) -> str:
        return f"EntryId({self.value!r})"

    def __hash__(self) -> int:
        return self.value.__hash__()

    @classmethod
    def generate(cls) -> Self:
        """Generates an EntryId.

        Returns:
            The generated EntryId.
        """
        return cls(uuid.uuid4())


# pylint: disable=unnecessary-ellipsis
class Dictable(Protocol):
    """A protocol for objects that can be converted to and from dictionaries."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Creates an instance from a dictionary."""
        ...

    def to_dict(self) -> Dict[str, str]:
        """Converts the instance to a dictionary."""
        ...


# pylint: disable=too-few-public-methods
class Record:
    """The result of a lookup

    Attributes:
        entry_id: Uniquely identifies the entry.
        key_id: The GPG Key Id used for encryption.
        timestamp: The time the entry was created.
        description: Description of the entry. Can be a URI or a descriptive name.
        identity: Optional identifying value, such as a username.
        plaintext: The plaintext value.
        meta: Optional field for additional non-specific information.
    """

    entry_id: EntryId
    key_id: KeyId
    timestamp: Timestamp
    description: Description
    identity: Optional[Identity]
    meta: Optional[Metadata]

    @property
    def plaintext(self) -> Plaintext:
        """Returns the plaintext associated with this record."""
        raise NotImplementedError()


def remap_keys(mapping: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any]:
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


def get_optional[K, V](d: Dict[K, Any], key: K, value_type: type[V]) -> Optional[V]:
    """Gets an optional value from a dictionary.

    Args:
        d: The dictionary to get the value from.
        key: The key to get the value for.
        value_type: The type of the value.

    Returns:
        The value, or None if the key is not present.

    Examples:
    >>> get_optional({"a": 1}, "a", int)
    1
    >>> get_optional({"a": 1}, "a", str)
    Traceback (most recent call last):
    ...
    TypeError: Invalid a: expected a value of type <class 'str'>
    >>> get_optional({"a": 1}, "b", int) is None
    True
    """
    value = d.get(key)
    if value is None:
        return None
    if not isinstance(value, value_type):
        raise TypeError(f"Invalid {key}: expected a value of type {value_type}")
    return value


def get_required[K, V](d: Dict[K, Any], key: K, value_type: type[V]) -> V:
    """Gets a required value from a dictionary.

    Args:
        d: The dictionary to get the value from.
        key: The key to get the value for.
        value_type: The type of the value.

    Returns:
        The value.

    Examples:
    >>> get_required({"a": 1}, "a", int)
    1
    >>> get_required({"a": 1}, "a", str)
    Traceback (most recent call last):
    ...
    TypeError: Invalid a: expected a value of type <class 'str'>
    >>> get_required({"a": 1}, "b", int)
    Traceback (most recent call last):
    ...
    KeyError: 'Invalid entry: missing required key: b'
    """
    value = get_optional(d, key, value_type)
    if value is None:
        raise KeyError(f"Invalid entry: missing required key: {key}")
    return value

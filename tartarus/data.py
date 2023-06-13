"""Core data structures and related functions."""
import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, NewType, Optional

KeyId = NewType('KeyId', str)
"""Represents a GPG Key Id."""

EntryId = NewType('EntryId', str)
"""Uniquely identifies an 'Entry'."""

Description = NewType('Description', str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType('Identity', str)
"""Represents an identifying value, such as the username in a username/password pair."""

Ciphertext = NewType('Ciphertext', bytes)
"""Holds the encrypted value of an 'Entry'."""

Metadata = NewType('Metadata', str)
"""Contains additional non-specific information for an 'Entry'."""


def parse_timestamp(timestamp: str) -> datetime:
    """Parses a UTC ISO timestamp into a datetime object.

    Args:
        timestamp: The timestamp to parse.

    Returns:
        The parsed datetime object.

    Raises:
        ValueError: If the timestamp is in an invalid format.

    Examples:
        >>> parse_timestamp('2023-06-07T02:58:54.640805116Z')
        datetime.datetime(2023, 6, 7, 2, 58, 54, 640805)

        >>> parse_timestamp('2023-06-07T02:58:54Z')
        datetime.datetime(2023, 6, 7, 2, 58, 54)

        >>> parse_timestamp('2023-06-07T02:58Z')
        datetime.datetime(2023, 6, 7, 2, 58)
    """
    # Remove the Zulu indication
    timestamp = timestamp.rstrip('Z')

    # Separate date and time components
    date, time = timestamp.split('T')

    # Extract time components
    time_components = time.split(':')
    time_components_len = len(time_components)

    if time_components_len not in (2, 3):
        raise ValueError('Invalid timestamp format')

    # Extract time components and update the format string and timestamp_str incrementally
    hours = time_components[0]
    minutes = time_components[1]
    fmt = '%Y-%m-%dT%H:%M'
    timestamp_str = f'{date}T{hours}:{minutes}'

    if time_components_len == 3:  # seconds exist
        seconds = time_components[2]
        if '.' in seconds:
            # seconds include fractional part
            seconds_components = seconds.split('.')
            if len(seconds_components) != 2:
                raise ValueError('Invalid timestamp format')

            seconds = seconds_components[0]
            microseconds = seconds_components[1][:6]
            fmt += ':%S.%f'
            timestamp_str += f':{seconds}.{microseconds}'
        else:
            fmt += ':%S'
            timestamp_str += f':{seconds}'

    # Parse the timestamp string into a datetime object
    return datetime.strptime(timestamp_str, fmt)


class Entry:
    """A record that stores an encrypted value along with associated information.

    Attributes:
        id: Uniquely identifies the entry.
        key_id: Represents the GPG Key Id used for encryption.
        timestamp: The time the entry was created.
        description: Description of the entry. Can be a URI or a descriptive name.
        identity: Optional identifying value, such as a username.
        ciphertext: Holds the encrypted value of the entry.
        meta: Optional field for additional non-specific information.
    """

    entry_id: EntryId
    key_id: KeyId
    timestamp: datetime
    description: Description
    identity: Optional[Identity]
    ciphertext: Ciphertext
    meta: Optional[Metadata]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        entry_id: EntryId,
        key_id: KeyId,
        timestamp: datetime,
        description: Description,
        identity: Optional[Identity],
        ciphertext: Ciphertext,
        meta: Optional[Metadata],
    ):
        self.entry_id = entry_id
        self.key_id = key_id
        self.timestamp = timestamp
        self.description = description
        self.identity = identity
        self.ciphertext = ciphertext
        self.meta = meta

    def __hash__(self) -> int:
        return hash(self.entry_id)

    @classmethod
    def from_dict(cls, data: Dict[Any, Any]) -> Optional['Entry']:
        """Creates an 'Entry' from a dictionary.

        Args:
            data: The dictionary to create the 'Entry' from.

        Returns:
            The created 'Entry'.
        """
        data = {k.lower(): v for k, v in data.items()}
        try:
            return cls(
                entry_id=EntryId(data['id']),
                key_id=KeyId(data['keyid']),
                timestamp=parse_timestamp(data['timestamp']),
                description=Description(data['description']),
                identity=Identity(data['identity']) if 'identity' in data else None,
                ciphertext=Ciphertext(base64.b64decode(data['ciphertext'])),
                meta=Metadata(data['meta']) if 'meta' in data else None,
            )
        except KeyError:
            return None

    def to_ordered_dict(self) -> Dict[str, Any]:
        """Converts the 'Entry' to an ordered dictionary.

        Returns:
            The converted 'Entry'.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'id': self.entry_id,
            'keyid': self.key_id,
            'description': self.description,
            'identity': self.identity,
            'ciphertext': self.ciphertext,
            'meta': self.meta,
        }


@dataclass
class Entries:
    """A collection of 'Entry' objects.

    Attributes:
        entries: The collection of entries.
    """

    entries: list[Entry]

    @classmethod
    def from_json(cls, data: str) -> 'Entries':
        """Creates an 'Entries' object from a JSON string.

        Args:
            data: The JSON string to create the 'Entries' object from.

        Returns:
            The created 'Entries' object.
        """
        raw_entries: list[Dict[str, Any]] = json.loads(data)

        ret: list[Entry] = []

        for item in raw_entries:
            maybe_entry = Entry.from_dict(item)
            if maybe_entry is not None:
                ret.append(maybe_entry)

        return cls(ret)

    def sort(self) -> None:
        """Sorts the entries by timestamp."""
        self.entries.sort(key=lambda entry: entry.timestamp, reverse=True)

    def lookup(self, description: Description, identity: Optional[Identity] = None) -> list[Entry]:
        """Searches for entries that match the provided description and identity.

        Matching is fuzzy and case-insensitive.

        Args:
            description: The description to search for.
            identity: Optional identity to search for.

        Returns:
            A list of entries that match the provided description and identity.
        """
        return [
            entry
            for entry in self.entries
            if description.lower() in entry.description.lower()
            and (identity is None or (entry.identity is not None and identity.lower() in entry.identity.lower()))
        ]


Plaintext = NewType('Plaintext', str)
"""Holds a plaintext value."""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import NewType, Optional

KeyId = NewType('KeyId', str)
"""Represents a GPG Key Id."""


class Backend(Enum):
    """
    Represents the backend used to store the data.
    """

    SQLITE = 1
    JSON = 2


@dataclass
class Config:
    """
    A configuration object.
    """

    data_dir: Path
    """The directory where the data is stored."""
    backend: Backend
    """The backend used to store the data."""
    gpg_key_id: KeyId
    """The GPG Key Id used for encryption."""
    allow_multiple_keys: bool
    """Whether or not to allow multiple GPG keys to be used for encryption."""


Id = NewType('Id', str)
"""Uniquely identifies an 'Entry'."""

Description = NewType('Description', str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType('Identity', str)
"""Represents an identifying value, such as the username in a username/password pair."""

Ciphertext = NewType('Ciphertext', bytes)
"""Holds the encrypted value of an 'Entry'."""

Metadata = NewType('Metadata', str)
"""Contains additional non-specific information for an 'Entry'."""


@dataclass
class Entry:
    """
    A record that stores an encrypted value along with associated information.

    Attributes:
        id: Uniquely identifies the entry.
        key_id: Represents the GPG Key Id used for encryption.
        timestamp: The time the entry was created.
        description: Description of the entry. Can be a URI or a descriptive name.
        identity: Optional identifying value, such as a username.
        ciphertext: Holds the encrypted value of the entry.
        meta: Optional field for additional non-specific information.
    """

    id: Id
    key_id: KeyId
    timestamp: datetime
    description: Description
    identity: Optional[Identity]
    ciphertext: Ciphertext
    meta: Optional[Metadata]

    @classmethod
    def from_dict(cls, data: dict) -> Optional['Entry']:
        """
        Creates an 'Entry' from a dictionary.

        Args:
            data: The dictionary to create the 'Entry' from.

        Returns:
            The created 'Entry'.
        """
        data = {k.lower(): v for k, v in data.items()}
        try:
            return cls(
                id=Id(data['id']),
                key_id=KeyId(data['keyid']),
                timestamp=datetime.fromisoformat(data['timestamp']),
                description=Description(data['description']),
                identity=Identity(data['identity']) if 'identity' in data else None,
                ciphertext=Ciphertext(data['ciphertext']),
                meta=Metadata(data['meta']) if 'meta' in data else None,
            )
        except KeyError:
            return None

    def to_string(self, verbosity: int) -> str:
        """
        Converts the 'Entry' to a string.

        Args:
            verbosity: The verbosity level of the output.

        Returns:
            The 'Entry' as a string.
        """
        return f'{self.ciphertext}'


@dataclass
class Entries:
    """
    A collection of 'Entry' objects.

    Attributes:
        entries: The collection of entries.
    """

    entries: list[Entry]

    @classmethod
    def __from_dicts(cls, data: list[dict]) -> 'Entries':
        """
        Creates an 'Entries' object from a list of dictionaries.

        Args:
            data: The list of dictionaries to create the 'Entries' object from.

        Returns:
            The created 'Entries' object.
        """
        ret = [Entry.from_dict(entry) for entry in data if Entry.from_dict(entry) is not None]
        return cls(ret)

    @classmethod
    def from_json(cls, data: str) -> 'Entries':
        """
        Creates an 'Entries' object from a JSON string.

        Args:
            data: The JSON string to create the 'Entries' object from.

        Returns:
            The created 'Entries' object.
        """
        object = json.loads(data)
        if isinstance(object, list):
            return cls.__from_dicts(object)
        else:
            return cls([])

    def lookup(self, description: Description, identity: Optional[Identity] = None) -> list[Entry]:
        """
        Searches for entries that match the provided description and identity.

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
            and (identity is None or identity.lower() in entry.identity.lower())
        ]


Plaintext = NewType('Plaintext', str)
"""Holds a plaintext value."""

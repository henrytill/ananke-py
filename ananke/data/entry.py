"""Module for the 'Entry' class and related types."""

import functools
from typing import Any, Optional, Self, Tuple

from . import common
from .common import Ciphertext, Description, EntryId, Identity, KeyId, Metadata, Timestamp


class Entry:
    """A record that stores an encrypted value along with associated information.

    Attributes:
        entry_id: Uniquely identifies the entry.
        key_id: The GPG Key Id used for encryption.
        timestamp: The time the entry was created.
        description: Description of the entry. Can be a URI or a descriptive name.
        identity: Optional identifying value, such as a username.
        ciphertext: The encrypted value.
        meta: Optional field for additional non-specific information.
    """

    entry_id: EntryId
    key_id: KeyId
    timestamp: Timestamp
    description: Description
    identity: Optional[Identity]
    ciphertext: Ciphertext
    meta: Optional[Metadata]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        entry_id: EntryId,
        key_id: KeyId,
        timestamp: Timestamp,
        description: Description,
        identity: Optional[Identity],
        ciphertext: Ciphertext,
        meta: Optional[Metadata],
    ) -> None:
        self.entry_id = entry_id
        self.key_id = key_id
        self.timestamp = timestamp
        self.description = description
        self.identity = identity
        self.ciphertext = ciphertext
        self.meta = meta

    def __repr__(self) -> str:
        return f"Entry({self.entry_id})"

    def __hash__(self) -> int:
        return hash(self.entry_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entry):
            return False
        return (
            self.timestamp == other.timestamp
            and self.entry_id == other.entry_id
            and self.key_id == other.key_id
            and self.description == other.description
            and self.identity == other.identity
            and self.ciphertext == other.ciphertext
            and self.meta == other.meta
        )

    def normalize(self) -> Self:
        """Regenerates the 'entry_id' attribute.

        Returns:
            The 'Entry'
        """
        self.entry_id = self.fresh_id()
        return self

    def fresh_id(self) -> EntryId:
        """Generates a fresh 'EntryId'.

        Returns:
            The fresh 'EntryId'
        """
        return EntryId.generate(
            key_id=self.key_id,
            timestamp=self.timestamp,
            description=self.description,
            maybe_identity=self.identity,
        )

    @classmethod
    def from_dict(cls, data: dict[Any, Any]) -> Self:
        """Creates an 'Entry' from a dictionary.

        Args:
            data: The dictionary to create the 'Entry' from.

        Returns:
            The created 'Entry'.
        """
        # Get required keys
        id_str: str = common.get_required(data, "id", str)
        key_id_str: str = common.get_required(data, "key_id", str)
        timestamp_str: str = common.get_required(data, "timestamp", str)
        description_str: str = common.get_required(data, "description", str)
        ciphertext_str: str = common.get_required(data, "ciphertext", str)

        # Get optional keys
        maybe_identity: Optional[str] = common.get_optional(data, "identity", str)
        maybe_meta: Optional[str] = common.get_optional(data, "meta", str)

        # Validate timestamp
        try:
            timestamp = Timestamp.fromisoformat(timestamp_str)
        except ValueError as err:
            raise ValueError("Invalid timestamp format") from err

        # Validate ciphertext
        try:
            ciphertext = Ciphertext.from_base64(ciphertext_str)
        except ValueError as err:
            raise ValueError("Invalid ciphertext format") from err

        return cls(
            entry_id=EntryId(id_str),
            key_id=KeyId(key_id_str),
            timestamp=timestamp,
            description=Description(description_str),
            identity=Identity(maybe_identity) if maybe_identity else None,
            ciphertext=ciphertext,
            meta=Metadata(maybe_meta) if maybe_meta else None,
        )

    @classmethod
    def from_tuple(cls, row: Tuple[Any, Any, Any, Any, Any, Any, Any]) -> Self:
        """Creates an 'Entry' from a tuple.

        Args:
            data: The tuple to create the 'Entry' from.

        Returns:
            The created 'Entry'.
        """
        entry_dict = {
            "id": row[0],
            "key_id": row[1],
            "timestamp": row[2],
            "description": row[3],
            "ciphertext": row[5],
        }
        if row[4]:
            entry_dict["identity"] = row[4]
        if row[6]:
            entry_dict["meta"] = row[6]
        return cls.from_dict(entry_dict)

    def to_dict(self) -> dict[str, str]:
        """Converts the 'Entry' to a dictionary.

        Returns:
            The converted 'Entry'.
        """
        ret = {
            "timestamp": self.timestamp.isoformat(),
            "id": str(self.entry_id),
            "key_id": self.key_id,
            "description": self.description,
            "ciphertext": self.ciphertext.to_base64(),
        }
        if self.identity is not None:
            ret["identity"] = self.identity
        if self.meta is not None:
            ret["meta"] = self.meta
        return ret


CAMEL_TO_SNAKE = {
    # camelCase
    "timestamp": "timestamp",
    "id": "id",
    "keyId": "key_id",
    "description": "description",
    "identity": "identity",
    "ciphertext": "ciphertext",
    "meta": "meta",
    # PascalCase
    "Timestamp": "timestamp",
    "Id": "id",
    "KeyId": "key_id",
    "Description": "description",
    "Identity": "identity",
    "Ciphertext": "ciphertext",
    "Meta": "meta",
}

SNAKE_TO_CAMEL = {
    "timestamp": "timestamp",
    "id": "id",
    "key_id": "keyId",
    "description": "description",
    "identity": "identity",
    "ciphertext": "ciphertext",
    "meta": "meta",
}


remap_keys_camel_to_snake = functools.partial(common.remap_keys, CAMEL_TO_SNAKE)
remap_keys_snake_to_camel = functools.partial(common.remap_keys, SNAKE_TO_CAMEL)

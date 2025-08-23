"""Module for the 'SecureEntry' class and related types."""

# pylint: disable=duplicate-code
import functools
from dataclasses import dataclass
from typing import Any, Dict, Optional, Self
from uuid import UUID

from ..cipher import KeyId, Plaintext
from . import common
from .common import Description, EntryId, Identity, Metadata, Record, Timestamp


@dataclass
class SecureIndexElement:
    """A record used to index collections of SecureEntry.

    Attributes:
        entry_id: Uniquely identifies the entry.
        key_id: The GPG Key Id used for encryption.
        description: Description of the entry. Can be a URI or a descriptive name.
    """

    entry_id: EntryId
    key_id: KeyId
    description: Description

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Creates a 'SecureIndexElement' from a dictionary.

        Args:
            data: The dictionary to create the 'SecureIndexElement' from.

        Returns:
            The created 'SecureIndexElement'.
        """
        # Get required keys
        id_str = common.get_required(data, "entry_id", str)
        key_id_str = common.get_required(data, "key_id", str)
        description_str = common.get_required(data, "description", str)

        # Validate entry id
        try:
            uuid = UUID(id_str)
        except ValueError as err:
            raise ValueError("Invalid id format") from err

        return cls(
            entry_id=EntryId(uuid),
            key_id=KeyId(key_id_str),
            description=Description(description_str),
        )

    def to_dict(self) -> Dict[str, str]:
        """Converts the 'SecureIndexElement' to a dictionary.

        Returns:
            The converted 'SecureIndexElement'.
        """
        return {
            "entry_id": str(self.entry_id),
            "key_id": self.key_id,
            "description": self.description,
        }


# pylint: disable=too-many-instance-attributes
class SecureEntry(Record):
    """A record that stores a plaintext value along with associated information."""

    def __init__(
        self,
        entry_id: EntryId,
        key_id: KeyId,
        timestamp: Timestamp,
        description: Description,
        identity: Optional[Identity],
        plaintext: Plaintext,
        meta: Optional[Metadata],
    ) -> None:
        super().__init__(
            entry_id=entry_id,
            key_id=key_id,
            timestamp=timestamp,
            description=description,
            identity=identity,
            meta=meta,
        )
        self._plaintext = plaintext

    def __repr__(self) -> str:
        return f"SecureEntry({self.entry_id})"

    def __hash__(self) -> int:
        return hash(self.entry_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecureEntry):
            return False
        return (
            self.timestamp == other.timestamp
            and self.entry_id == other.entry_id
            and self.key_id == other.key_id
            and self.description == other.description
            and self.identity == other.identity
            and self.plaintext == other.plaintext
            and self.meta == other.meta
        )

    def __lt__(self, other: Self) -> bool:
        return self.timestamp.__lt__(other.timestamp)

    @property
    def plaintext(self) -> Plaintext:
        return self._plaintext

    @plaintext.setter
    def plaintext(self, plaintext: Plaintext) -> None:
        self._plaintext = plaintext

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Creates a 'SecretEntry' from a dictionary.

        Args:
            data: The dictionary to create the 'SecretEntry' from.

        Returns:
            The created 'SecretEntry'.
        """
        # Get required keys
        id_str = common.get_required(data, "id", str)
        key_id_str = common.get_required(data, "key_id", str)
        timestamp_str = common.get_required(data, "timestamp", str)
        description_str = common.get_required(data, "description", str)
        plaintext_str = common.get_required(data, "plaintext", str)

        # Get optional keys
        maybe_identity = common.get_optional(data, "identity", str)
        maybe_meta = common.get_optional(data, "meta", str)

        # Validate entry id
        try:
            uuid = UUID(id_str)
        except ValueError as err:
            raise ValueError("Invalid id format") from err

        # Validate timestamp
        try:
            timestamp = Timestamp.fromisoformat(timestamp_str)
        except ValueError as err:
            raise ValueError("Invalid timestamp format") from err

        return cls(
            entry_id=EntryId(uuid),
            key_id=KeyId(key_id_str),
            timestamp=timestamp,
            description=Description(description_str),
            identity=Identity(maybe_identity) if maybe_identity else None,
            plaintext=Plaintext(plaintext_str),
            meta=Metadata(maybe_meta) if maybe_meta else None,
        )

    def to_dict(self) -> Dict[str, str]:
        """Converts the 'SecretEntry' to a dictionary.

        Returns:
            The converted 'SecretEntry'.
        """
        ret = {
            "timestamp": self.timestamp.isoformat(),
            "id": str(self.entry_id),
            "key_id": self.key_id,
            "description": self.description,
            "plaintext": str(self.plaintext),
        }
        if self.identity is not None:
            ret["identity"] = self.identity
        if self.meta is not None:
            ret["meta"] = self.meta
        return ret

    def update(self) -> Self:
        """Updates the timestamp of an 'Entry'.

        Returns:
            The 'Entry'
        """
        self.timestamp = Timestamp.now()
        return self

    def to_index_element(self) -> SecureIndexElement:
        """Converts the 'SecureEntry' to a 'SecureIndexElement'.

        Returns:
            The converted 'SecureIndexElement'.
        """
        return SecureIndexElement(
            entry_id=self.entry_id,
            key_id=self.key_id,
            description=self.description,
        )


# TODO: Consolidate
CAMEL_TO_SNAKE = {
    # camelCase
    "timestamp": "timestamp",
    "id": "id",
    "entryId": "entry_id",
    "keyId": "key_id",
    "description": "description",
    "identity": "identity",
    "plaintext": "plaintext",
    "meta": "meta",
    # PascalCase
    "Timestamp": "timestamp",
    "Id": "id",
    "KeyId": "key_id",
    "Description": "description",
    "Identity": "identity",
    "Plaintext": "plaintext",
    "Meta": "meta",
}

SNAKE_TO_CAMEL = {
    "timestamp": "timestamp",
    "id": "id",
    "entry_id": "entryId",
    "key_id": "keyId",
    "description": "description",
    "identity": "identity",
    "plaintext": "plaintext",
    "meta": "meta",
}


remap_keys_camel_to_snake = functools.partial(common.remap_keys, CAMEL_TO_SNAKE)
remap_keys_snake_to_camel = functools.partial(common.remap_keys, SNAKE_TO_CAMEL)

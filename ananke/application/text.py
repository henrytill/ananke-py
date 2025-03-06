from pathlib import Path
from typing import List, Optional

from ..cipher import Plaintext
from ..cipher.gpg import Text
from ..config import Backend, Config
from ..data import Description, Identity, Metadata, Record, SecureIndexElement
from . import common
from .common import Application, Target


class TextApplication(Application):
    """A Text Application"""

    def __init__(self, config: Config) -> None:
        assert config.backend == Backend.TEXT

        self.config = config
        self.config.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.cipher = Text(self.config.key_id)
        self.elements: List[SecureIndexElement] = []
        if self.config.data_file.exists():
            self.elements += common.read(SecureIndexElement, self.config.data_file, self.cipher)

    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Optional[Identity] = None,
        maybe_meta: Optional[Metadata] = None,
    ) -> None:
        raise NotImplementedError

    def lookup(
        self,
        description: Description,
        maybe_identity: Optional[Identity] = None,
    ) -> List[Record]:
        raise NotImplementedError

    def modify(
        self,
        target: Target,
        maybe_description: Optional[Description],
        maybe_identity: Optional[Identity],
        maybe_plaintext: Optional[Plaintext],
        maybe_meta: Optional[Metadata],
    ) -> None:
        raise NotImplementedError

    def remove(self, target: Target) -> None:
        raise NotImplementedError

    def import_entries(self, path: Optional[Path]) -> None:
        raise NotImplementedError

    def export_entries(self, path: Optional[Path]) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

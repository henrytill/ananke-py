from pathlib import Path
from typing import Optional, Tuple

from ..config import Config
from ..data import Description, Entry, Identity, Metadata, Plaintext
from . import common
from .common import Application, Target


class JsonApplication(Application):
    """A JSON Application"""

    config: Config
    entries: list[Entry]

    def __init__(self, config: Config) -> None:
        self.config = config
        self.entries = []

        if self.config.data_file.exists():
            self.entries += common.read(self.config.data_file)

    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Optional[Identity] = None,
        maybe_meta: Optional[Metadata] = None,
    ) -> None:
        return

    def lookup(
        self, description: Description, maybe_identity: Optional[Identity] = None
    ) -> list[Tuple[Entry, Plaintext]]:
        ret: list[Tuple[Entry, Plaintext]] = []
        return ret

    # pylint: disable=too-many-arguments
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

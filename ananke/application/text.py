import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, cast

from .. import data
from ..cipher import ArmoredCiphertext, Plaintext
from ..cipher.gpg import Text
from ..config import Backend, Config
from ..data import Description, Dictable, Identity, Metadata, Record, SecureIndexElement
from .common import Application, Target


class TextApplication(Application):
    """A Text Application"""

    config: Config
    cipher: Text
    elements: List[SecureIndexElement]

    def __init__(self, config: Config) -> None:
        assert config.backend == Backend.TEXT

        self.config = config
        self.cipher = Text(self.config.key_id)
        self.config.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.elements = []

        if self.config.data_file.exists():
            self.elements += read(SecureIndexElement, self.cipher, self.config.data_file)

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


T = TypeVar("T", bound=Dictable)


def read(cls: Type[T], cipher: Text, path: Path) -> List[T]:
    """Reads objects from a text file"""
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist")
    text = path.read_text(encoding="utf-8")
    json_data = cipher.decrypt(ArmoredCiphertext(text)).value
    parsed = json.loads(json_data, object_hook=data.remap_keys_camel_to_snake)
    if not isinstance(parsed, list):
        raise TypeError("Expected a list")
    ret: List[T] = []
    for item in cast(List[object], parsed):
        if not isinstance(item, dict):
            raise TypeError("Expected a dictionary")
        ret.append(cls.from_dict(cast(Dict[str, Any], item)))
    return ret


def write(cipher: Text, path: Path, plaintext: Plaintext) -> None:
    """Writes plaintext to a text file"""
    armored = cipher.encrypt(plaintext)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(armored, encoding="utf-8")

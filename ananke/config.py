"""Configuration."""

import configparser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Optional, Self

from .cipher import KeyId


# pylint: disable=invalid-name
@dataclass(frozen=True)
class Env:
    """Environment variables used for configuration."""

    CONFIG_DIR: str = "ANANKE_CONFIG_DIR"
    DATA_DIR: str = "ANANKE_DATA_DIR"
    BACKEND: str = "ANANKE_BACKEND"
    KEY_ID: str = "ANANKE_KEY_ID"
    ALLOW_MULTIPLE_KEYS: str = "ANANKE_ALLOW_MULTIPLE_KEYS"


class OsFamily(Enum):
    """The operating system family."""

    POSIX = 1
    NT = 2

    @classmethod
    def from_str(cls, os_family_str: str) -> "OsFamily":
        """Creates an OsFamily from a string.

        Args:
            os_family_str: The string to create the OsFamily from.

        Returns:
            The created OsFamily.
        """
        match os_family_str:
            case "posix":
                return cls.POSIX
            case "nt":
                return cls.NT
            case _:
                raise ValueError(f"Invalid OsFamily string: {os_family_str}")

    def __str__(self) -> str:
        match self:
            case OsFamily.POSIX:
                return "posix"
            case OsFamily.NT:
                return "nt"


class Backend(Enum):
    """The backend used to store application data."""

    SQLITE = 1
    JSON = 2
    TEXT = 3

    @classmethod
    def from_str(cls, backend_str: str) -> "Backend":
        """Creates a Backend from a string.

        Args:
            backend_str: The string to create the Backend from.

        Returns:
            The created Backend.
        """
        match backend_str:
            case "sqlite":
                return cls.SQLITE
            case "json":
                return cls.JSON
            case "text":
                return cls.TEXT
            case _:
                raise ValueError(f"Invalid Backend string: {backend_str}")

    def __str__(self) -> str:
        match self:
            case Backend.SQLITE:
                return "sqlite"
            case Backend.JSON:
                return "json"
            case Backend.TEXT:
                return "text"

    @classmethod
    def default(cls) -> "Backend":
        """Returns default Backend."""
        return cls.TEXT


@dataclass(frozen=True)
class Config:
    """A configuration object.

    Attributes:
        data_dir: The directory where the data is stored.
        backend: The backend used to store the data.
        key_id: The key ID used to encrypt the data.
        allow_multiple_keys: Whether multiple keys are allowed to encrypt the data.
    """

    config_dir: Path
    data_dir: Path
    backend: Backend
    key_id: KeyId
    allow_multiple_keys: bool

    @property
    def config_file(self) -> Path:
        """Returns the path to the configuration file."""
        return self.config_dir / "ananke.ini"

    @property
    def db_dir(self) -> Path:
        """Returns the path to db directory."""
        return self.data_dir / "db"

    @property
    def data_file(self) -> Path:
        """Returns the path to the data file."""
        match self.backend:
            case Backend.JSON:
                return self.db_dir / "data.json"
            case Backend.SQLITE:
                return self.db_dir / "db.sqlite"
            case Backend.TEXT:
                return self.db_dir / "index.asc"

    @property
    def schema_file(self) -> Path:
        """Returns the path to the schema file."""
        return self.data_dir / "db" / "schema"

    def pretty_print(self) -> str:
        """Returns a pretty-printed string."""
        ret = f"""\
config_dir = {self.config_dir}
data_dir = {self.data_dir}
backend = {self.backend}
key_id = {self.key_id}
allow_multiple_keys = {self.allow_multiple_keys}\
"""
        return ret


def _file_reader(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist")
    return path.read_text(encoding="utf-8")


class ConfigBuilder:
    """A configuration builder."""

    config_dir: Optional[Path]
    data_dir: Optional[Path]
    backend: Optional[Backend]
    key_id: Optional[KeyId]
    allow_multiple_keys: Optional[bool]

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        backend: Optional[Backend] = None,
        key_id: Optional[KeyId] = None,
        allow_multiple_keys: Optional[bool] = None,
    ) -> None:
        self.config_dir = config_dir
        self.data_dir = data_dir
        self.backend = backend
        self.key_id = key_id
        self.allow_multiple_keys = allow_multiple_keys

    @property
    def config_file(self) -> Optional[Path]:
        """Returns the path to a possible configuration file, if one can be determined."""
        return (self.config_dir / "ananke.ini") if self.config_dir else None

    def with_env(self, env: Mapping[str, str]) -> Self:
        """Updates attributes from environment variables.

        Args:
            env: An environment. Typically, this is `os.environ`.

        Returns:
            The updated configuration.
        """
        config_dir = env.get(Env.CONFIG_DIR)
        if config_dir is not None:
            self.config_dir = Path(config_dir)

        data_dir = env.get(Env.DATA_DIR)
        if data_dir is not None:
            self.data_dir = Path(data_dir)

        backend = env.get(Env.BACKEND)
        if backend is not None:
            self.backend = Backend.from_str(backend)

        key_id = env.get(Env.KEY_ID)
        if key_id is not None:
            self.key_id = KeyId(key_id)

        allow_multiple_keys = env.get(Env.ALLOW_MULTIPLE_KEYS)
        if allow_multiple_keys is not None:
            try:
                self.allow_multiple_keys = bool(_strtobool(allow_multiple_keys))
            except ValueError:
                self.allow_multiple_keys = False

        return self

    def with_config(self, reader: Callable[[Path], str] = _file_reader) -> Self:
        """Updates attributes from the string representation of a configuration file.

        Args:
            config: The string representation of a configuration file.
            reader: A function that reads a file and returns its string representation.

        Returns:
            The updated configuration.
        """
        if self.config_dir is None:
            raise ValueError("config_dir is not set")

        config_file = self.config_dir / "ananke.ini"
        config_str = reader(config_file)

        config_parser = configparser.ConfigParser()
        config_parser.read_string(config_str)

        data_dir = config_parser.get("data", "dir", fallback=None)
        if data_dir is not None:
            self.data_dir = Path(data_dir)

        backend = config_parser.get("data", "backend", fallback=None)
        if backend is not None:
            self.backend = Backend.from_str(backend)

        key_id = config_parser.get("gpg", "key_id", fallback=None)
        if key_id is not None:
            self.key_id = KeyId(key_id)

        allow_multiple_keys = config_parser.getboolean("gpg", "allow_multiple_keys", fallback=None)
        if allow_multiple_keys is not None:
            self.allow_multiple_keys = bool(allow_multiple_keys)

        return self

    def with_defaults(self, os_family: OsFamily, env: Mapping[str, str]) -> Self:
        """Updates unset attributes with default values.

        Args:
            os_family: The operating system family.
            env: An environment. Typically, this is `os.environ`.

        Returns:
            The updated configuration.
        """
        config_dir = env.get(Env.CONFIG_DIR)
        if config_dir is not None:
            self.config_dir = Path(config_dir)

        if self.config_dir is None:
            self.config_dir = _get_config_dir(os_family, env)

        if self.data_dir is None:
            self.data_dir = _get_data_dir(os_family, env)

        if self.allow_multiple_keys is None:
            self.allow_multiple_keys = False

        return self

    def build(self) -> Config:
        """Builds a configuration object.

        Returns:
            The configuration object.
        """
        if self.config_dir is None:
            raise ValueError("config_dir is not set")

        if self.data_dir is None:
            raise ValueError("data_dir is not set")

        if self.backend is None:
            raise ValueError("backend is not set")

        if self.key_id is None:
            raise ValueError("key_id is not set")

        if self.allow_multiple_keys is None:
            raise ValueError("allow_multiple_keys is not set")

        # Create a configuration object
        config = Config(
            config_dir=self.config_dir,
            data_dir=self.data_dir,
            backend=self.backend,
            key_id=self.key_id,
            allow_multiple_keys=self.allow_multiple_keys,
        )

        # Return the configuration
        return config

    def ini(self) -> str:
        """Returns the given configuration formatted as the contents of an ini file."""
        return f"""\
[data]
backend={self.backend}
dir={self.data_dir}
[gpg]
key_id={self.key_id}
allow_multiple_keys={str(self.allow_multiple_keys).lower()}
"""


def _get_config_dir(os_family: OsFamily, env: Mapping[str, str]) -> Path:
    """Returns the path to the configuration directory.

    Args:
        os_family: The operating system family.
        env: An environment. Typically, this is `os.environ`.

    Returns:
        The path to the configuration directory.
    """
    if os_family is OsFamily.NT:
        app_data = env.get("APPDATA")
        config_dir = Path(app_data) if app_data else Path.home() / "AppData" / "Roaming"
        return config_dir / "ananke"

    xdg_config_home = env.get("XDG_CONFIG_HOME")
    config_dir = Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    return config_dir / "ananke"


def _get_data_dir(os_family: OsFamily, env: Mapping[str, str]) -> Path:
    """Returns the path to the data directory.

    Args:
        os_family: The operating system family.
        env: An environment. Typically, this is `os.environ`.

    Returns:
        The path to the data directory.
    """
    if os_family is OsFamily.NT:
        local_app_data = env.get("LOCALAPPDATA")
        data_dir = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return data_dir / "ananke"

    xdg_data_home = env.get("XDG_DATA_HOME")
    data_dir = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return data_dir / "ananke"


def _strtobool(bool_str: str) -> bool:
    if bool_str.lower() in {"true", "yes", "on", "1"}:
        return True
    if bool_str.lower() in {"false", "no", "off", "0"}:
        return False
    raise ValueError(f"Invalid boolean string: {bool_str}")

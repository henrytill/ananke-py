"""Configuration."""
import configparser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Optional, Self

from . import io
from .data import KeyId


def strtobool(bool_str: str) -> bool:
    """Converts a string to a boolean.

    Args:
        bool_str: The string to convert.

    Returns:
        The converted boolean.

    Raises:
        ValueError: If the string is not a valid boolean.
    """
    if bool_str.lower() in {"true", "yes", "on", "1"}:
        return True
    if bool_str.lower() in {"false", "no", "off", "0"}:
        return False
    raise ValueError(f"Invalid boolean string: {bool_str}")


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

    @staticmethod
    def from_str(os_family_str: str) -> "OsFamily":
        """Creates an OsFamily from a string.

        Args:
            os_family_str: The string to create the OsFamily from.

        Returns:
            The created OsFamily.
        """
        match os_family_str:
            case "posix":
                return OsFamily.POSIX
            case "nt":
                return OsFamily.NT
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

    @staticmethod
    def from_str(backend_str: str) -> "Backend":
        """Creates a Backend from a string.

        Args:
            backend_str: The string to create the Backend from.

        Returns:
            The created Backend.
        """
        match backend_str:
            case "sqlite":
                return Backend.SQLITE
            case "json":
                return Backend.JSON
            case _:
                raise ValueError(f"Invalid Backend string: {backend_str}")

    def __str__(self) -> str:
        match self:
            case Backend.SQLITE:
                return "sqlite"
            case Backend.JSON:
                return "json"


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
        """Returns the path to the configuration file.

        Returns:
            The path to the configuration file.
        """
        return self.config_dir / "ananke.ini"

    @property
    def data_file(self) -> Path:
        """Returns the path to the data file.

        Returns:
            The path to the data file.
        """
        return self.data_dir / "db" / "data.json"

    @property
    def schema_file(self) -> Path:
        """Returns the path to the schema file.

        Returns:
            The path to the schema file.
        """
        return self.data_dir / "db" / "schema"


class ConfigBuilder:
    """A configuration builder."""

    _config_dir: Optional[Path]
    _data_dir: Optional[Path]
    _backend: Optional[Backend]
    _key_id: Optional[KeyId]
    _allow_multiple_keys: Optional[bool]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        config_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        backend: Optional[Backend] = None,
        key_id: Optional[KeyId] = None,
        allow_multiple_keys: Optional[bool] = None,
    ) -> None:
        self._config_dir = config_dir
        self._data_dir = data_dir
        self._backend = backend
        self._key_id = key_id
        self._allow_multiple_keys = allow_multiple_keys

    def with_env(self, env: Mapping[str, str]) -> Self:
        """Updates attributes from environment variables.

        Args:
            env: An environment. Typically, this is `os.environ`.

        Returns:
            The updated configuration.
        """
        config_dir = env.get(Env.CONFIG_DIR)
        if config_dir is not None:
            self._config_dir = Path(config_dir)

        data_dir = env.get(Env.DATA_DIR)
        if data_dir is not None:
            self._data_dir = Path(data_dir)

        backend = env.get(Env.BACKEND)
        if backend is not None:
            self._backend = Backend.from_str(backend)

        key_id = env.get(Env.KEY_ID)
        if key_id is not None:
            self._key_id = KeyId(key_id)

        allow_multiple_keys = env.get(Env.ALLOW_MULTIPLE_KEYS)
        if allow_multiple_keys is not None:
            try:
                self._allow_multiple_keys = bool(strtobool(allow_multiple_keys))
            except ValueError:
                self._allow_multiple_keys = False

        return self

    def with_config(self, reader: Callable[[Path], Optional[str]] = io.file_reader) -> Self:
        """Updates attributes from the string representation of a configuration file.

        Args:
            config: The string representation of a configuration file.
            reader: A function that reads a file and returns its string representation.

        Returns:
            The updated configuration.
        """
        if self._config_dir is None:
            raise ValueError("config_dir is not set")

        config_file = self._config_dir / "ananke.ini"
        maybe_config_str = reader(config_file)
        if maybe_config_str is None:
            raise ValueError(f"Configuration file does not exist: {config_file}")

        config_parser = configparser.ConfigParser()
        config_parser.read_string(maybe_config_str)

        data_dir = config_parser.get("data", "dir", fallback=None)
        if data_dir is not None:
            self._data_dir = Path(data_dir)

        backend = config_parser.get("data", "backend", fallback=None)
        if backend is not None:
            self._backend = Backend.from_str(backend)

        key_id = config_parser.get("gpg", "key_id", fallback=None)
        if key_id is not None:
            self._key_id = KeyId(key_id)

        allow_multiple_keys = config_parser.getboolean("gpg", "allow_multiple_keys", fallback=None)
        if allow_multiple_keys is not None:
            self._allow_multiple_keys = bool(allow_multiple_keys)

        return self

    def with_defaults(self, os_family: OsFamily, env: Mapping[str, str]) -> Self:
        """Updates unset attributes with default values.

        Args:
            os_family: The operating system family.
            env: An environment. Typically, this is `os.environ`.

        Returns:
            The updated configuration.
        """
        if self._config_dir is None:
            self._config_dir = _get_config_dir(os_family, env)

        if self._data_dir is None:
            self._data_dir = _get_data_dir(os_family, env)

        if self._backend is None:
            self._backend = Backend.JSON

        if self._allow_multiple_keys is None:
            self._allow_multiple_keys = False

        return self

    def build(self) -> Config:
        """Builds a configuration object.

        Returns:
            The configuration object.
        """
        if self._config_dir is None:
            raise ValueError("config_dir is not set")

        if self._data_dir is None:
            raise ValueError("data_dir is not set")

        if self._backend is None:
            raise ValueError("backend is not set")

        if self._key_id is None:
            raise ValueError("key_id is not set")

        if self._allow_multiple_keys is None:
            raise ValueError("allow_multiple_keys is not set")

        # Create a configuration object
        config = Config(
            config_dir=self._config_dir,
            data_dir=self._data_dir,
            backend=self._backend,
            key_id=self._key_id,
            allow_multiple_keys=self._allow_multiple_keys,
        )

        # Return the configuration
        return config


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

"""Configuration."""
import configparser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Optional, Self

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
    if bool_str.lower() in {'true', 'yes', 'on', '1'}:
        return True
    if bool_str.lower() in {'false', 'no', 'off', '0'}:
        return False
    raise ValueError(f'Invalid boolean string: {bool_str}')


# pylint: disable=too-few-public-methods
class Env:
    """Environment variables used for configuration."""

    DATA_DIR: str = 'TARTARUS_DATA_DIR'
    BACKEND: str = 'TARTARUS_BACKEND'
    KEY_ID: str = 'TARTARUS_KEY_ID'
    ALLOW_MULTIPLE_KEYS: str = 'TARTARUS_ALLOW_MULTIPLE_KEYS'


class OsFamily(Enum):
    """The operating system family."""

    POSIX = 1
    NT = 2

    def __str__(self) -> str:
        return {
            self.POSIX: 'posix',
            self.NT: 'nt',
        }[self]

    @staticmethod
    def from_str(os_family_str: str) -> 'OsFamily':
        """Creates an OsFamily from a string.

        Args:
            os_family_str: The string to create the OsFamily from.

        Returns:
            The created OsFamily.
        """
        match = {
            'posix': OsFamily.POSIX,
            'nt': OsFamily.NT,
        }
        try:
            return match[os_family_str]
        except KeyError as exc:
            raise ValueError(f'Invalid OsFamily string: {os_family_str}') from exc


class Backend(Enum):
    """The backend used to store application data."""

    SQLITE = 1
    JSON = 2

    @staticmethod
    def from_str(backend_str: str) -> 'Backend':
        """Creates a Backend from a string.

        Args:
            s: The string to create the Backend from.

        Returns:
            The created Backend.
        """
        match = {
            'sqlite': Backend.SQLITE,
            'json': Backend.JSON,
        }
        try:
            return match[backend_str]
        except KeyError as exc:
            raise ValueError(f'Invalid Backend string: {backend_str}') from exc

    def __str__(self) -> str:
        return {
            self.SQLITE: 'sqlite',
            self.JSON: 'json',
        }[self]


@dataclass(frozen=True)
class Config:
    """A configuration object.

    Attributes:
        data_dir: The directory where the data is stored.
        backend: The backend used to store the data.
        key_id: The key ID used to encrypt the data.
        allow_multiple_keys: Whether multiple keys are allowed to encrypt the data.
    """

    data_dir: Path
    backend: Backend
    key_id: KeyId
    allow_multiple_keys: bool

    @property
    def data_file(self) -> Path:
        """Returns the path to the data file.

        Returns:
            The path to the data file.
        """
        return self.data_dir / 'db' / 'data.json'


class ConfigBuilder:
    """A configuration builder."""

    _data_dir: Optional[Path]
    _backend: Optional[Backend]
    _key_id: Optional[KeyId]
    _allow_multiple_keys: Optional[bool]

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        backend: Optional[Backend] = None,
        key_id: Optional[KeyId] = None,
        allow_multiple_keys: Optional[bool] = None,
    ) -> None:
        self._data_dir = data_dir
        self._backend = backend
        self._key_id = key_id
        self._allow_multiple_keys = allow_multiple_keys

    def with_env(self, env: Mapping[str, str]) -> Self:
        """Updates unset attributes from environment variables.

        Args:
            env: An environment. Typically, this is `os.environ`.

        Returns:
            The updated configuration.
        """
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

    def with_config(self, config: str) -> Self:
        """Updates unset attributes from the string representation of a configuration file.

        Args:
            config: The string representation of a configuration file.

        Returns:
            The updated configuration.
        """
        config_parser = configparser.ConfigParser()
        config_parser.read_string(config)

        data_dir = config_parser.get('data', 'dir', fallback=None)
        if data_dir is not None:
            self._data_dir = Path(data_dir)

        backend = config_parser.get('data', 'backend', fallback=None)
        if backend is not None:
            self._backend = Backend.from_str(backend)

        key_id = config_parser.get('gpg', 'key_id', fallback=None)
        if key_id is not None:
            self._key_id = KeyId(key_id)

        allow_multiple_keys = config_parser.getboolean('gpg', 'allow_multiple_keys', fallback=None)
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
        if self._data_dir is None:
            if os_family == OsFamily.NT:
                local_app_data = env.get("LOCALAPPDATA")
                data_home = Path(local_app_data) if local_app_data else Path.home() / 'AppData' / 'Local'
            else:
                xdg_data_home = env.get('XDG_DATA_HOME')
                data_home = Path(xdg_data_home) if xdg_data_home else Path.home() / '.local' / 'share'

            self._data_dir = data_home / 'tartarus'

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
        if self._data_dir is None:
            raise ValueError('data_dir is not set')

        if self._backend is None:
            raise ValueError('backend is not set')

        if self._key_id is None:
            raise ValueError('key_id is not set')

        if self._allow_multiple_keys is None:
            raise ValueError('allow_multiple_keys is not set')

        # Create a configuration object
        config = Config(
            data_dir=self._data_dir,
            backend=self._backend,
            key_id=self._key_id,
            allow_multiple_keys=self._allow_multiple_keys,
        )

        # Return the configuration
        return config


def get_config_dir(os_family: OsFamily, env: Mapping[str, str]) -> Path:
    """Returns the path to the configuration directory.

    Args:
        os_family: The operating system family.
        env: An environment. Typically, this is `os.environ`.

    Returns:
        The path to the configuration directory.
    """
    if os_family == OsFamily.NT:
        app_data = env.get('APPDATA')
        config_home = Path(app_data) if app_data else Path.home() / 'AppData' / 'Roaming'
    else:
        xdg_config_home = env.get('XDG_CONFIG_HOME')
        config_home = Path(xdg_config_home) if xdg_config_home else Path.home() / '.config'

    return config_home


def get_config_file(os_family: OsFamily, env: Mapping[str, str]) -> Path:
    """Returns the path to the configuration file.

    Args:
        os_family: The operating system family.
        env: An environment. Typically, this is `os.environ`.

    Returns:
        The path to the configuration file.
    """
    config_home = get_config_dir(os_family, env)
    return config_home / 'tartarus' / 'tartarus.ini'

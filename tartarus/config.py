import configparser
import os
from dataclasses import dataclass
from distutils.util import strtobool
from enum import Enum
from pathlib import Path
from typing import Optional

from .data import KeyId


class Env:
    DATA_DIR: str = 'HECATE_DATA_DIR'
    BACKEND: str = 'HECATE_BACKEND'
    KEY_ID: str = 'HECATE_KEYID'
    ALLOW_MULTIPLE_KEYS: str = 'HECATE_ALLOW_MULTIPLE_KEYS'


class Backend(Enum):
    """
    Represents the backend used to store the data.
    """

    SQLITE = 1
    JSON = 2

    @staticmethod
    def from_str(s: str) -> 'Backend':
        """
        Creates a Backend from a string.

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
            return match[s]
        except KeyError:
            raise ValueError(f'Invalid Backend string: {s}')


class ConfigBuilder:
    """
    A configuration builder.
    """

    data_dir: Optional[Path] = None
    backend: Optional[Backend] = None
    key_id: Optional[KeyId] = None
    allow_multiple_keys: Optional[bool] = None

    def __init__(self) -> None:
        pass

    def with_env(self) -> 'ConfigBuilder':
        """
        Updates unset attributes from environment variables.

        Returns:
            The updated configuration.
        """
        data_dir = os.getenv(Env.DATA_DIR)
        if data_dir is not None:
            self.data_dir = Path(data_dir)

        backend = os.getenv(Env.BACKEND)
        if backend is not None:
            self.backend = Backend.from_str(backend)

        key_id = os.getenv(Env.KEY_ID)
        if key_id is not None:
            self.key_id = KeyId(key_id)

        allow_multiple_keys = os.getenv(Env.ALLOW_MULTIPLE_KEYS)
        if allow_multiple_keys is not None:
            try:
                self.allow_multiple_keys = bool(strtobool(allow_multiple_keys))
            except ValueError:
                self.allow_multiple_keys = False

        return self

    def with_config_file(self, path: Path) -> 'ConfigBuilder':
        """
        Updates unset attributes from a configuration file.

        Args:
            path: The path to the configuration file.

        Returns:
            The updated configuration.
        """
        config = configparser.ConfigParser()
        config.read(path)

        data_dir = config.get('data', 'dir', fallback=None)
        if data_dir is not None:
            self.data_dir = Path(data_dir)

        backend = config.get('data', 'backend', fallback=None)
        if backend is not None:
            self.backend = Backend.from_str(backend)

        key_id = config.get('gpg', 'key_id', fallback=None)
        if key_id is not None:
            self.key_id = KeyId(key_id)

        allow_multiple_keys = config.getboolean('gpg', 'allow_multiple_keys', fallback=None)
        if allow_multiple_keys is not None:
            self.allow_multiple_keys = bool(allow_multiple_keys)

        return self

    def with_defaults(self) -> 'ConfigBuilder':
        """
        Updates unset attributes with default values.

        Returns:
            The updated configuration.
        """
        if self.data_dir is None:
            if os.name == 'nt':
                local_app_data = os.getenv("LOCALAPPDATA")
                data_home = Path(local_app_data) if local_app_data else Path.home() / 'AppData' / 'Local'
            else:
                xdg_data_home = os.getenv('XDG_DATA_HOME')
                data_home = Path(xdg_data_home) if xdg_data_home else Path.home() / '.local' / 'share'
            self.data_dir = data_home / 'hecate'

        if self.backend is None:
            self.backend = Backend.JSON

        if self.allow_multiple_keys is None:
            self.allow_multiple_keys = False

        return self

    def build(self) -> 'Config':
        """
        Builds a configuration object.

        Returns:
            The configuration object.
        """

        if self.data_dir is None:
            raise ValueError('data_dir is not set')

        if self.backend is None:
            raise ValueError('backend is not set')

        if self.key_id is None:
            raise ValueError('key_id is not set')

        if self.allow_multiple_keys is None:
            raise ValueError('allow_multiple_keys is not set')

        # Create a configuration object
        config = Config(
            data_dir=self.data_dir,
            backend=self.backend,
            key_id=self.key_id,
            allow_multiple_keys=self.allow_multiple_keys,
        )

        # Return the configuration
        return config


@dataclass(frozen=True)
class Config:
    """
    A configuration object.

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
        """
        Returns the path to the data file.

        Returns:
            The path to the data file.
        """
        return self.data_dir / 'db' / 'data.json'


def get_config_file_path() -> Path:
    """
    Returns the path to the configuration file.

    Returns:
        The path to the configuration file.

    Raises:
        FileNotFoundError: If the configuration directory does not exist.
    """
    if os.name == 'nt':
        app_data = os.getenv('APPDATA')
        config_home = Path(app_data) if app_data else Path.home() / 'AppData' / 'Roaming'
    else:
        xdg_config_home = os.getenv('XDG_CONFIG_HOME')
        config_home = Path(xdg_config_home) if xdg_config_home else Path.home() / '.config'

    if not config_home.exists():
        raise FileNotFoundError(f"The configuration directory '{config_home}' does not exist.")

    return config_home / 'tartarus' / 'tartarus.ini'

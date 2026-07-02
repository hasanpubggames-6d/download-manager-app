"""
Configuration Module for AI Studio Download Manager
Handles application settings and preferences
"""

import os
import json
from typing import Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Config:
    """Application configuration class"""

    # Download settings
    download_path: str = field(default_factory=lambda: Config.get_default_download_path())
    max_connections: int = 4
    max_speed: int = 0  # 0 = unlimited (KB/s)
    auto_start_downloads: bool = True
    show_notifications: bool = True
    retry_failed_downloads: bool = True
    max_retries: int = 3

    # UI settings
    theme: str = 'light'
    language: str = 'en'
    show_speed_in_title: bool = True
    minimize_to_tray: bool = False

    # Advanced settings
    chunk_size: int = 1024 * 1024  # 1MB chunks
    timeout: int = 30  # seconds
    buffer_size: int = 8192
    verify_ssl: bool = True
    use_proxy: bool = False
    proxy_url: str = ''
    proxy_port: int = 8080
    proxy_username: str = ''
    proxy_password: str = ''

    # Metadata settings
    extract_metadata: bool = True
    save_thumbnails: bool = True

    # Internal
    _config_file: str = field(default='', repr=False)
    _loaded: bool = field(default=False, repr=False)

    @staticmethod
    def get_default_download_path() -> str:
        """Get the default download path based on platform"""
        try:
            # Try Android storage first
            if os.path.exists('/storage/emulated/0/Download'):
                return '/storage/emulated/0/Download/AIStudio'
            elif os.path.exists('/sdcard/Download'):
                return '/sdcard/Download/AIStudio'
        except:
            pass

        # Fall back to user downloads
        home = str(Path.home())
        download_paths = [
            os.path.join(home, 'Downloads', 'AIStudio'),
            os.path.join(home, 'downloads', 'AIStudio'),
            os.path.join(home, 'AIStudio Downloads'),
        ]

        for path in download_paths:
            if os.path.exists(os.path.dirname(path)):
                return path

        # Final fallback
        return os.path.join(home, 'AIStudio Downloads')

    @classmethod
    def get_config_path(cls) -> str:
        """Get the path to the configuration file"""
        # On Android, use external storage
        config_dir = os.path.join(cls.get_default_download_path(), '.config')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'settings.json')

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from file"""
        config_file = cls.get_config_path()
        config = cls(_config_file=config_file)

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Update config with loaded values
                for key, value in data.items():
                    if hasattr(config, key) and not key.startswith('_'):
                        setattr(config, key, value)

                config._loaded = True
            except Exception as e:
                print(f"Error loading config: {e}")

        # Ensure download directory exists
        os.makedirs(config.download_path, exist_ok=True)

        return config

    def save(self) -> bool:
        """Save configuration to file"""
        config_file = self._config_file or self.get_config_path()

        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(config_file), exist_ok=True)

            # Convert to dict, excluding private fields
            data = {
                k: v for k, v in asdict(self).items()
                if not k.startswith('_')
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_proxy_config(self) -> Optional[dict]:
        """Get proxy configuration if enabled"""
        if not self.use_proxy or not self.proxy_url:
            return None

        proxy_config = {
            'http': f'{self.proxy_url}:{self.proxy_port}',
            'https': f'{self.proxy_url}:{self.proxy_port}',
        }

        if self.proxy_username and self.proxy_password:
            proxy_config['auth'] = (self.proxy_username, self.proxy_password)

        return proxy_config

    def ensure_download_path(self) -> bool:
        """Ensure download path exists and is writable"""
        try:
            if not os.path.exists(self.download_path):
                os.makedirs(self.download_path, exist_ok=True)

            # Test write permission
            test_file = os.path.join(self.download_path, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)

            return True
        except Exception as e:
            print(f"Download path error: {e}")
            return False

    def __setattr__(self, name, value):
        """Auto-save when config changes"""
        super().__setattr__(name, value)

        # Don't auto-save during init for private fields
        if not name.startswith('_') and hasattr(self, '_loaded') and self._loaded:
            self.save()


class ConfigValidator:
    """Validator for configuration values"""

    @staticmethod
    def validate_max_connections(value: int) -> int:
        """Validate max connections (1-16)"""
        return max(1, min(16, value))

    @staticmethod
    def validate_speed_limit(value: int) -> int:
        """Validate speed limit (>= 0)"""
        return max(0, value)

    @staticmethod
    def validate_timeout(value: int) -> int:
        """Validate timeout (5-300 seconds)"""
        return max(5, min(300, value))

    @staticmethod
    def validate_chunk_size(value: int) -> int:
        """Validate chunk size (min 64KB)"""
        return max(64 * 1024, value)

    @staticmethod
    def validate_path(path: str) -> bool:
        """Validate download path exists and is accessible"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except:
            return False


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.load()
    return _config_instance


def reload_config() -> Config:
    """Reload config from file"""
    global _config_instance
    _config_instance = Config.load()
    return _config_instance

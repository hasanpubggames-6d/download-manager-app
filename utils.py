"""
Utility Functions for AI Studio Download Manager
Common helper functions and utilities
"""

import os
import re
import time
import hashlib
import threading
import subprocess
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from urllib.parse import urlparse, unquote


class Utils:
    """General utility functions"""

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """Sanitize a filename to be safe for all platforms"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')

        # Truncate if too long
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            ext_length = len(ext)
            name = name[:max_length - ext_length]
            filename = name + ext

        # Ensure non-empty filename
        if not filename:
            filename = f'download_{int(time.time())}'

        return filename

    @staticmethod
    def get_filename_from_url(url: str) -> str:
        """Extract filename from URL"""
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            filename = os.path.basename(path)

            if filename and '.' in filename:
                return filename

            # Try to get filename from query parameters
            if '?' in url:
                query = url.split('?')[-1]
                for param in query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        if key.lower() in ['filename', 'file', 'name']:
                            return unquote(value)

        except:
            pass

        # Generate default filename
        return f'download_{int(time.time())}'

    @staticmethod
    def get_filename_from_content_disposition(header: str) -> Optional[str]:
        """Extract filename from Content-Disposition header"""
        if not header:
            return None

        # Try to find filename* first (RFC 5987)
        match = re.search(r"filename\*=(?:UTF-8''|)([^;]+)", header, re.IGNORECASE)
        if match:
            return unquote(match.group(1))

        # Then try regular filename
        match = re.search(r'filename="?([^";\n]+)"?', header, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'md5',
                           chunk_size: int = 8192) -> str:
        """Calculate hash of a file"""
        hash_obj = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    @staticmethod
    def verify_file_integrity(file_path: str, expected_hash: str,
                              algorithm: str = 'md5') -> bool:
        """Verify file integrity against expected hash"""
        if not os.path.exists(file_path):
            return False

        actual_hash = Utils.calculate_file_hash(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return '0 B'

        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        size = float(size_bytes)

        for unit in units[:-1]:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024

        return f'{size:.1f} {units[-1]}'

    @staticmethod
    def format_time(seconds: int) -> str:
        """Format time duration"""
        if seconds < 0:
            return '--:--'

        if seconds < 60:
            return f'{seconds}s'

        if seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f'{minutes}m {secs}s'

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f'{hours}h {minutes}m'

    @staticmethod
    def format_speed(bytes_per_second: int) -> str:
        """Format transfer speed"""
        return f'{Utils.format_size(bytes_per_second)}/s'

    @staticmethod
    def is_url_valid(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    @staticmethod
    def get_url_domain(url: str) -> str:
        """Get domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ''

    @staticmethod
    def ensure_dir(path: str) -> bool:
        """Ensure directory exists"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except:
            return False

    @staticmethod
    def get_available_space(path: str) -> int:
        """Get available disk space in bytes"""
        try:
            stat = os.statvfs(path)
            return stat.f_bavail * stat.f_frsize
        except:
            return 0

    @staticmethod
    def has_enough_space(path: str, required_bytes: int) -> bool:
        """Check if there's enough disk space"""
        available = Utils.get_available_space(path)
        # Add 100MB buffer
        return available >= (required_bytes + 100 * 1024 * 1024)

    @staticmethod
    def open_file_externally(file_path: str) -> bool:
        """Open file with system default application"""
        try:
            if os.name == 'posix':
                # Try termux-open for Android
                if os.path.exists('/system/bin/am'):
                    subprocess.run(['am', 'start', '-a', 'android.intent.action.VIEW',
                                  '-d', f'file://{file_path}'], check=True)
                    return True
                else:
                    subprocess.run(['xdg-open', file_path], check=True)
                    return True
            elif os.name == 'nt':
                os.startfile(file_path)
                return True
        except:
            pass
        return False

    @staticmethod
    def open_folder(file_path: str) -> bool:
        """Open containing folder"""
        folder = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
        return Utils.open_file_externally(folder)

    @staticmethod
    def get_unique_filename(directory: str, filename: str) -> str:
        """Get unique filename, appending number if needed"""
        base_path = os.path.join(directory, filename)

        if not os.path.exists(base_path):
            return filename

        name, ext = os.path.splitext(filename)
        counter = 1

        while True:
            new_filename = f'{name} ({counter}){ext}'
            new_path = os.path.join(directory, new_filename)

            if not os.path.exists(new_path):
                return new_filename

            counter += 1

    @staticmethod
    def run_in_thread(func: Callable, *args, **kwargs) -> threading.Thread:
        """Run a function in a separate thread"""
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def debounce(wait: float):
        """Debounce decorator"""
        def decorator(func: Callable) -> Callable:
            last_call = [0]
            timer = [None]

            def wrapper(*args, **kwargs):
                now = time.time()

                if timer[0]:
                    timer[0].cancel()

                timer[0] = threading.Timer(wait, func, args, kwargs)
                timer[0].start()

            return wrapper
        return decorator


class DownloadURLParser:
    """Parse and analyze download URLs"""

    SUPPORTED_PROTOCOLS = ['http://', 'https://', 'ftp://']

    # Special URL patterns for various services
    URL_PATTERNS = {
        'youtube': [
            r'(youtube\.com/watch\?v=)',
            r'(youtu\.be/)',
            r'(youtube\.com/shorts/)',
        ],
        'drive': [
            r'(drive\.google\.com)',
        ],
        'dropbox': [
            r'(dropbox\.com/s/)',
            r'(dl\.dropboxusercontent\.com)',
        ],
        'mediafire': [
            r'(mediafire\.com/file/)',
        ],
        'mega': [
            r'(mega\.nz)',
            r'(mega\.co\.nz)',
        ],
    }

    @classmethod
    def parse(cls, url: str) -> Dict[str, Any]:
        """Parse a URL and extract information"""
        result = {
            'url': url,
            'valid': False,
            'protocol': '',
            'domain': '',
            'filename': '',
            'extension': '',
            'service_type': 'direct',
            'needs_processing': False,
        }

        try:
            parsed = urlparse(url)
            result['protocol'] = parsed.scheme
            result['domain'] = parsed.netloc
            result['valid'] = bool(parsed.scheme and parsed.netloc)

            # Get filename from URL
            filename = Utils.get_filename_from_url(url)
            result['filename'] = filename

            if filename and '.' in filename:
                result['extension'] = os.path.splitext(filename)[1].lower()

            # Check for special services
            for service, patterns in cls.URL_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, url, re.IGNORECASE):
                        result['service_type'] = service
                        result['needs_processing'] = True
                        break

        except Exception as e:
            result['error'] = str(e)

        return result

    @classmethod
    def is_direct_download(cls, url: str) -> bool:
        """Check if URL is a direct download link"""
        parsed = cls.parse(url)
        return not parsed.get('needs_processing', False)

    @classmethod
    def get_service_type(cls, url: str) -> str:
        """Get the type of download service"""
        info = cls.parse(url)
        return info.get('service_type', 'direct')


class SpeedLimiter:
    """Rate limit downloads"""

    def __init__(self, max_speed: int = 0):
        """
        Initialize speed limiter

        Args:
            max_speed: Maximum speed in bytes per second (0 = unlimited)
        """
        self.max_speed = max_speed
        self._bytes_this_second = 0
        self._second_start = time.time()
        self._lock = threading.Lock()

    def set_max_speed(self, speed: int):
        """Set maximum speed"""
        with self._lock:
            self.max_speed = speed

    def wait_if_needed(self, bytes_downloaded: int):
        """Wait if download speed exceeds limit"""
        if self.max_speed <= 0:
            return

        with self._lock:
            now = time.time()
            elapsed = now - self._second_start

            # Reset counter if second has passed
            if elapsed >= 1.0:
                self._bytes_this_second = 0
                self._second_start = now
                elapsed = 0

            self._bytes_this_second += bytes_downloaded

            # Check if we've exceeded the limit
            if self._bytes_this_second >= self.max_speed:
                # Calculate wait time
                remaining_time = 1.0 - elapsed
                if remaining_time > 0:
                    time.sleep(remaining_time)
                    self._bytes_this_second = 0
                    self._second_start = time.time()

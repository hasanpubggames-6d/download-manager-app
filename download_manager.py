"""
Download Manager Module for AI Studio Download Manager
Handles multi-threaded downloads with pause/resume support
"""

import os
import time
import uuid
import threading
import urllib.request
import urllib.error
from enum import Enum, auto
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse, unquote
import ssl
import json


class DownloadStatus(Enum):
    """Download status enum"""
    PENDING = auto()
    QUEUED = auto()
    DOWNLOADING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    UNKNOWN = auto()

    @property
    def text(self) -> str:
        return {
            DownloadStatus.PENDING: 'Pending',
            DownloadStatus.QUEUED: 'Queued',
            DownloadStatus.DOWNLOADING: 'Downloading...',
            DownloadStatus.PAUSED: 'Paused',
            DownloadStatus.COMPLETED: 'Completed',
            DownloadStatus.FAILED: 'Failed',
            DownloadStatus.CANCELLED: 'Cancelled',
            DownloadStatus.UNKNOWN: 'Unknown'
        }.get(self, 'Unknown')


@dataclass
class DownloadItem:
    """Represents a single download item"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    url: str = ''
    filename: str = ''
    download_path: str = ''
    total_size: int = 0
    downloaded_size: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    speed: int = 0  # bytes per second
    time_remaining: int = 0  # seconds
    error_message: str = ''
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    supports_resume: bool = False
    etag: str = ''
    last_modified: str = ''

    # Internal fields
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _pause_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _temp_file: str = field(default='', repr=False)

    @property
    def status_text(self) -> str:
        """Get human readable status"""
        if self.status == DownloadStatus.DOWNLOADING:
            speed_mb = self.speed / (1024 * 1024)
            return f"{self.status.text} ({speed_mb:.1f} MB/s)"
        return self.status.text

    @property
    def file_path(self) -> str:
        """Get full file path"""
        return os.path.join(self.download_path, self.filename)

    @property
    def temp_file_path(self) -> str:
        """Get temp file path for partial downloads"""
        return self.file_path + '.download'

    @property
    def size_mb(self) -> float:
        """Get total size in MB"""
        return self.total_size / (1024 * 1024)

    @property
    def downloaded_mb(self) -> float:
        """Get downloaded size in MB"""
        return self.downloaded_size / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            'id': self.id,
            'url': self.url,
            'filename': self.filename,
            'download_path': self.download_path,
            'total_size': self.total_size,
            'downloaded_size': self.downloaded_size,
            'progress': self.progress,
            'speed': self.speed,
            'status': self.status.name,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'supports_resume': self.supports_resume,
        }


class DownloadWorker(threading.Thread):
    """Worker thread for downloading files"""

    def __init__(self, item: DownloadItem, config: 'Config', manager: 'DownloadManager'):
        super().__init__(daemon=True)
        self.item = item
        self.config = config
        self.manager = manager
        self.stop_event = item._stop_event
        self.pause_event = item._pause_event
        self._last_progress_time = 0

    def run(self):
        """Execute download"""
        try:
            self._download()
        except Exception as e:
            self.item.error_message = str(e)
            self.item.status = DownloadStatus.FAILED
            self.manager._on_download_error(self.item, str(e))
        finally:
            self.manager._on_download_finished(self.item)

    def _download(self):
        """Perform the actual download"""
        # Prepare request
        request = urllib.request.Request(self.item.url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36')

        # Add range header for resume
        if self.item.supports_resume and self.item.downloaded_size > 0:
            request.add_header('Range', f'bytes={self.item.downloaded_size}-')

        # Create SSL context
        if self.config.verify_ssl:
            ssl_context = ssl.create_default_context()
        else:
            ssl_context = ssl._create_unverified_context()

        # Open connection
        response = urllib.request.urlopen(request, timeout=self.config.timeout, context=ssl_context)

        # Handle response
        http_code = response.getcode()
        headers = response.headers

        # Check for partial content support
        accepts_ranges = headers.get('Accept-Ranges', '').lower() == 'bytes'
        self.item.supports_resume = accepts_ranges

        # Get content length
        content_length = int(headers.get('Content-Length', 0))
        if http_code == 206:  # Partial content
            self.item.total_size = content_length + self.item.downloaded_size
        elif http_code == 200:
            self.item.total_size = content_length

        # Determine file mode
        if os.path.exists(self.item.temp_file_path) and self.item.supports_resume:
            file_mode = 'ab'
            start_pos = os.path.getsize(self.item.temp_file_path)
        else:
            file_mode = 'wb'
            start_pos = 0
            self.item.downloaded_size = 0

        # Update status
        self.item.status = DownloadStatus.DOWNLOADING
        self.item.started_at = datetime.now()

        # Download progress tracking
        chunk_size = self.config.chunk_size
        last_size = self.item.downloaded_size
        last_time = time.time()

        with open(self.item.temp_file_path, file_mode) as f:
            while True:
                # Check for pause
                while self.pause_event.is_set():
                    time.sleep(0.1)
                    self.item.status = DownloadStatus.PAUSED

                # Check for stop
                if self.stop_event.is_set():
                    self.item.status = DownloadStatus.CANCELLED
                    return

                # Read chunk
                chunk = response.read(self.config.buffer_size)
                if not chunk:
                    break

                # Write chunk
                f.write(chunk)
                self.item.downloaded_size += len(chunk)

                # Calculate speed and progress
                current_time = time.time()
                time_diff = current_time - last_time

                if time_diff >= 0.5:  # Update every 0.5 seconds
                    size_diff = self.item.downloaded_size - last_size
                    self.item.speed = int(size_diff / time_diff)

                    if self.item.speed > 0 and self.item.total_size > 0:
                        remaining = self.item.total_size - self.item.downloaded_size
                        self.item.time_remaining = int(remaining / self.item.speed)

                    if self.item.total_size > 0:
                        self.item.progress = (self.item.downloaded_size / self.item.total_size) * 100

                    last_size = self.item.downloaded_size
                    last_time = current_time

        # Download complete
        self._finalize_download()

    def _finalize_download(self):
        """Finalize the download after completion"""
        # Move temp file to final location
        if os.path.exists(self.item.temp_file_path):
            try:
                # Remove existing file if any
                if os.path.exists(self.item.file_path):
                    os.remove(self.item.file_path)
                os.rename(self.item.temp_file_path, self.item.file_path)
            except Exception as e:
                # Fallback: copy and delete
                import shutil
                shutil.copy2(self.item.temp_file_path, self.item.file_path)
                os.remove(self.item.temp_file_path)

        # Update status
        self.item.status = DownloadStatus.COMPLETED
        self.item.completed_at = datetime.now()
        self.item.progress = 100
        self.item.speed = 0

    def pause(self):
        """Pause the download"""
        self.item.status = DownloadStatus.PAUSED
        self.pause_event.set()

    def resume(self):
        """Resume the download"""
        self.item.status = DownloadStatus.DOWNLOADING
        self.pause_event.clear()

    def stop(self):
        """Stop the download"""
        self.stop_event.set()
        if self.item._thread and self.item._thread.is_alive():
            self.item._thread.join(timeout=2)


class DownloadManager:
    """Main download manager class"""

    def __init__(self, config: 'Config'):
        self.config = config
        self.downloads: Dict[str, DownloadItem] = {}
        self.active_downloads: Dict[str, DownloadWorker] = {}
        self.download_queue: List[str] = []
        self.lock = threading.Lock()
        self._max_active = config.max_connections
        self._save_file = os.path.join(
            config.download_path, '.config', 'downloads.json'
        )

        # Load saved downloads
        self._load_downloads()

        # Queue processor
        self._queue_processor = threading.Thread(target=self._process_queue, daemon=True)
        self._queue_processor.start()

    def _load_downloads(self):
        """Load saved downloads from file"""
        if os.path.exists(self._save_file):
            try:
                with open(self._save_file, 'r') as f:
                    data = json.load(f)

                for dl_data in data.get('downloads', []):
                    dl = self._create_download_from_json(dl_data)
                    if dl.status not in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED]:
                        self.downloads[dl.id] = dl
                        dl.status = DownloadStatus.PENDING
            except Exception as e:
                print(f"Error loading downloads: {e}")

    def _save_downloads(self):
        """Save downloads to file"""
        os.makedirs(os.path.dirname(self._save_file), exist_ok=True)

        data = {
            'downloads': [dl.to_dict() for dl in self.downloads.values()]
        }

        with open(self._save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _create_download_from_json(self, data: Dict) -> DownloadItem:
        """Create DownloadItem from JSON data"""
        item = DownloadItem(
            id=data.get('id', str(uuid.uuid4())[:8]),
            url=data.get('url', ''),
            filename=data.get('filename', ''),
            download_path=data.get('download_path', ''),
            total_size=data.get('total_size', 0),
            downloaded_size=data.get('downloaded_size', 0),
            progress=data.get('progress', 0),
            status=DownloadStatus[data.get('status', 'PENDING')],
            supports_resume=data.get('supports_resume', False)
        )
        return item

    def add_download(self, url: str, filename: Optional[str] = None) -> DownloadItem:
        """Add a new download to the queue"""
        # Parse URL to get filename
        if not filename:
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path)) or f'download_{int(time.time())}'

        if not filename:
            filename = f'download_{int(time.time())}'

        # Create download item
        item = DownloadItem(
            url=url,
            filename=filename,
            download_path=self.config.download_path
        )

        with self.lock:
            self.downloads[item.id] = item
            self.download_queue.append(item.id)

        # Save downloads
        self._save_downloads()

        return item

    def start_download(self, download_id: str) -> bool:
        """Start a specific download"""
        with self.lock:
            if download_id not in self.downloads:
                return False

            if len(self.active_downloads) >= self._max_active:
                return False

            item = self.downloads[download_id]

            # Check if already active
            if item.status == DownloadStatus.DOWNLOADING:
                return True

            # Reset status
            item.status = DownloadStatus.PENDING
            item._stop_event.clear()
            item._pause_event.clear()

            # Create and start worker
            worker = DownloadWorker(item, self.config, self)
            item._thread = worker
            self.active_downloads[download_id] = worker
            worker.start()

            return True

    def pause_download(self, download_id: str) -> bool:
        """Pause a download"""
        with self.lock:
            if download_id in self.active_downloads:
                worker = self.active_downloads[download_id]
                worker.pause()
                return True
            return False

    def resume_download(self, download_id: str) -> bool:
        """Resume a paused download"""
        with self.lock:
            if download_id in self.active_downloads:
                worker = self.active_downloads[download_id]
                worker.resume()
                return True
            elif download_id in self.downloads:
                return self.start_download(download_id)
            return False

    def cancel_download(self, download_id: str) -> bool:
        """Cancel a download"""
        with self.lock:
            if download_id in self.active_downloads:
                worker = self.active_downloads.pop(download_id)
                worker.stop()

            if download_id in self.downloads:
                item = self.downloads.pop(download_id, None)
                if item:
                    # Remove temp file
                    if os.path.exists(item.temp_file_path):
                        try:
                            os.remove(item.temp_file_path)
                        except:
                            pass
                    item.status = DownloadStatus.CANCELLED
                self._save_downloads()
                return True
            return False

    def start_all(self):
        """Start all pending downloads"""
        with self.lock:
            for dl_id in list(self.download_queue):
                if dl_id in self.downloads:
                    if len(self.active_downloads) < self._max_active:
                        self.start_download(dl_id)

    def pause_all(self):
        """Pause all active downloads"""
        with self.lock:
            for worker in self.active_downloads.values():
                worker.pause()

    def stop_all(self):
        """Stop all downloads"""
        with self.lock:
            for worker in self.active_downloads.values():
                worker.stop()
            self.active_downloads.clear()

    def clear_completed(self):
        """Remove completed downloads"""
        with self.lock:
            completed_ids = [
                dl_id for dl_id, dl in self.downloads.items()
                if dl.status == DownloadStatus.COMPLETED
            ]
            for dl_id in completed_ids:
                del self.downloads[dl_id]
            self._save_downloads()

    def get_all_downloads(self) -> List[DownloadItem]:
        """Get list of all downloads"""
        return list(self.downloads.values())

    def get_download(self, download_id: str) -> Optional[DownloadItem]:
        """Get a specific download by ID"""
        return self.downloads.get(download_id)

    def _process_queue(self):
        """Process download queue in background"""
        while True:
            time.sleep(1)

            with self.lock:
                # Check if we can start more downloads
                if len(self.active_downloads) < self._max_active:
                    for dl_id in self.download_queue:
                        if dl_id in self.downloads:
                            item = self.downloads[dl_id]
                            if item.status == DownloadStatus.PENDING:
                                if self.start_download(dl_id):
                                    break

    def _on_download_finished(self, item: DownloadItem):
        """Called when a download finishes"""
        with self.lock:
            if item.id in self.active_downloads:
                del self.active_downloads[item.id]

            if item.id in self.download_queue:
                self.download_queue.remove(item.id)

        self._save_downloads()

    def _on_download_error(self, item: DownloadItem, error: str):
        """Called when a download fails"""
        print(f"Download error: {item.filename} - {error}")

        # Check for retry
        if self.config.retry_failed_downloads:
            # Could implement retry logic here
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Get download statistics"""
        downloads = self.get_all_downloads()

        return {
            'total': len(downloads),
            'active': len([d for d in downloads if d.status == DownloadStatus.DOWNLOADING]),
            'paused': len([d for d in downloads if d.status == DownloadStatus.PAUSED]),
            'completed': len([d for d in downloads if d.status == DownloadStatus.COMPLETED]),
            'failed': len([d for d in downloads if d.status == DownloadStatus.FAILED]),
            'pending': len([d for d in downloads if d.status == DownloadStatus.PENDING]),
            'total_size': sum(d.total_size for d in downloads),
            'downloaded': sum(d.downloaded_size for d in downloads),
        }

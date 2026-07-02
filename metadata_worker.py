"""
Metadata Worker Module for AI Studio Download Manager
Extracts and manages metadata for downloaded files
"""

import os
import json
import threading
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class FileMetadata:
    """Metadata for a downloaded file"""
    filename: str = ''
    file_path: str = ''
    file_size: int = 0
    file_type: str = ''
    mime_type: str = ''
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = None
    download_url: str = ''
    source_domain: str = ''
    duration: Optional[float] = None  # For audio/video
    width: Optional[int] = None  # For images/video
    height: Optional[int] = None  # For images/video
    title: str = ''
    author: str = ''
    description: str = ''
    keywords: List[str] = field(default_factory=list)
    checksum_md5: str = ''
    checksum_sha256: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.modified_at:
            data['modified_at'] = self.modified_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        if data.get('modified_at'):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        return cls(**data)


class MetadataWorker:
    """Worker for extracting and managing file metadata"""

    # MIME type mappings
    MIME_TYPES = {
        '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska',
        '.mov': 'video/quicktime',
        '.webm': 'video/webm',
        '.flv': 'video/x-flv',
        '.wmv': 'video/x-ms-wmv',
        '.m4v': 'video/mp4',
        '.mpg': 'video/mpeg',
        '.mpeg': 'video/mpeg',

        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.tiff': 'image/tiff',

        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',

        '.zip': 'application/zip',
        '.rar': 'application/vnd.rar',
        '.7z': 'application/x-7z-compressed',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',

        '.apk': 'application/vnd.android.package-archive',
        '.exe': 'application/x-msdownload',
        '.dmg': 'application/x-apple-diskimage',
        '.iso': 'application/x-iso9660-image',

        '.json': 'application/json',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.txt': 'text/plain',
        '.css': 'text/css',
        '.js': 'application/javascript',
    }

    FILE_TYPE_MAPPING = {
        'video': ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.ape'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico', '.tiff'],
        'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf'],
        'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'application': ['.apk', '.exe', '.dmg', '.iso'],
        'code': ['.py', '.java', '.js', '.html', '.css', '.json', '.xml'],
    }

    def __init__(self, config: 'Config'):
        self.config = config
        self._metadata_cache: Dict[str, FileMetadata] = {}
        self._metadata_dir = os.path.join(
            config.download_path, '.metadata'
        )
        self._running = True
        self._lock = threading.Lock()

        # Ensure metadata directory exists
        os.makedirs(self._metadata_dir, exist_ok=True)

        # Load existing metadata
        self._load_metadata_cache()

        # Start background processor
        self._processor = threading.Thread(target=self._process_metadata, daemon=True)
        self._processor.start()

    def _load_metadata_cache(self):
        """Load existing metadata from files"""
        for filename in os.listdir(self._metadata_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self._metadata_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    metadata = FileMetadata.from_dict(data)
                    self._metadata_cache[metadata.file_path] = metadata
                except Exception as e:
                    print(f"Error loading metadata: {e}")

    def _process_metadata(self):
        """Background process for metadata extraction"""
        while self._running:
            time.sleep(5)

    def get_extension(self, filename: str) -> str:
        """Get file extension in lowercase"""
        return Path(filename).suffix.lower()

    def get_mime_type(self, filename: str) -> str:
        """Get MIME type for a file"""
        ext = self.get_extension(filename)
        return self.MIME_TYPES.get(ext, 'application/octet-stream')

    def get_file_type(self, filename: str) -> str:
        """Get file type category"""
        ext = self.get_extension(filename)

        for file_type, extensions in self.FILE_TYPE_MAPPING.items():
            if ext in extensions:
                return file_type
        return 'other'

    def extract_metadata(self, file_path: str, url: str = '') -> Optional[FileMetadata]:
        """Extract metadata from a file"""
        if not os.path.exists(file_path):
            return None

        try:
            filename = os.path.basename(file_path)
            file_stat = os.stat(file_path)

            metadata = FileMetadata(
                filename=filename,
                file_path=file_path,
                file_size=file_stat.st_size,
                file_type=self.get_file_type(filename),
                mime_type=self.get_mime_type(filename),
                created_at=datetime.now(),
                modified_at=datetime.fromtimestamp(file_stat.st_mtime),
                download_url=url,
            )

            # Extract source domain
            if url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    metadata.source_domain = parsed.netloc
                except:
                    pass

            # Save metadata
            self._save_metadata(metadata)

            # Cache metadata
            with self._lock:
                self._metadata_cache[file_path] = metadata

            return metadata

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return None

    def _save_metadata(self, metadata: FileMetadata):
        """Save metadata to file"""
        safe_filename = metadata.file_path.replace('/', '_').replace('\\', '_')
        meta_path = os.path.join(self._metadata_dir, f'{safe_filename}.json')

        try:
            os.makedirs(self._metadata_dir, exist_ok=True)

            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")

    def get_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """Get cached metadata for a file"""
        with self._lock:
            return self._metadata_cache.get(file_path)

    def search_metadata(self, query: str) -> List[FileMetadata]:
        """Search metadata by query"""
        query = query.lower()
        results = []

        with self._lock:
            for metadata in self._metadata_cache.values():
                # Search in filename, title, description, keywords
                searchable = ' '.join([
                    metadata.filename,
                    metadata.title,
                    metadata.description,
                    ' '.join(metadata.keywords)
                ]).lower()

                if query in searchable:
                    results.append(metadata)

        return results

    def get_files_by_type(self, file_type: str) -> List[FileMetadata]:
        """Get all files of a specific type"""
        results = []

        with self._lock:
            for metadata in self._metadata_cache.values():
                if metadata.file_type == file_type:
                    results.append(metadata)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get metadata statistics"""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_type': {},
            'by_domain': {},
        }

        with self._lock:
            stats['total_files'] = len(self._metadata_cache)

            for metadata in self._metadata_cache.values():
                stats['total_size'] += metadata.file_size

                # Count by type
                file_type = metadata.file_type
                stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1

                # Count by domain
                domain = metadata.source_domain or 'unknown'
                stats['by_domain'][domain] = stats['by_domain'].get(domain, 0) + 1

        return stats

    def cleanup_deleted_files(self):
        """Remove metadata for files that no longer exist"""
        to_remove = []

        with self._lock:
            for file_path in list(self._metadata_cache.keys()):
                if not os.path.exists(file_path):
                    to_remove.append(file_path)

            for file_path in to_remove:
                del self._metadata_cache[file_path]

                # Remove metadata file
                safe_filename = file_path.replace('/', '_').replace('\\', '_')
                meta_path = os.path.join(self._metadata_dir, f'{safe_filename}.json')
                if os.path.exists(meta_path):
                    try:
                        os.remove(meta_path)
                    except:
                        pass

        return len(to_remove)

    def stop(self):
        """Stop the metadata worker"""
        self._running = False
        if self._processor.is_alive():
            self._processor.join(timeout=2)

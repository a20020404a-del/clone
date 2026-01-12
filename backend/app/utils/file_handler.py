"""File handling utilities"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
import aiofiles
import aiofiles.os

from ..config import get_settings


class FileHandler:
    """Utility class for file operations"""

    def __init__(self):
        self.settings = get_settings()

    async def save_upload_file(
        self,
        content: bytes,
        filename: str,
        file_type: str
    ) -> Tuple[str, Path]:
        """
        Save an uploaded file.

        Args:
            content: File content as bytes
            filename: Original filename
            file_type: Type of file ('voice', 'image', 'video')

        Returns:
            Tuple of (file_id, file_path)
        """
        file_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower() or self._default_extension(file_type)

        upload_dir = self.settings.upload_dir / file_type
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{file_id}{ext}"

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return file_id, file_path

    def _default_extension(self, file_type: str) -> str:
        """Get default extension for file type"""
        defaults = {
            "voice": ".mp3",
            "image": ".png",
            "video": ".mp4"
        }
        return defaults.get(file_type, "")

    async def get_file(self, file_id: str, file_type: str) -> Optional[Path]:
        """
        Get file path by ID.

        Args:
            file_id: File identifier
            file_type: Type of file

        Returns:
            Path to file if exists, None otherwise
        """
        base_dir = self.settings.upload_dir / file_type

        # Try common extensions
        extensions = {
            "voice": [".mp3", ".wav", ".m4a", ".ogg"],
            "image": [".png", ".jpg", ".jpeg"],
            "video": [".mp4", ".webm"]
        }

        for ext in extensions.get(file_type, [""]):
            file_path = base_dir / f"{file_id}{ext}"
            if file_path.exists():
                return file_path

        return None

    async def get_output_file(self, file_id: str, file_type: str) -> Optional[Path]:
        """
        Get output file path by ID.

        Args:
            file_id: File identifier
            file_type: Type of file

        Returns:
            Path to file if exists, None otherwise
        """
        base_dir = self.settings.output_dir / file_type

        extensions = {
            "voice": [".mp3", ".wav"],
            "video": [".mp4", ".webm"]
        }

        for ext in extensions.get(file_type, [""]):
            file_path = base_dir / f"{file_id}{ext}"
            if file_path.exists():
                return file_path

        return None

    async def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path to file

        Returns:
            True if deleted, False otherwise
        """
        try:
            if file_path.exists():
                await aiofiles.os.remove(file_path)
                return True
        except Exception:
            pass
        return False

    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up files older than specified age.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of files deleted
        """
        import time

        deleted_count = 0
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for base_dir in [self.settings.upload_dir, self.settings.output_dir]:
            if not base_dir.exists():
                continue

            for file_type_dir in base_dir.iterdir():
                if not file_type_dir.is_dir():
                    continue

                for file_path in file_type_dir.iterdir():
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age_seconds:
                            try:
                                await aiofiles.os.remove(file_path)
                                deleted_count += 1
                            except Exception:
                                pass

        return deleted_count

    def get_file_info(self, file_path: Path) -> dict:
        """
        Get file information.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file info
        """
        if not file_path.exists():
            return {}

        stat = file_path.stat()
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "extension": file_path.suffix
        }

    def validate_file_size(self, size: int, file_type: str) -> Tuple[bool, str]:
        """
        Validate file size.

        Args:
            size: File size in bytes
            file_type: Type of file

        Returns:
            Tuple of (is_valid, message)
        """
        max_sizes = {
            "voice": self.settings.max_voice_file_size,
            "image": self.settings.max_image_file_size,
            "video": 100 * 1024 * 1024  # 100MB
        }

        max_size = max_sizes.get(file_type, 10 * 1024 * 1024)

        if size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File too large. Maximum size is {max_mb:.1f}MB"

        return True, "File size OK"

    def validate_file_type(self, filename: str, file_type: str) -> Tuple[bool, str]:
        """
        Validate file extension.

        Args:
            filename: Original filename
            file_type: Expected file type

        Returns:
            Tuple of (is_valid, message)
        """
        ext = Path(filename).suffix.lower().lstrip(".")

        allowed = {
            "voice": self.settings.supported_audio_formats,
            "image": self.settings.supported_image_formats,
            "video": ["mp4", "webm", "mov"]
        }

        allowed_formats = allowed.get(file_type, [])

        if ext not in allowed_formats:
            return False, f"Invalid file type. Allowed: {', '.join(allowed_formats)}"

        return True, "File type OK"

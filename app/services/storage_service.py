"""
Storage Service - Local and Google Drive storage
"""
import asyncio
import logging
import os
import shutil
import uuid
from typing import Optional, BinaryIO
from urllib.parse import urljoin

import httpx

from app.config import get_settings
from app.core.exceptions import ProcessingError
from app.core.security import sanitize_filename

settings = get_settings()
logger = logging.getLogger(__name__)


class StorageService:
    """Service for file storage operations"""
    
    def __init__(self, storage_type: str = "local", google_credentials: Optional[dict] = None):
        self.storage_type = storage_type
        self.google_credentials = google_credentials
        self.local_path = settings.storage_path
        
        # Ensure directories exist
        for subfolder in ["audio", "covers", "temp", "references"]:
            os.makedirs(os.path.join(self.local_path, subfolder), exist_ok=True)
    
    async def save_file(
        self,
        data: bytes,
        subfolder: str = "audio",
        filename: Optional[str] = None,
        extension: str = "mp3"
    ) -> str:
        """
        Save a file to storage.
        
        Args:
            data: File bytes
            subfolder: Subfolder (audio, covers, temp)
            filename: Optional filename
            extension: File extension
        
        Returns:
            URL/path to saved file
        """
        if self.storage_type == "google_drive":
            return await self._save_to_google_drive(data, subfolder, filename, extension)
        else:
            return await self._save_locally(data, subfolder, filename, extension)
    
    async def _save_locally(
        self,
        data: bytes,
        subfolder: str,
        filename: Optional[str],
        extension: str
    ) -> str:
        """Save file to local storage"""
        if not filename:
            filename = f"{uuid.uuid4()}.{extension}"
        else:
            filename = sanitize_filename(filename)
            if not filename.endswith(f".{extension}"):
                filename = f"{filename}.{extension}"
        
        folder_path = os.path.join(self.local_path, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, filename)
        
        # Write asynchronously
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_file, file_path, data)
        
        return f"/storage/{subfolder}/{filename}"
    
    def _write_file(self, path: str, data: bytes):
        """Synchronous file write"""
        with open(path, "wb") as f:
            f.write(data)
    
    async def _save_to_google_drive(
        self,
        data: bytes,
        subfolder: str,
        filename: Optional[str],
        extension: str
    ) -> str:
        """Save file to Google Drive"""
        # TODO: Implement Google Drive upload
        # For now, fall back to local storage
        logger.warning("Google Drive storage not implemented, using local storage")
        return await self._save_locally(data, subfolder, filename, extension)
    
    async def get_file(self, path: str) -> bytes:
        """
        Get file from storage.
        
        Args:
            path: Path/URL to file
        
        Returns:
            File bytes
        """
        if path.startswith("/storage/"):
            # Local file
            full_path = os.path.join(self.local_path, path[9:])
            
            if not os.path.exists(full_path):
                raise ProcessingError(f"File not found: {path}")
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._read_file, full_path)
        
        elif path.startswith("http"):
            # Remote file - download it
            return await self._download_file(path)
        
        else:
            raise ProcessingError(f"Invalid file path: {path}")
    
    def _read_file(self, path: str) -> bytes:
        """Synchronous file read"""
        with open(path, "rb") as f:
            return f.read()
    
    async def _download_file(self, url: str) -> bytes:
        """Download file from URL"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as e:
            raise ProcessingError(f"Failed to download file: {e}")
    
    async def delete_file(self, path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            path: Path to file
        
        Returns:
            True if deleted, False if not found
        """
        if path.startswith("/storage/"):
            full_path = os.path.join(self.local_path, path[9:])
            
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        
        return False
    
    async def copy_file(self, source_path: str, dest_subfolder: str, new_filename: Optional[str] = None) -> str:
        """
        Copy a file within storage.
        
        Args:
            source_path: Source path
            dest_subfolder: Destination subfolder
            new_filename: Optional new filename
        
        Returns:
            Path to copied file
        """
        data = await self.get_file(source_path)
        
        if new_filename:
            filename = new_filename
        else:
            filename = os.path.basename(source_path)
        
        extension = filename.split(".")[-1] if "." in filename else "bin"
        
        return await self.save_file(data, dest_subfolder, filename, extension)
    
    def get_absolute_path(self, relative_path: str) -> str:
        """
        Convert relative storage path to absolute path.
        
        Args:
            relative_path: Relative path (e.g., /storage/audio/file.mp3)
        
        Returns:
            Absolute file system path
        """
        if relative_path.startswith("/storage/"):
            return os.path.join(self.local_path, relative_path[9:])
        return relative_path
    
    def get_relative_path(self, absolute_path: str) -> str:
        """
        Convert absolute path to relative storage path.
        
        Args:
            absolute_path: Absolute file system path
        
        Returns:
            Relative storage path
        """
        if absolute_path.startswith(self.local_path):
            relative = absolute_path[len(self.local_path):].lstrip("/")
            return f"/storage/{relative}"
        return absolute_path
    
    async def save_from_url(
        self,
        url: str,
        subfolder: str = "covers",
        filename: Optional[str] = None
    ) -> str:
        """
        Download a file from URL and save to storage.
        
        Args:
            url: Source URL
            subfolder: Destination subfolder
            filename: Optional filename
        
        Returns:
            Path to saved file
        """
        data = await self._download_file(url)
        
        # Determine extension from URL or content type
        extension = "jpg"  # Default
        if "." in url.split("/")[-1]:
            extension = url.split(".")[-1].split("?")[0][:4]
        
        return await self.save_file(data, subfolder, filename, extension)
    
    async def cleanup_temp(self, max_age_hours: int = 24):
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep
        """
        import time
        
        temp_path = os.path.join(self.local_path, "temp")
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(temp_path):
            file_path = os.path.join(temp_path, filename)
            try:
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.debug(f"Cleaned up temp file: {filename}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {e}")
    
    def get_storage_stats(self) -> dict:
        """Get storage usage statistics"""
        stats = {
            "total_size_mb": 0,
            "by_folder": {}
        }
        
        for subfolder in ["audio", "covers", "temp"]:
            folder_path = os.path.join(self.local_path, subfolder)
            if os.path.exists(folder_path):
                size = sum(
                    os.path.getsize(os.path.join(folder_path, f))
                    for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))
                )
                stats["by_folder"][subfolder] = round(size / (1024 * 1024), 2)
                stats["total_size_mb"] += stats["by_folder"][subfolder]
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats

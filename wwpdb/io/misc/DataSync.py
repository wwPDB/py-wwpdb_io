# pylint: disable=logging-fstring-interpolation
# ruff: noqa: UP006,UP045

from __future__ import annotations

import hashlib
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class DataMoveError(Exception):
    """Custom exception for data movement errors."""

    # pylint: disable=unnecessary-pass


class DataMover(ABC):
    """Abstract base class for data movement operations."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize the data mover.

        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            dry_run: If True, simulate operations without actual changes
        """
        self.dry_run = dry_run

    @abstractmethod
    def sync_files(self, source_path: str, destination_path: str, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync files from source to destination.

        Args:
            file_patterns: Optional list of file patterns to sync

        Returns:
            Dictionary containing sync results and statistics
        """
        # pylint: disable=unnecessary-pass

    @abstractmethod
    def verify_integrity(self, source_path: str, destination_path: str, file_path: str) -> bool:
        """
        Verify file integrity after transfer.

        Args:
            file_path: Path to the file to verify

        Returns:
            True if file integrity is verified, False otherwise
        """
        # pylint: disable=unnecessary-pass


class RsyncDataMover(DataMover):
    """Rsync-based data mover with integrity checks and data loss prevention."""

    def __init__(self, dry_run: bool = False, rsync_options: Optional[List[str]] = None):
        """
        Initialize the Rsync data mover.

        Args:
            dry_run: If True, simulate operations without actual changes
            rsync_options: Additional rsync options
        """
        self.dry_run = dry_run
        super().__init__(dry_run)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Default rsync options for safety and integrity
        self.default_options = [
            "-avz",  # archive mode, verbose, compress
            "--update",  # only transfer files that are newer
            "--checksum",  # use checksums instead of mod-time & size
            "--partial",  # keep partially transferred files
            "--progress",  # show progress
            "--stats",  # show file transfer statistics
            "--human-readable",  # human readable numbers
            "--itemize-changes",  # itemize changes
        ]

        if dry_run:
            self.default_options.append("--dry-run")

        self.rsync_options = rsync_options or []
        self.all_options = self.default_options + self.rsync_options

    def _validate_paths(self, source_path: Path, destination_path: Path) -> None:
        """Validate source and destination paths."""
        if not source_path.exists():
            estr = f"Source path does not exist: {source_path}"
            raise DataMoveError(estr)

        if not source_path.is_dir():
            estr = f"Source path is not a directory: {source_path}"
            raise DataMoveError(estr)

        # Create destination directory if it doesn't exist
        if not self.dry_run:
            destination_path.mkdir(parents=True, exist_ok=True)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()  # noqa: S324
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except OSError as e:
            self.logger.error("Error calculating checksum for %s: %s", file_path, e)
            return ""

    def _run_rsync_command(self, source_path: Path, destination_path: Path, additional_options: Optional[List[str]] = None) -> subprocess.CompletedProcess:
        """
        Execute rsync command with proper error handling.

        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            additional_options: Additional rsync options for this specific run

        Returns:
            CompletedProcess object with command results
        """
        options = self.all_options.copy()
        if additional_options:
            options.extend(additional_options)

        # Ensure source path ends with / to sync contents, not the directory itself
        source_str = str(source_path).rstrip("/") + "/"
        destination_str = str(destination_path)

        cmd = ["rsync"] + options + [source_str, destination_str]  # noqa: RUF005

        self.logger.info("Executing rsync command: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=3600,  # 1 hour timeout
            )

            if result.stdout:
                self.logger.debug("Rsync output: %s", result.stdout)
            if result.stderr:
                self.logger.warning("Rsync stderr: %s", result.stderr)

            return result

        except subprocess.TimeoutExpired:
            estr = "Rsync operation timed out"
            raise DataMoveError(estr)  # noqa: B904  pylint: disable=raise-missing-from
        except Exception as e:  # noqa: BLE001
            estr = f"Error executing rsync command: {e}"
            raise DataMoveError(estr)  # noqa: B904  pylint: disable=raise-missing-from

    def sync_files(self, source_path: str, destination_path: str, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync files using rsync with integrity checks.

        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            file_patterns: Optional list of file patterns to include/exclude

        Returns:
            Dictionary containing sync results and statistics
        """
        source_path_obj = Path(source_path)
        destination_path_obj = Path(destination_path)

        self._validate_paths(source_path_obj, destination_path_obj)

        additional_options = []

        # Add include/exclude patterns if specified
        if file_patterns:
            for pattern in file_patterns:
                if pattern.startswith("!"):  # Exclude pattern
                    additional_options.extend(["--exclude", pattern[1:]])
                else:  # Include pattern
                    additional_options.extend(["--include", pattern])

        # Get pre-sync file counts for statistics
        pre_sync_stats = self._get_directory_stats(source_path_obj)

        # Execute rsync
        result = self._run_rsync_command(source_path_obj, destination_path_obj, additional_options)

        # Parse rsync exit code
        success = result.returncode == 0
        if not success:
            error_msg = f"Rsync failed with exit code {result.returncode}: {result.stderr}"
            self.logger.error(error_msg)
            raise DataMoveError(error_msg)

        # Get post-sync statistics
        post_sync_stats = self._get_directory_stats(destination_path_obj) if not self.dry_run else {}

        # Parse rsync output for transfer statistics
        transfer_stats = self._parse_rsync_stats(result.stdout)

        return {
            "success": success,
            "dry_run": self.dry_run,
            "source_path": str(source_path_obj),
            "destination_path": str(destination_path_obj),
            "pre_sync_stats": pre_sync_stats,
            "post_sync_stats": post_sync_stats,
            "transfer_stats": transfer_stats,
            "timestamp": datetime.now().isoformat(),  # noqa: DTZ005
        }

    def verify_integrity(self, source_path: str, destination_path: str, file_path: str) -> bool:
        """
        Verify file integrity by comparing checksums.

        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            file_path: Relative path to the file to verify

        Returns:
            True if file integrity is verified, False otherwise
        """
        source_path_obj = Path(source_path)
        destination_path_obj = Path(destination_path)

        source_file = source_path_obj / file_path
        dest_file = destination_path_obj / file_path

        if not source_file.exists() or not dest_file.exists():
            self.logger.error("File missing for integrity check: %s", file_path)
            return False

        # Compare file sizes first (quick check)
        if source_file.stat().st_size != dest_file.stat().st_size:
            self.logger.error("File size mismatch for %s", file_path)
            return False

        # Compare checksums
        source_checksum = self._calculate_checksum(source_file)
        dest_checksum = self._calculate_checksum(dest_file)

        if source_checksum != dest_checksum:
            self.logger.error("Checksum mismatch for %s", file_path)
            return False

        self.logger.info("Integrity verified for %s", file_path)
        return True

    def get_file_info(self, file_path: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive file information.

        Args:
            file_path: Path to the file (can be absolute or relative to base_path)
            base_path: Base path if file_path is relative

        Returns:
            Dictionary containing file information
        """
        # Handle both absolute and relative paths
        if os.path.isabs(file_path):
            full_path = Path(file_path)
        elif base_path:
            full_path = Path(base_path) / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            return {"exists": False, "path": str(full_path)}

        stat = full_path.stat()

        return {
            "exists": True,
            "path": str(full_path),
            "size": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),  # noqa: DTZ006
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),  # noqa: DTZ006
            "checksum": self._calculate_checksum(full_path),
            "is_file": full_path.is_file(),
            "is_directory": full_path.is_dir(),
            "permissions": oct(stat.st_mode)[-3:],
        }

    def _get_directory_stats(self, path: Path) -> Dict[str, Any]:
        """Get statistics about a directory."""
        if not path.exists():
            return {"exists": False}

        file_count = 0
        dir_count = 0
        total_size = 0

        try:
            for item in path.rglob("*"):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
                elif item.is_dir():
                    dir_count += 1
        except Exception as e:  # noqa: BLE001
            self.logger.warning("Error getting directory stats: %s", e)

        return {
            "exists": True,
            "path": str(path),
            "file_count": file_count,
            "directory_count": dir_count,
            "total_size_bytes": total_size,
            "total_size_human": self._human_readable_size(total_size),
        }

    def _parse_rsync_stats(self, rsync_output: str) -> Dict[str, Any]:
        """Parse rsync statistics from output."""
        stats = {}

        # Look for common rsync statistics patterns
        lines = rsync_output.split("\n")
        for oline in lines:
            line = oline.strip()
            if "sent" in line and "received" in line:
                # Parse: "sent 1,234 bytes  received 567 bytes  890.00 bytes/sec"
                stats["transfer_summary"] = line
            elif line.startswith("Number of files"):
                stats["file_summary"] = line
            elif line.startswith("Total file size"):
                stats["size_summary"] = line

        return stats

    def _human_readable_size(self, size_in_bytes: int) -> str:
        """Convert bytes to human readable format."""
        fsize_in_bytes = float(size_in_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if fsize_in_bytes < 1024:
                return f"{fsize_in_bytes:.1f} {unit}"
            fsize_in_bytes /= 1024
        return f"{fsize_in_bytes:.1f} PB"

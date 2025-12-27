# pylint: disable=redefined-outer-name,protected-access
# ruff: noqa: S101,SLF001
from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from wwpdb.io.misc.DataSync import DataMoveError, RsyncDataMover


@pytest.fixture
def temp_directories() -> Iterator[tuple[str, str]]:
    """Create temporary source and destination directories for testing.

    Yields:
       str: source directory
       str: destination diretcory
    """
    source_dir = tempfile.mkdtemp(prefix="test_source_")
    dest_dir = tempfile.mkdtemp(prefix="test_dest_")

    yield source_dir, dest_dir

    # Cleanup
    shutil.rmtree(source_dir, ignore_errors=True)
    shutil.rmtree(dest_dir, ignore_errors=True)


@pytest.fixture
def sample_files(temp_directories) -> tuple[str, str, dict[str, str], dict[str, str]]:
    """Create sample files with different timestamps for testing.

    Returns:
       Files used in test
    """
    source_dir, dest_dir = temp_directories

    # Create source files
    source_files = {
        "new_file.txt": "This is a new file",
        "updated_file.txt": "This is an updated file - new version",
        "outdated_file.txt": "This is an outdated file",
    }

    # Create destination files with different timestamps
    dest_files = {"updated_file.txt": "This is an updated file - old version", "outdated_file.txt": "This is an outdated file - newer version"}

    # Write source files
    for filename, content in source_files.items():
        file_path = Path(source_dir) / filename
        file_path.write_text(content)

    # Write destination files and manipulate timestamps
    current_time = time.time()

    for filename, content in dest_files.items():
        file_path = Path(dest_dir) / filename
        file_path.write_text(content)

        if filename == "updated_file.txt":
            # Make dest file older than source
            old_time = current_time - 3600  # 1 hour ago
            os.utime(file_path, (old_time, old_time))
        elif filename == "outdated_file.txt":
            # Make dest file newer than source
            source_file = Path(source_dir) / filename
            new_time = current_time + 3600  # 1 hour in future
            os.utime(file_path, (new_time, new_time))
            # Make source file older
            old_time = current_time - 7200  # 2 hours ago
            os.utime(source_file, (old_time, old_time))

    return source_dir, dest_dir, source_files, dest_files


class TestRsyncDataMover:
    """Test suite for RsyncDataMover class."""

    def test_init_default(self):
        """Test RsyncDataMover initialization with default parameters."""
        mover = RsyncDataMover()

        assert not mover.dry_run
        assert "--dry-run" not in mover.all_options
        assert "--update" in mover.all_options
        assert "--checksum" in mover.all_options

    def test_init_with_dry_run(self):
        """Test RsyncDataMover initialization with dry run enabled."""
        mover = RsyncDataMover(dry_run=True)

        assert mover.dry_run
        assert "--dry-run" in mover.all_options

    def test_init_with_custom_rsync_options(self):
        """Test RsyncDataMover initialization with custom rsync options."""
        custom_options = ["--delete", "--compress-level=9"]

        mover = RsyncDataMover(rsync_options=custom_options)

        for option in custom_options:
            assert option in mover.all_options

    def test_validate_paths_nonexistent_source(self, temp_directories):
        """Test that validation fails when source directory doesn't exist."""
        _source_dir, dest_dir = temp_directories
        nonexistent_source = "/nonexistent/source/path"

        mover = RsyncDataMover()

        with pytest.raises(DataMoveError, match="Source path does not exist"):
            mover._validate_paths(Path(nonexistent_source), Path(dest_dir))

    def test_validate_paths_source_is_file(self, temp_directories):
        """Test that validation fails when source path is a file, not directory."""
        source_dir, dest_dir = temp_directories

        # Create a file instead of directory
        source_file = Path(source_dir) / "not_a_directory.txt"
        source_file.write_text("I am a file, not a directory")

        mover = RsyncDataMover()

        with pytest.raises(DataMoveError, match="Source path is not a directory"):
            mover._validate_paths(source_file, Path(dest_dir))

    def test_validate_paths_creates_destination(self):
        """Test that validation creates destination directory if it doesn't exist."""
        source_dir = tempfile.mkdtemp()
        dest_dir = Path(tempfile.gettempdir()) / "test_dest_create"

        try:
            # Ensure destination doesn't exist
            if dest_dir.exists():
                shutil.rmtree(dest_dir)

            mover = RsyncDataMover()
            mover._validate_paths(Path(source_dir), dest_dir)

            assert dest_dir.exists()
            assert dest_dir.is_dir()
        finally:
            shutil.rmtree(source_dir, ignore_errors=True)
            shutil.rmtree(dest_dir, ignore_errors=True)

    def test_calculate_checksum(self, temp_directories):
        """Test checksum calculation for files."""
        source_dir, _ = temp_directories
        test_file = Path(source_dir) / "checksum_test.txt"
        test_content = "This is test content for checksum"
        test_file.write_text(test_content)

        mover = RsyncDataMover()
        checksum1 = mover._calculate_checksum(test_file)
        checksum2 = mover._calculate_checksum(test_file)

        # Same file should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 32  # MD5 hash length
        assert checksum1 != ""  # noqa: PLC1901

    @patch("subprocess.run")
    def test_sync_files_successful_dry_run(self, mock_subprocess, sample_files):
        """Test successful file sync in dry run mode."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Mock successful rsync execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "sending incremental file list\n./\nnew_file.txt\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover(dry_run=True)
        result = mover.sync_files(source_dir, dest_dir)

        assert result["success"]
        assert result["dry_run"]
        assert result["source_path"] == source_dir
        assert result["destination_path"] == dest_dir
        assert "transfer_stats" in result
        assert "pre_sync_stats" in result

        # Verify rsync was called with correct arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]  # First positional argument (command)
        assert "rsync" in call_args
        assert "--dry-run" in call_args
        assert "--update" in call_args
        assert "--checksum" in call_args

    @patch("subprocess.run")
    def test_sync_files_with_file_patterns(self, mock_subprocess, sample_files):
        """Test sync with specific file patterns."""
        source_dir, dest_dir, _source_files, _ = sample_files

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "sending incremental file list\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover(dry_run=True)
        patterns = ["*.txt", "!*outdated*"]
        result = mover.sync_files(source_dir, dest_dir, file_patterns=patterns)

        assert result["success"]

        # Check that include/exclude patterns were passed to rsync
        call_args = mock_subprocess.call_args[0][0]
        assert "--include" in call_args
        assert "--exclude" in call_args

    @patch("subprocess.run")
    def test_sync_files_rsync_failure(self, mock_subprocess, temp_directories):
        """Test handling of rsync command failure."""
        source_dir, dest_dir = temp_directories

        # Mock failed rsync execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "rsync: failed to connect to server"
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover()

        with pytest.raises(DataMoveError, match="Rsync failed with exit code 1"):
            mover.sync_files(source_dir, dest_dir)

    def test_verify_integrity_matching_files(self, sample_files):
        """Test integrity verification with matching files."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Copy a file to destination to test integrity
        source_file = Path(source_dir) / "new_file.txt"
        dest_file = Path(dest_dir) / "new_file.txt"
        shutil.copy2(source_file, dest_file)

        mover = RsyncDataMover()
        is_valid = mover.verify_integrity(source_dir, dest_dir, "new_file.txt")

        assert is_valid

    def test_verify_integrity_different_content(self, sample_files):
        """Test integrity verification with different file content."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Create files with different content
        source_file = Path(source_dir) / "test_integrity.txt"
        dest_file = Path(dest_dir) / "test_integrity.txt"

        source_file.write_text("Original content")
        dest_file.write_text("Modified content")

        mover = RsyncDataMover()
        is_valid = mover.verify_integrity(source_dir, dest_dir, "test_integrity.txt")

        assert not is_valid

    def test_verify_integrity_missing_files(self, temp_directories):
        """Test integrity verification with missing files."""
        source_dir, dest_dir = temp_directories

        mover = RsyncDataMover()
        is_valid = mover.verify_integrity(source_dir, dest_dir, "nonexistent.txt")

        assert not is_valid

    def test_verify_integrity_size_mismatch(self, sample_files):
        """Test integrity verification with size mismatch."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Create files with different sizes
        source_file = Path(source_dir) / "size_test.txt"
        dest_file = Path(dest_dir) / "size_test.txt"

        source_file.write_text("Short")
        dest_file.write_text("This is a much longer content that should fail size check")

        mover = RsyncDataMover()
        is_valid = mover.verify_integrity(source_dir, dest_dir, "size_test.txt")

        assert not is_valid

    def test_get_file_info_absolute_path(self, sample_files):
        """Test getting file info with absolute path."""
        source_dir, _dest_dir, _source_files, _ = sample_files
        test_file = Path(source_dir) / "new_file.txt"

        mover = RsyncDataMover()
        file_info = mover.get_file_info(str(test_file))

        assert file_info["exists"]
        assert file_info["is_file"]
        assert file_info["size"] > 0
        assert len(file_info["checksum"]) == 32  # MD5 length

    def test_get_file_info_relative_path(self, sample_files):
        """Test getting file info with relative path and base path."""
        source_dir, _dest_dir, _source_files, _ = sample_files

        mover = RsyncDataMover()
        file_info = mover.get_file_info("new_file.txt", base_path=source_dir)

        assert file_info["exists"]
        assert file_info["is_file"]
        assert file_info["size"] > 0

    def test_get_file_info_nonexistent(self, temp_directories):
        """Test getting file info for non-existent file."""
        source_dir, _dest_dir = temp_directories

        mover = RsyncDataMover()
        file_info = mover.get_file_info("nonexistent.txt", base_path=source_dir)

        assert not file_info["exists"]

    def test_get_directory_stats(self, sample_files):
        """Test directory statistics calculation."""
        source_dir, _dest_dir, source_files, _ = sample_files

        mover = RsyncDataMover()
        stats = mover._get_directory_stats(Path(source_dir))

        assert stats["exists"]
        assert stats["file_count"] == len(source_files)
        assert stats["directory_count"] == 0  # No subdirectories
        assert stats["total_size_bytes"] > 0
        assert "total_size_human" in stats

    def test_get_directory_stats_nonexistent(self, temp_directories):
        """Test directory statistics for non-existent directory."""
        source_dir, _dest_dir = temp_directories
        nonexistent_path = Path(source_dir) / "nonexistent"

        mover = RsyncDataMover()
        stats = mover._get_directory_stats(nonexistent_path)

        assert not stats["exists"]

    def test_human_readable_size(self):
        """Test human readable size conversion."""
        mover = RsyncDataMover()

        assert mover._human_readable_size(512) == "512.0 B"
        assert mover._human_readable_size(1024) == "1.0 KB"
        assert mover._human_readable_size(1024 * 1024) == "1.0 MB"
        assert mover._human_readable_size(1024 * 1024 * 1024) == "1.0 GB"

    @patch("subprocess.run")
    def test_copy_nonexistent_files_in_dest(self, mock_subprocess, sample_files):
        """Test that files not existing in destination are copied."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Mock rsync output showing new file transfer
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "sending incremental file list\n" + ">f+++++++++ new_file.txt\nsent 123 bytes  received 45 bytes  336.00 bytes/sec\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover()
        result = mover.sync_files(source_dir, dest_dir)

        assert result["success"]

        # Verify rsync was called with --update flag (only newer files)
        call_args = mock_subprocess.call_args[0][0]
        assert "--update" in call_args

    @patch("subprocess.run")
    def test_dont_copy_outdated_files(self, mock_subprocess, sample_files):
        """Test that files where destination is newer are not copied."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Mock rsync output showing no transfer for outdated file
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "sending incremental file list\n"  # noqa: ISC003
            + "sent 67 bytes  received 12 bytes  158.00 bytes/sec\n"
            + "Number of files: 3\n"
            + "Number of files transferred: 0\n"
        )
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover()
        result = mover.sync_files(source_dir, dest_dir)

        assert result["success"]

        # Verify --update flag is used (prevents overwriting newer files)
        call_args = mock_subprocess.call_args[0][0]
        assert "--update" in call_args
        assert "--checksum" in call_args  # Also verify by checksum, not just timestamp

    @patch("subprocess.run")
    def test_copy_updated_files_only(self, mock_subprocess, sample_files):
        """Test that only files where source is newer are copied."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Mock rsync output showing selective file transfer
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "sending incremental file list\n"
            ">f.st...... updated_file.txt\n"  # Updated file
            ">f+++++++++ new_file.txt\n"  # New file
            "sent 234 bytes  received 56 bytes  580.00 bytes/sec\n"
            "Number of files: 3\n"
            "Number of files transferred: 2\n"
        )
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover()
        result = mover.sync_files(source_dir, dest_dir)

        assert result["success"]

        # Parse transfer stats to verify selective copying
        transfer_stats = result["transfer_stats"]
        assert "transfer_summary" in transfer_stats

    def test_error_nonexistent_source_directory(self, temp_directories):
        """Test error when source directory doesn't exist."""
        _source_dir, dest_dir = temp_directories
        nonexistent_source = "/path/that/does/not/exist"

        mover = RsyncDataMover()

        with pytest.raises(DataMoveError, match="Source path does not exist"):
            mover.sync_files(nonexistent_source, dest_dir)

    def test_error_nonexistent_destination_parent(self, temp_directories):
        """Test behavior when destination parent directory doesn't exist."""
        source_dir, _dest_dir = temp_directories
        nonexistent_dest = "/path/that/does/not/exist/destination"

        mover = RsyncDataMover()

        # This should work because _validate_paths creates parent directories
        # But let's test the error condition by mocking a filesystem error
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):  # noqa: SIM117
            with pytest.raises(OSError):  # noqa: PT011
                mover.sync_files(source_dir, nonexistent_dest)

    @patch("subprocess.run")
    def test_validate_paths_called_on_sync(self, mock_subprocess, temp_directories):
        """Test that _validate_paths is called during sync_files."""
        source_dir, dest_dir = temp_directories

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "sending incremental file list\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover()

        with patch.object(mover, "_validate_paths") as mock_validate:
            mover.sync_files(source_dir, dest_dir)
            mock_validate.assert_called_once_with(Path(source_dir), Path(dest_dir))

    @patch("subprocess.run")
    def test_rsync_command_construction(self, mock_subprocess, temp_directories):
        """Test that rsync command is constructed correctly with source and dest paths."""
        source_dir, dest_dir = temp_directories

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "sending incremental file list\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mover = RsyncDataMover()
        mover.sync_files(source_dir, dest_dir)

        # Verify rsync command includes correct source and destination
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "rsync"
        assert call_args[-2] == f"{source_dir}/"  # Source with trailing slash
        assert call_args[-1] == dest_dir  # Destination


class TestRsyncDataMoverIntegration:
    """Integration tests that actually execute rsync commands (optional)."""

    @pytest.mark.integration
    def test_real_rsync_execution(self, sample_files):
        """Test actual rsync execution (requires rsync to be installed)."""
        source_dir, dest_dir, _source_files, _ = sample_files

        # Only run if rsync is available
        if not shutil.which("rsync"):
            pytest.skip("rsync not available on system")

        mover = RsyncDataMover(dry_run=True)
        result = mover.sync_files(source_dir, dest_dir)

        assert result["success"]
        assert result["dry_run"]
        assert result["source_path"] == source_dir
        assert result["destination_path"] == dest_dir

    @pytest.mark.integration
    def test_real_file_sync_and_verification(self, sample_files):
        """Test real file sync with integrity verification."""
        source_dir, dest_dir, source_files, _ = sample_files

        if not shutil.which("rsync"):
            pytest.skip("rsync not available on system")

        # Clear destination directory for clean test
        for file in Path(dest_dir).glob("*"):
            file.unlink()

        mover = RsyncDataMover(dry_run=False)
        result = mover.sync_files(source_dir, dest_dir)

        assert result["success"]
        assert result["source_path"] == source_dir
        assert result["destination_path"] == dest_dir

        # Verify files were actually copied
        for filename in source_files:
            dest_file = Path(dest_dir) / filename
            assert dest_file.exists()

            # Verify integrity
            is_valid = mover.verify_integrity(source_dir, dest_dir, filename)
            assert is_valid

    @pytest.mark.integration
    def test_multiple_sync_operations(self, temp_directories):
        """Test using the same mover instance for multiple sync operations."""
        source_dir, dest_dir = temp_directories

        if not shutil.which("rsync"):
            pytest.skip("rsync not available on system")

        # Create multiple source directories
        source_dir2 = tempfile.mkdtemp(prefix="test_source2_")
        dest_dir2 = tempfile.mkdtemp(prefix="test_dest2_")

        try:
            # Create test files in both source directories
            (Path(source_dir) / "file1.txt").write_text("Content 1")
            (Path(source_dir2) / "file2.txt").write_text("Content 2")

            mover = RsyncDataMover(dry_run=True)

            # Sync from first source to first dest
            result1 = mover.sync_files(source_dir, dest_dir)
            assert result1["success"]
            assert result1["source_path"] == source_dir
            assert result1["destination_path"] == dest_dir

            # Sync from second source to second dest using same mover
            result2 = mover.sync_files(source_dir2, dest_dir2)
            assert result2["success"]
            assert result2["source_path"] == source_dir2
            assert result2["destination_path"] == dest_dir2

        finally:
            shutil.rmtree(source_dir2, ignore_errors=True)
            shutil.rmtree(dest_dir2, ignore_errors=True)

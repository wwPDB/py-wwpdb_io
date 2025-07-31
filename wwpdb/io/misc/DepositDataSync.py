import os
import sys
import time
import subprocess
import logging
import hashlib
import click
import django

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from wwpdb.io.locator.PathInfo import PathInfo

os.environ["DJANGO_SETTINGS_MODULE"] = "wwpdb.apps.deposit.settings"
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User


class SyncDirection(Enum):
    TO_DEPOSIT = 'to_deposit'
    FROM_DEPOSIT = 'from_deposit'

    def __str__(self):
        return self.value


@dataclass
class SyncCandidate:
    """Data class representing a candidate for synchronization."""
    deposition_id: str
    sync_direction: SyncDirection


class DataMoveError(Exception):
    """Custom exception for data movement errors."""
    pass


class DataMover(ABC):
    """Abstract base class for data movement operations."""
    
    def __init__(self, source_path: str, destination_path: str, dry_run: bool = False):
        """
        Initialize the data mover.
        
        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            dry_run: If True, simulate operations without actual changes
        """
        self.source_path = Path(source_path)
        self.destination_path = Path(destination_path)
        self.dry_run = dry_run
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def sync_files(self, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync files from source to destination.
        
        Args:
            file_patterns: Optional list of file patterns to sync
            
        Returns:
            Dictionary containing sync results and statistics
        """
        pass
    
    @abstractmethod
    def verify_integrity(self, file_path: str) -> bool:
        """
        Verify file integrity after transfer.
        
        Args:
            file_path: Path to the file to verify
            
        Returns:
            True if file integrity is verified, False otherwise
        """
        pass


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
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default rsync options for safety and integrity
        self.default_options = [
            '-avz',           # archive mode, verbose, compress
            '--update',       # only transfer files that are newer
            '--checksum',     # use checksums instead of mod-time & size
            '--partial',      # keep partially transferred files
            '--progress',     # show progress
            '--stats',        # show file transfer statistics
            '--human-readable',  # human readable numbers
            '--itemize-changes',  # itemize changes
        ]
        
        if dry_run:
            self.default_options.append('--dry-run')
            
        self.rsync_options = rsync_options or []
        self.all_options = self.default_options + self.rsync_options
        
    def _validate_paths(self, source_path: Path, destination_path: Path) -> None:
        """Validate source and destination paths."""
        if not source_path.exists():
            raise DataMoveError(f"Source path does not exist: {source_path}")
            
        if not source_path.is_dir():
            raise DataMoveError(f"Source path is not a directory: {source_path}")
            
        # Create destination directory if it doesn't exist
        if not self.dry_run:
            destination_path.mkdir(parents=True, exist_ok=True)
            
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def _run_rsync_command(self, source_path: Path, destination_path: Path, 
                          additional_options: Optional[List[str]] = None) -> subprocess.CompletedProcess:
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
        source_str = str(source_path).rstrip('/') + '/'
        destination_str = str(destination_path)
        
        cmd = ['rsync'] + options + [source_str, destination_str]
        
        self.logger.info(f"Executing rsync command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.stdout:
                self.logger.debug(f"Rsync output: {result.stdout}")
            if result.stderr:
                self.logger.warning(f"Rsync stderr: {result.stderr}")
                
            return result
            
        except subprocess.TimeoutExpired:
            raise DataMoveError("Rsync operation timed out")
        except Exception as e:
            raise DataMoveError(f"Error executing rsync command: {e}")
    
    def sync_files(self, source_path: str, destination_path: str, 
                   file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
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
                if pattern.startswith('!'):  # Exclude pattern
                    additional_options.extend(['--exclude', pattern[1:]])
                else:  # Include pattern
                    additional_options.extend(['--include', pattern])
        
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
            'success': success,
            'dry_run': self.dry_run,
            'source_path': str(source_path_obj),
            'destination_path': str(destination_path_obj),
            'pre_sync_stats': pre_sync_stats,
            'post_sync_stats': post_sync_stats,
            'transfer_stats': transfer_stats,
            'timestamp': datetime.now().isoformat()
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
            self.logger.error(f"File missing for integrity check: {file_path}")
            return False
        
        # Compare file sizes first (quick check)
        if source_file.stat().st_size != dest_file.stat().st_size:
            self.logger.error(f"File size mismatch for {file_path}")
            return False
        
        # Compare checksums
        source_checksum = self._calculate_checksum(source_file)
        dest_checksum = self._calculate_checksum(dest_file)
        
        if source_checksum != dest_checksum:
            self.logger.error(f"Checksum mismatch for {file_path}")
            return False
        
        self.logger.info(f"Integrity verified for {file_path}")
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
            return {'exists': False, 'path': str(full_path)}
        
        stat = full_path.stat()
        
        return {
            'exists': True,
            'path': str(full_path),
            'size': stat.st_size,
            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'checksum': self._calculate_checksum(full_path),
            'is_file': full_path.is_file(),
            'is_directory': full_path.is_dir(),
            'permissions': oct(stat.st_mode)[-3:]
        }
    
    def _get_directory_stats(self, path: Path) -> Dict[str, Any]:
        """Get statistics about a directory."""
        if not path.exists():
            return {'exists': False}
        
        file_count = 0
        dir_count = 0
        total_size = 0
        
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
                elif item.is_dir():
                    dir_count += 1
        except Exception as e:
            self.logger.warning(f"Error getting directory stats: {e}")
        
        return {
            'exists': True,
            'path': str(path),
            'file_count': file_count,
            'directory_count': dir_count,
            'total_size_bytes': total_size,
            'total_size_human': self._human_readable_size(total_size)
        }
    
    def _parse_rsync_stats(self, rsync_output: str) -> Dict[str, Any]:
        """Parse rsync statistics from output."""
        stats = {}
        
        # Look for common rsync statistics patterns
        lines = rsync_output.split('\n')
        for line in lines:
            line = line.strip()
            if 'sent' in line and 'received' in line:
                # Parse: "sent 1,234 bytes  received 567 bytes  890.00 bytes/sec"
                stats['transfer_summary'] = line
            elif line.startswith('Number of files'):
                stats['file_summary'] = line
            elif line.startswith('Total file size'):
                stats['size_summary'] = line
        
        return stats
    
    def _human_readable_size(self, size_in_bytes: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.1f} PB"


class DepositDataSync:

    def __init__(self):
        """
        Initialize the deposit data sync.
        
        Args:
            data_mover: DataMover instance for handling file operations
            db_connection: Database connection for querying sync criteria
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pi = PathInfo()
        self.mover = RsyncDataMover(dry_run=False)

    def _get_candidates_by_status(self, status) -> List[str]:
        """Get entries with a specific status from the database."""
        pass

    def _sync_data_to_deposit(self, dep_id: str) -> Dict[str, Any]:
        self.logger.info(f"Syncing deposition data from deposit-ui to deposit {dep_id}")
        source = self.pi.getDepositUIPath(dataSetId=dep_id)
        destin = self.pi.getDepositPath(dataSetId=dep_id)

        return self.mover.sync_files(
            source_path=str(source),
            destination_path=str(destin),
        )

    def _sync_data_from_deposit(self, dep_id: str) -> Dict[str, Any]:
        self.logger.info(f"Syncing deposition data from deposit {dep_id} to deposit-ui")
        source = self.pi.getDepositPath(dataSetId=dep_id)
        destin = self.pi.getDepositUIPath(dataSetId=dep_id)

        return self.mover.sync_files(
            source_path=str(source),
            destination_path=str(destin),
        )

    def _sync_pickles_to_deposit(self, dep_id: str) -> Dict[str, Any]:
        self.logger.info(f"Syncing pickles from deposit-ui to deposit {dep_id}")
        source = self.pi.getDirPath(dataSetId=dep_id, fileSource="pickles")
        destin = os.path.join(os.path.dirname(self.pi.getDepositPath(dataSetId=dep_id)), "temp_files", "deposition-v-200", dep_id)

        return self.mover.sync_files(
            source_path=str(source),
            destination_path=str(destin),
        )

    def _sync_pickles_from_deposit(self, dep_id: str) -> Dict[str, Any]:
        self.logger.info(f"Syncing pickles from deposit {dep_id} to deposit-ui")
        source = os.path.join(os.path.dirname(self.pi.getDepositPath(dataSetId=dep_id)), "temp_files", "deposition-v-200", dep_id)
        destin = self.pi.getDirPath(dataSetId=dep_id, fileSource="pickles")

        return self.mover.sync_files(
            source_path=str(source),
            destination_path=str(destin),
        )

    def sync_single(self, dep_id: str, direction: SyncDirection) -> Dict[str, Any]:
        """
        Execute the synchronization process.
        
        Args:
            dep_id: Deposit ID to sync
            direction: Sync direction (to_deposit or from_deposit)
            
        Returns:
            Dictionary containing sync results and statistics
        """
        self.logger.info("Starting data synchronization")
        try:
            if not dep_id.startswith("D_"):
                raise ValueError("Invalid deposition ID")

            if direction == SyncDirection.TO_DEPOSIT:
                data_status = self._sync_data_to_deposit(dep_id)
                pickle_status = self._sync_pickles_to_deposit(dep_id)
            else:
                data_status = self._sync_data_from_deposit(dep_id)
                pickle_status = self._sync_pickles_from_deposit(dep_id)

            self.logger.info(f"Synchronization completed for {dep_id} in {direction} direction")
            return {
                'success': True,
                'data_sync': data_status,
                'pickle_sync': pickle_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Synchronization failed: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
    
    def sync_expired(self, cutoff_hours: int) -> Dict[str, Any]:
        """
        Sync all depositions that had sessions expired based on the cutoff.
        
        Args:
            cutoff: The cutoff time in hours
            
        Returns:
            Dictionary containing sync results and statistics
        """
        dt = datetime.now() - timedelta(hours=int(cutoff_hours))
        self.logger.info(f"Syncing all deposits expired after {dt}")
        sync_candidates = set()

        try:
            sessions = Session.objects.filter(expire_date__gte=dt)
            for session in sessions:
                try:
                    data = session.get_decoded()
                    if '_auth_user_id' in data:
                        user = User.objects.filter(id=data['_auth_user_id']).first()
                        sync_candidates.add(user.username)
                except Exception as e:
                    self.logger.error(f"Error decoding session data: {e}")

            if not sync_candidates:
                self.logger.info("No expired deposits found for synchronization.")
                return {
                    'success': True,
                    'message': "No expired deposits found for synchronization.",
                    'timestamp': datetime.now().isoformat()
                }
            
            self.logger.info(f"The depositions with expired sessions to sync: {sync_candidates}")
            for dep_id in sync_candidates:
                self.logger.info(f"Syncing deposition {dep_id} to deposit")
                data_status = self._sync_data_to_deposit(dep_id)
                pickle_status = self._sync_pickles_to_deposit(dep_id)

            return {
                'success': True,
                'data_sync': data_status,
                'pickle_sync': pickle_status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Sync expired operation failed: {e}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }


def print_sync_result(result, file=sys.stdout):
    """Print sync result dictionary in a nicely formatted way."""
    
    def print_dict(data, indent=0):
        """Recursively print dictionary with proper indentation."""
        spaces = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{spaces}{key}:", file=file)
                print_dict(value, indent + 1)
            elif isinstance(value, list):
                print(f"{spaces}{key}: {value}", file=file)
            else:
                print(f"{spaces}{key}: {value}", file=file)
    
    print("=" * 50, file=file)
    print("SYNC OPERATION RESULT", file=file)
    print("=" * 50, file=file)
    
    if result.get('success'):
        print("Status: SUCCESS", file=file)
    else:
        print("Status: FAILED", file=file)
        if 'error' in result:
            print(f"Error: {result['error']}", file=file)
    
    print(f"Timestamp: {result.get('timestamp', 'N/A')}", file=file)
    print(file=file)
    
    # Print data sync results if available
    if 'data_sync' in result:
        print("DATA SYNC RESULTS:", file=file)
        print("-" * 30, file=file)
        print_dict(result['data_sync'], 1)
        print(file=file)
    
    # Print pickle sync results if available
    if 'pickle_sync' in result:
        print("PICKLE SYNC RESULTS:", file=file)
        print("-" * 30, file=file)
        print_dict(result['pickle_sync'], 1)
        print(file=file)
    
    print("=" * 50, file=file)


# CLI group
@click.group()
def cli():
    """Deposit Data Sync CLI"""
    pass


# sync-single command
@cli.command()
@click.argument("dep_id", type=str)
@click.argument("direction", type=click.Choice([d.value for d in SyncDirection], case_sensitive=False))
def sync_single(dep_id, direction):
    """
    Sync a single deposit by ID in the specified direction.

    DEP_ID: The deposit ID to sync.
    DIRECTION: The sync direction (upload or download).
    """
    click.echo(f"Syncing deposit {dep_id} in {direction} direction.")
    sync_direction = SyncDirection(direction.lower())
    syncer = DepositDataSync()
    result = syncer.sync_single(dep_id, sync_direction)
    print_sync_result(result)

    if not result['success']:
        sys.exit(1)


# sync-expired command
@cli.command()
@click.argument("cutoff", type=int)
def sync_expired(cutoff):
    """
    Sync all depositions that had sessions expired based on the cutoff.

    CUTOFF: The cutoff time in hours.
    """
    click.echo(f"Syncing all deposits expired after {cutoff} hours ago.")
    syncer = DepositDataSync()
    result = syncer.sync_expired(cutoff)
    print_sync_result(result)

    if not result['success']:
        sys.exit(1)


# Entry point
if __name__ == "__main__":
    cli()
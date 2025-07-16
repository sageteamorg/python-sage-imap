import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sage_imap.exceptions import (
    IMAPDefaultFolderError,
    IMAPFolderExistsError,
    IMAPFolderNotFoundError,
    IMAPFolderOperationError,
)
from sage_imap.helpers.enums import DefaultMailboxes
from sage_imap.services.client import IMAPClient

logger = logging.getLogger(__name__)


@dataclass
class FolderInfo:
    """Information about an IMAP folder."""

    name: str
    delimiter: str = "/"
    attributes: List[str] = None
    exists: bool = True
    selectable: bool = True
    has_children: bool = False
    has_no_children: bool = False
    marked: bool = False
    unmarked: bool = False
    message_count: Optional[int] = None
    recent_count: Optional[int] = None
    unseen_count: Optional[int] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = []


@dataclass
class FolderOperationResult:
    """Result of a folder operation."""

    success: bool
    folder_name: str
    operation: str
    operation_time: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class IMAPFolderService:
    """Enhanced service class for managing IMAP folders.

    Purpose
    -------
    This class provides comprehensive methods to create, rename, delete, list, and
    manage folders in an IMAP mailbox. It includes advanced folder operations,
    validation, monitoring, and integration with the enhanced client.

    Parameters
    ----------
    client : IMAPClient
        An instance of the IMAPClient class used to communicate with the IMAP server.

    Attributes
    ----------
    client : IMAPClient
        The IMAP client instance.
    operation_history : List[FolderOperationResult]
        History of folder operations for monitoring.
    _default_folders : Set[str]
        Set of default folders that should not be deleted.

    Methods
    -------
    create_folder(folder_name: str, parent: Optional[str] = None) -> FolderOperationResult
        Creates a new folder with optional parent hierarchy.
    rename_folder(old_name: str, new_name: str) -> FolderOperationResult
        Renames an existing folder with validation.
    delete_folder(folder_name: str, force: bool = False) -> FolderOperationResult
        Deletes a folder with safety checks.
    list_folders(pattern: str = "*", reference: str = "") -> List[FolderInfo]
        Lists folders with detailed information.
    get_folder_info(folder_name: str) -> FolderInfo
        Gets detailed information about a specific folder.
    folder_exists(folder_name: str) -> bool
        Checks if a folder exists.
    get_folder_hierarchy() -> Dict[str, List[str]]
        Returns the folder hierarchy structure.
    copy_folder_structure(source_folder: str, target_folder: str) -> List[FolderOperationResult]
        Copies folder structure from source to target.
    get_folder_statistics() -> Dict[str, Any]
        Returns statistics about folder operations.

    Example
    -------
    >>> client = IMAPClient('imap.example.com', 'username', 'password')
    >>> folder_service = IMAPFolderService(client)
    >>>
    >>> # Create a folder
    >>> result = folder_service.create_folder('Projects/Work')
    >>> print(f"Success: {result.success}")
    >>>
    >>> # List folders with details
    >>> folders = folder_service.list_folders()
    >>> for folder in folders:
    ...     print(f"Folder: {folder.name}, Messages: {folder.message_count}")
    >>>
    >>> # Get folder hierarchy
    >>> hierarchy = folder_service.get_folder_hierarchy()
    >>> print(f"Hierarchy: {hierarchy}")
    """

    def __init__(self, client: IMAPClient):
        self.client = client
        self.operation_history: List[FolderOperationResult] = []
        self._default_folders = {
            DefaultMailboxes.INBOX.value,
            DefaultMailboxes.SENT.value,
            DefaultMailboxes.DRAFTS.value,
            DefaultMailboxes.TRASH.value,
            DefaultMailboxes.SPAM.value,
            DefaultMailboxes.ARCHIVE.value,
            "INBOX",  # Always protect INBOX
        }
        self._folder_cache: Dict[str, FolderInfo] = {}
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = 300  # 5 minutes

    def _validate_folder_name(self, folder_name: str) -> str:
        """
        Validate and sanitize folder name.

        Parameters
        ----------
        folder_name : str
            The folder name to validate.

        Returns
        -------
        str
            Sanitized folder name.

        Raises
        ------
        ValueError
            If folder name is invalid.
        """
        if not folder_name or not folder_name.strip():
            raise ValueError("Folder name cannot be empty")

        folder_name = folder_name.strip()

        # Check for invalid characters
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "\0"]
        for char in invalid_chars:
            if char in folder_name:
                raise ValueError(f"Folder name cannot contain '{char}'")

        # Check length
        if len(folder_name) > 255:
            raise ValueError("Folder name too long (max 255 characters)")

        return folder_name

    def _is_default_folder(self, folder_name: str) -> bool:
        """Check if folder is a default/system folder."""
        return folder_name in self._default_folders

    def _parse_folder_attributes(self, attributes_str: str) -> List[str]:
        """Parse folder attributes from IMAP response."""
        if not attributes_str:
            return []

        # Remove parentheses and split by space
        attributes_str = attributes_str.strip("()")
        if not attributes_str:
            return []

        return [attr.strip("\\") for attr in attributes_str.split()]

    def _parse_folder_list_response(self, response: List[bytes]) -> List[FolderInfo]:
        """
        Parse folder list response from IMAP server.

        Parameters
        ----------
        response : List[bytes]
            Raw response from IMAP LIST command.

        Returns
        -------
        List[FolderInfo]
            List of parsed folder information.
        """
        folders = []

        for item in response:
            if not item:
                continue

            try:
                # Decode the response
                folder_str = item.decode("utf-8")

                # Parse the LIST response format: (attributes) "delimiter" "name"
                # Example: (\HasNoChildren) "/" "INBOX"
                match = re.match(r'\(([^)]*)\)\s+"([^"]*)"\s+"([^"]*)"', folder_str)
                if not match:
                    # Try alternative format without quotes
                    match = re.match(r"\(([^)]*)\)\s+([^\s]+)\s+(.+)", folder_str)
                    if not match:
                        logger.warning(f"Could not parse folder response: {folder_str}")
                        continue

                attributes_str, delimiter, name = match.groups()
                attributes = self._parse_folder_attributes(attributes_str)

                # Create folder info
                folder_info = FolderInfo(
                    name=name,
                    delimiter=delimiter,
                    attributes=attributes,
                    exists=True,
                    selectable="\\Noselect" not in attributes,
                    has_children="\\HasChildren" in attributes,
                    has_no_children="\\HasNoChildren" in attributes,
                    marked="\\Marked" in attributes,
                    unmarked="\\Unmarked" in attributes,
                )

                folders.append(folder_info)

            except Exception as e:
                logger.warning(f"Error parsing folder response '{item}': {e}")
                continue

        return folders

    def _execute_folder_operation(
        self,
        operation: str,
        folder_name: str,
        operation_func: callable,
        *args,
        **kwargs,
    ) -> FolderOperationResult:
        """
        Execute a folder operation with monitoring and error handling.

        Parameters
        ----------
        operation : str
            Name of the operation.
        folder_name : str
            Name of the folder being operated on.
        operation_func : callable
            Function to execute the operation.
        *args, **kwargs
            Arguments to pass to the operation function.

        Returns
        -------
        FolderOperationResult
            Result of the operation.
        """
        start_time = time.time()

        try:
            result = operation_func(*args, **kwargs)
            operation_time = time.time() - start_time

            operation_result = FolderOperationResult(
                success=True,
                folder_name=folder_name,
                operation=operation,
                operation_time=operation_time,
                details=result if isinstance(result, dict) else None,
            )

            self.operation_history.append(operation_result)
            logger.info(
                f"Successfully completed {operation} on folder '{folder_name}' in {operation_time:.2f}s"
            )

            return operation_result

        except Exception as e:
            operation_time = time.time() - start_time
            error_message = str(e)

            operation_result = FolderOperationResult(
                success=False,
                folder_name=folder_name,
                operation=operation,
                operation_time=operation_time,
                error_message=error_message,
            )

            self.operation_history.append(operation_result)
            logger.error(
                f"Failed {operation} on folder '{folder_name}': {error_message}"
            )

            raise

    def create_folder(
        self, folder_name: str, parent: Optional[str] = None
    ) -> FolderOperationResult:
        """
        Creates a new folder with optional parent hierarchy.

        Parameters
        ----------
        folder_name : str
            The name of the folder to create.
        parent : Optional[str]
            Parent folder name for hierarchical creation.

        Returns
        -------
        FolderOperationResult
            Result of the folder creation operation.

        Raises
        ------
        IMAPFolderExistsError
            If the folder already exists.
        IMAPFolderOperationError
            If the folder creation fails.

        Example
        -------
        >>> result = folder_service.create_folder('Projects', 'Work')
        >>> if result.success:
        ...     print(f"Created folder: {result.folder_name}")
        """

        def _create_folder():
            validated_name = self._validate_folder_name(folder_name)

            # Construct full folder path
            if parent:
                validated_parent = self._validate_folder_name(parent)
                full_path = f"{validated_parent}/{validated_name}"
            else:
                full_path = validated_name

            # Check if folder already exists
            if self.folder_exists(full_path):
                raise IMAPFolderExistsError(f"Folder '{full_path}' already exists.")

            # Create parent folder if it doesn't exist
            if parent and not self.folder_exists(parent):
                logger.info(f"Creating parent folder: {parent}")
                self.create_folder(parent)

            logger.debug(f"Creating folder: {full_path}")
            status, response = self.client.create(full_path)

            if status != "OK":
                error_msg = f"Failed to create folder '{full_path}': {response}"
                raise IMAPFolderOperationError(error_msg)

            # Clear cache
            self._clear_cache()

            return {"full_path": full_path, "parent": parent}

        return self._execute_folder_operation("create", folder_name, _create_folder)

    def rename_folder(self, old_name: str, new_name: str) -> FolderOperationResult:
        """
        Renames an existing folder with comprehensive validation.

        Parameters
        ----------
        old_name : str
            The current name of the folder to be renamed.
        new_name : str
            The new name for the folder.

        Returns
        -------
        FolderOperationResult
            Result of the folder rename operation.

        Raises
        ------
        IMAPFolderNotFoundError
            If the folder to be renamed does not exist.
        IMAPFolderExistsError
            If the new folder name already exists.
        IMAPDefaultFolderError
            If attempting to rename a default folder.
        IMAPFolderOperationError
            If the folder rename operation fails.

        Example
        -------
        >>> result = folder_service.rename_folder('OldProject', 'NewProject')
        >>> print(f"Renamed folder: {result.success}")
        """

        def _rename_folder():
            validated_old = self._validate_folder_name(old_name)
            validated_new = self._validate_folder_name(new_name)

            # Check if source folder exists
            if not self.folder_exists(validated_old):
                raise IMAPFolderNotFoundError(
                    f"Folder '{validated_old}' does not exist."
                )

            # Check if destination already exists
            if self.folder_exists(validated_new):
                raise IMAPFolderExistsError(f"Folder '{validated_new}' already exists.")

            # Prevent renaming default folders
            if self._is_default_folder(validated_old):
                raise IMAPDefaultFolderError(
                    f"Cannot rename default folder '{validated_old}'."
                )

            logger.debug(f"Renaming folder from '{validated_old}' to '{validated_new}'")
            status, response = self.client.rename(validated_old, validated_new)

            if status != "OK":
                response_str = response[0].decode("utf-8") if response else ""
                if "NONEXISTENT" in response_str:
                    raise IMAPFolderNotFoundError(
                        f"Folder '{validated_old}' does not exist."
                    )
                else:
                    raise IMAPFolderOperationError(
                        f"Failed to rename folder: {response_str}"
                    )

            # Clear cache
            self._clear_cache()

            return {"old_name": validated_old, "new_name": validated_new}

        return self._execute_folder_operation("rename", old_name, _rename_folder)

    def delete_folder(
        self, folder_name: str, force: bool = False
    ) -> FolderOperationResult:
        """
        Deletes a folder with comprehensive safety checks.

        Parameters
        ----------
        folder_name : str
            The name of the folder to delete.
        force : bool, optional
            If True, bypasses some safety checks (default: False).

        Returns
        -------
        FolderOperationResult
            Result of the folder deletion operation.

        Raises
        ------
        IMAPFolderNotFoundError
            If the folder does not exist.
        IMAPDefaultFolderError
            If attempting to delete a default folder.
        IMAPFolderOperationError
            If the folder deletion fails.

        Example
        -------
        >>> result = folder_service.delete_folder('TempFolder')
        >>> if result.success:
        ...     print("Folder deleted successfully")
        """

        def _delete_folder():
            validated_name = self._validate_folder_name(folder_name)

            # Check if folder exists
            if not self.folder_exists(validated_name):
                raise IMAPFolderNotFoundError(
                    f"Folder '{validated_name}' does not exist."
                )

            # Prevent deletion of default folders
            if not force and self._is_default_folder(validated_name):
                raise IMAPDefaultFolderError(
                    f"Cannot delete default folder '{validated_name}'."
                )

            # Get folder info to check for children
            folder_info = self.get_folder_info(validated_name)
            if not force and folder_info.has_children:
                raise IMAPFolderOperationError(
                    f"Folder '{validated_name}' has subfolders. Use force=True to delete anyway."
                )

            logger.debug(f"Deleting folder: {validated_name}")
            status, response = self.client.delete(validated_name)

            if status != "OK":
                response_str = response[0].decode("utf-8") if response else ""
                if "NONEXISTENT" in response_str:
                    raise IMAPFolderNotFoundError(
                        f"Folder '{validated_name}' does not exist."
                    )
                else:
                    raise IMAPFolderOperationError(
                        f"Failed to delete folder: {response_str}"
                    )

            # Clear cache
            self._clear_cache()

            return {
                "deleted_folder": validated_name,
                "had_children": folder_info.has_children,
            }

        return self._execute_folder_operation("delete", folder_name, _delete_folder)

    def list_folders(self, pattern: str = "*", reference: str = "") -> List[FolderInfo]:
        """
        Lists folders with detailed information and caching.

        Parameters
        ----------
        pattern : str, optional
            Pattern to match folder names (default: "*" for all folders).
        reference : str, optional
            Reference name for the pattern (default: "").

        Returns
        -------
        List[FolderInfo]
            List of folder information objects.

        Example
        -------
        >>> folders = folder_service.list_folders()
        >>> for folder in folders:
        ...     print(f"Folder: {folder.name}, Selectable: {folder.selectable}")
        """
        # Check cache
        cache_key = f"{reference}:{pattern}"
        if (
            self._cache_expiry
            and datetime.now() < self._cache_expiry
            and cache_key in self._folder_cache
        ):
            return list(self._folder_cache[cache_key])

        try:
            logger.debug(f"Listing folders with pattern: {pattern}")
            status, response = self.client.list(reference, pattern)

            if status != "OK":
                logger.error(f"Failed to list folders: {response}")
                return []

            folders = self._parse_folder_list_response(response)

            # Enrich with additional information
            for folder in folders:
                if folder.selectable:
                    try:
                        # Get message counts
                        status_info = self.client.status(
                            folder.name, "(MESSAGES RECENT UNSEEN)"
                        )
                        if status_info[0] == "OK" and status_info[1]:
                            # Parse status response
                            status_str = status_info[1][0].decode("utf-8")

                            # Extract counts using regex
                            messages_match = re.search(r"MESSAGES (\d+)", status_str)
                            recent_match = re.search(r"RECENT (\d+)", status_str)
                            unseen_match = re.search(r"UNSEEN (\d+)", status_str)

                            if messages_match:
                                folder.message_count = int(messages_match.group(1))
                            if recent_match:
                                folder.recent_count = int(recent_match.group(1))
                            if unseen_match:
                                folder.unseen_count = int(unseen_match.group(1))
                    except Exception as e:
                        logger.debug(
                            f"Could not get status for folder {folder.name}: {e}"
                        )

            # Update cache
            self._folder_cache[cache_key] = folders
            self._cache_expiry = (
                datetime.now()
                .replace(second=0, microsecond=0)
                .replace(minute=(datetime.now().minute + 5) % 60)
            )

            logger.info(f"Listed {len(folders)} folders")
            return folders

        except Exception as e:
            logger.error(f"Exception listing folders: {e}")
            raise IMAPFolderOperationError(f"Failed to list folders: {e}")

    def get_folder_info(self, folder_name: str) -> FolderInfo:
        """
        Gets detailed information about a specific folder.

        Parameters
        ----------
        folder_name : str
            The name of the folder to get information about.

        Returns
        -------
        FolderInfo
            Detailed information about the folder.

        Raises
        ------
        IMAPFolderNotFoundError
            If the folder does not exist.

        Example
        -------
        >>> info = folder_service.get_folder_info('INBOX')
        >>> print(f"Messages: {info.message_count}, Unseen: {info.unseen_count}")
        """
        validated_name = self._validate_folder_name(folder_name)

        # Try to find in recent folder list
        all_folders = self.list_folders()
        for folder in all_folders:
            if folder.name == validated_name:
                return folder

        # If not found, folder doesn't exist
        raise IMAPFolderNotFoundError(f"Folder '{validated_name}' does not exist.")

    def folder_exists(self, folder_name: str) -> bool:
        """
        Checks if a folder exists.

        Parameters
        ----------
        folder_name : str
            The name of the folder to check.

        Returns
        -------
        bool
            True if the folder exists, False otherwise.

        Example
        -------
        >>> if folder_service.folder_exists('INBOX'):
        ...     print("INBOX exists")
        """
        try:
            self.get_folder_info(folder_name)
            return True
        except IMAPFolderNotFoundError:
            return False

    def get_folder_hierarchy(self) -> Dict[str, List[str]]:
        """
        Returns the folder hierarchy structure.

        Returns
        -------
        Dict[str, List[str]]
            Dictionary mapping parent folders to their children.

        Example
        -------
        >>> hierarchy = folder_service.get_folder_hierarchy()
        >>> print(f"Root folders: {hierarchy.get('', [])}")
        """
        folders = self.list_folders()
        hierarchy = {}

        for folder in folders:
            parts = folder.name.split(folder.delimiter)

            if len(parts) == 1:
                # Root level folder
                if "" not in hierarchy:
                    hierarchy[""] = []
                hierarchy[""].append(folder.name)
            else:
                # Nested folder
                parent = folder.delimiter.join(parts[:-1])
                if parent not in hierarchy:
                    hierarchy[parent] = []
                hierarchy[parent].append(folder.name)

        return hierarchy

    def copy_folder_structure(
        self, source_folder: str, target_folder: str
    ) -> List[FolderOperationResult]:
        """
        Copies folder structure from source to target.

        Parameters
        ----------
        source_folder : str
            Source folder to copy structure from.
        target_folder : str
            Target folder to copy structure to.

        Returns
        -------
        List[FolderOperationResult]
            List of results for each folder creation operation.

        Example
        -------
        >>> results = folder_service.copy_folder_structure('Projects', 'Archive/Projects')
        >>> successful = [r for r in results if r.success]
        >>> print(f"Created {len(successful)} folders")
        """
        results = []

        # Get all folders under source
        pattern = f"{source_folder}/*"
        source_folders = self.list_folders(pattern)

        for folder in source_folders:
            # Calculate relative path
            relative_path = folder.name[len(source_folder) :].lstrip("/")
            new_folder_name = f"{target_folder}/{relative_path}"

            try:
                result = self.create_folder(new_folder_name)
                results.append(result)
            except Exception as e:
                result = FolderOperationResult(
                    success=False,
                    folder_name=new_folder_name,
                    operation="copy_structure",
                    operation_time=0.0,
                    error_message=str(e),
                )
                results.append(result)

        return results

    def get_folder_statistics(self) -> Dict[str, Any]:
        """
        Returns comprehensive statistics about folder operations.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing folder statistics.

        Example
        -------
        >>> stats = folder_service.get_folder_statistics()
        >>> print(f"Total folders: {stats['total_folders']}")
        """
        folders = self.list_folders()

        total_messages = sum(f.message_count or 0 for f in folders)
        total_unseen = sum(f.unseen_count or 0 for f in folders)

        # Operation statistics
        successful_ops = [op for op in self.operation_history if op.success]
        failed_ops = [op for op in self.operation_history if not op.success]

        operation_counts = {}
        for op in self.operation_history:
            operation_counts[op.operation] = operation_counts.get(op.operation, 0) + 1

        return {
            "total_folders": len(folders),
            "selectable_folders": len([f for f in folders if f.selectable]),
            "folders_with_children": len([f for f in folders if f.has_children]),
            "total_messages": total_messages,
            "total_unseen_messages": total_unseen,
            "total_operations": len(self.operation_history),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate": (
                (len(successful_ops) / len(self.operation_history) * 100)
                if self.operation_history
                else 0
            ),
            "operation_counts": operation_counts,
            "average_operation_time": (
                sum(op.operation_time for op in self.operation_history)
                / len(self.operation_history)
                if self.operation_history
                else 0
            ),
            "recent_errors": [
                op.error_message for op in self.operation_history[-5:] if not op.success
            ],
        }

    def _clear_cache(self):
        """Clear the folder cache."""
        self._folder_cache.clear()
        self._cache_expiry = None

    def clear_operation_history(self):
        """Clear the operation history."""
        self.operation_history.clear()
        logger.info("Folder operation history cleared")

    def subscribe_folder(self, folder_name: str) -> FolderOperationResult:
        """
        Subscribe to a folder.

        Parameters
        ----------
        folder_name : str
            Name of the folder to subscribe to.

        Returns
        -------
        FolderOperationResult
            Result of the subscription operation.
        """

        def _subscribe():
            validated_name = self._validate_folder_name(folder_name)

            if not self.folder_exists(validated_name):
                raise IMAPFolderNotFoundError(
                    f"Folder '{validated_name}' does not exist."
                )

            status, response = self.client.subscribe(validated_name)

            if status != "OK":
                raise IMAPFolderOperationError(
                    f"Failed to subscribe to folder: {response}"
                )

            return {"subscribed_folder": validated_name}

        return self._execute_folder_operation("subscribe", folder_name, _subscribe)

    def unsubscribe_folder(self, folder_name: str) -> FolderOperationResult:
        """
        Unsubscribe from a folder.

        Parameters
        ----------
        folder_name : str
            Name of the folder to unsubscribe from.

        Returns
        -------
        FolderOperationResult
            Result of the unsubscription operation.
        """

        def _unsubscribe():
            validated_name = self._validate_folder_name(folder_name)

            status, response = self.client.unsubscribe(validated_name)

            if status != "OK":
                raise IMAPFolderOperationError(
                    f"Failed to unsubscribe from folder: {response}"
                )

            return {"unsubscribed_folder": validated_name}

        return self._execute_folder_operation("unsubscribe", folder_name, _unsubscribe)

    def list_subscribed_folders(self) -> List[FolderInfo]:
        """
        Lists subscribed folders.

        Returns
        -------
        List[FolderInfo]
            List of subscribed folders.
        """
        try:
            status, response = self.client.lsub("", "*")

            if status != "OK":
                logger.error(f"Failed to list subscribed folders: {response}")
                return []

            return self._parse_folder_list_response(response)

        except Exception as e:
            logger.error(f"Exception listing subscribed folders: {e}")
            raise IMAPFolderOperationError(f"Failed to list subscribed folders: {e}")

    def get_folder_quota(self, folder_name: str) -> Optional[Dict[str, Any]]:
        """
        Get quota information for a folder (if supported by server).

        Parameters
        ----------
        folder_name : str
            Name of the folder to get quota for.

        Returns
        -------
        Optional[Dict[str, Any]]
            Quota information if available, None otherwise.
        """
        try:
            validated_name = self._validate_folder_name(folder_name)

            # Check if server supports QUOTA extension
            if hasattr(self.client, "getquota"):
                status, response = self.client.getquota(validated_name)

                if status == "OK" and response:
                    # Parse quota response
                    quota_info = {}
                    for item in response:
                        if isinstance(item, bytes):
                            quota_str = item.decode("utf-8")
                            # Parse quota string (implementation depends on server format)
                            quota_info["raw"] = quota_str

                    return quota_info

            return None

        except Exception as e:
            logger.debug(f"Could not get quota for folder {folder_name}: {e}")
            return None

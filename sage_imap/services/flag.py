import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from sage_imap.exceptions import IMAPFlagOperationError
from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.models.message import MessageSet

logger = logging.getLogger(__name__)


@dataclass
class FlagOperationResult:
    """Result of a flag operation."""

    success: bool
    message_count: int
    flags_modified: List[Flag]
    operation_time: float
    error_message: Optional[str] = None
    failed_messages: List[str] = None


class IMAPFlagService:
    """
    Enhanced service class for managing IMAP flags on email messages.

    Purpose
    -------
    This class provides comprehensive methods to add, remove, and manage flags on email
    messages in an IMAP mailbox. It includes bulk operations, validation, performance
    monitoring, and integration with the enhanced email models.

    Parameters
    ----------
    mailbox : IMAPMailboxService
        The mailbox service that provides the connection to the IMAP server.

    Attributes
    ----------
    mailbox : IMAPMailboxService
        The mailbox service instance.
    operation_history : List[FlagOperationResult]
        History of flag operations for monitoring and debugging.

    Methods
    -------
    add_flag(msg_ids: MessageSet, flag: Flag) -> FlagOperationResult
        Adds a specified flag to the given set of messages.
    remove_flag(msg_ids: MessageSet, flag: Flag) -> FlagOperationResult
        Removes a specified flag from the given set of messages.
    bulk_add_flags(msg_ids: MessageSet, flags: List[Flag]) -> List[FlagOperationResult]
        Adds multiple flags to messages in a single operation.
    bulk_remove_flags(msg_ids: MessageSet, flags: List[Flag]) -> List[FlagOperationResult]
        Removes multiple flags from messages in a single operation.
    set_flags(msg_ids: MessageSet, flags: List[Flag]) -> FlagOperationResult
        Sets the exact flags for messages (replaces existing flags).
    get_message_flags(msg_id: str) -> List[Flag]
        Gets the current flags for a specific message.
    sync_flags_with_emails(emails: EmailIterator) -> Dict[str, List[Flag]]
        Synchronizes flags between server and email objects.
    get_operation_statistics() -> Dict[str, Any]
        Returns statistics about flag operations.

    Example
    -------
    >>> mailbox = IMAPMailboxService(client)
    >>> flag_service = IMAPFlagService(mailbox)
    >>> msg_ids = MessageSet("1,2,3")
    >>>
    >>> # Single flag operations
    >>> result = flag_service.add_flag(msg_ids, Flag.SEEN)
    >>> print(f"Success: {result.success}, Messages: {result.message_count}")
    >>>
    >>> # Bulk operations
    >>> results = flag_service.bulk_add_flags(msg_ids, [Flag.FLAGGED, Flag.ANSWERED])
    >>>
    >>> # Set exact flags
    >>> flag_service.set_flags(msg_ids, [Flag.SEEN, Flag.FLAGGED])
    >>>
    >>> # Get statistics
    >>> stats = flag_service.get_operation_statistics()
    >>> print(f"Total operations: {stats['total_operations']}")
    """

    def __init__(self, mailbox: "IMAPMailboxService"):  # type: ignore[name-defined]
        self.mailbox = mailbox
        self.operation_history: List[FlagOperationResult] = []
        self._operation_count = 0
        self._total_operation_time = 0.0

    def _validate_flags(self, flags: Union[Flag, List[Flag]]) -> List[Flag]:
        """
        Validate and normalize flags input.

        Parameters
        ----------
        flags : Union[Flag, List[Flag]]
            Single flag or list of flags to validate.

        Returns
        -------
        List[Flag]
            Validated list of flags.

        Raises
        ------
        ValueError
            If flags are invalid or empty.
        """
        if isinstance(flags, Flag):
            flags = [flags]
        elif not isinstance(flags, list):
            raise ValueError("Flags must be a Flag or list of Flag objects")

        if not flags:
            raise ValueError("At least one flag must be specified")

        # Validate each flag
        for flag in flags:
            if not isinstance(flag, Flag):
                raise ValueError(f"Invalid flag type: {type(flag)}")

        # Remove duplicates while preserving order
        seen = set()
        unique_flags = []
        for flag in flags:
            if flag not in seen:
                seen.add(flag)
                unique_flags.append(flag)

        return unique_flags

    def _validate_message_set(self, msg_ids: MessageSet) -> None:
        """
        Validate message set.

        Parameters
        ----------
        msg_ids : MessageSet
            Message set to validate.

        Raises
        ------
        ValueError
            If message set is invalid.
        """
        if not isinstance(msg_ids, MessageSet):
            raise ValueError("msg_ids must be a MessageSet object")

        if not msg_ids.msg_ids:
            raise ValueError("Message set cannot be empty")

    def _execute_flag_operation(
        self,
        msg_ids: MessageSet,
        flags: List[Flag],
        command: FlagCommand,
        operation_name: str,
    ) -> FlagOperationResult:
        """
        Execute a flag operation with comprehensive error handling and monitoring.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs to modify.
        flags : List[Flag]
            The flags to add or remove.
        command : FlagCommand
            The command to execute (ADD or REMOVE).
        operation_name : str
            Name of the operation for logging.

        Returns
        -------
        FlagOperationResult
            Result of the operation including success status and metrics.
        """
        start_time = time.time()

        try:
            # Validate inputs
            self._validate_message_set(msg_ids)
            validated_flags = self._validate_flags(flags)

            # Ensure mailbox is synchronized
            self.mailbox.check()

            # Execute the operation for each flag
            failed_messages = []
            successful_flags = []

            for flag in validated_flags:
                try:
                    logger.debug(
                        f"{operation_name} flag {flag.value} {command.value} messages: {msg_ids.msg_ids}"
                    )

                    status, response = self.mailbox.client.store(
                        msg_ids.msg_ids, command.value, flag.value
                    )

                    if status != "OK":
                        error_msg = (
                            f"Failed to {command.value} flag {flag.value}: {response}"
                        )
                        logger.error(error_msg)
                        failed_messages.append(f"Flag {flag.value}: {response}")
                    else:
                        successful_flags.append(flag)
                        logger.debug(f"Successfully {command.value} flag {flag.value}")

                except Exception as e:
                    error_msg = (
                        f"Exception during {command.value} flag {flag.value}: {e}"
                    )
                    logger.error(error_msg)
                    failed_messages.append(f"Flag {flag.value}: {str(e)}")

            # Calculate results
            operation_time = time.time() - start_time
            success = len(successful_flags) > 0 and len(failed_messages) == 0
            message_count = (
                len(msg_ids.msg_ids.split(","))
                if isinstance(msg_ids.msg_ids, str)
                else 1
            )

            result = FlagOperationResult(
                success=success,
                message_count=message_count,
                flags_modified=successful_flags,
                operation_time=operation_time,
                error_message="; ".join(failed_messages) if failed_messages else None,
                failed_messages=failed_messages if failed_messages else None,
            )

            # Update statistics
            self._operation_count += 1
            self._total_operation_time += operation_time
            self.operation_history.append(result)

            # Keep only last 100 operations in history
            if len(self.operation_history) > 100:
                self.operation_history = self.operation_history[-100:]

            if success:
                logger.info(
                    f"Successfully {operation_name} {len(successful_flags)} flags on {message_count} messages"
                )
            else:
                logger.warning(
                    f"Partially failed {operation_name}: {len(successful_flags)} successful, {len(failed_messages)} failed"
                )

            return result

        except Exception as e:
            operation_time = time.time() - start_time
            error_msg = f"Exception during {operation_name}: {e}"
            logger.error(error_msg)

            result = FlagOperationResult(
                success=False,
                message_count=0,
                flags_modified=[],
                operation_time=operation_time,
                error_message=error_msg,
            )

            self.operation_history.append(result)
            raise IMAPFlagOperationError(error_msg) from e

    def add_flag(self, msg_ids: MessageSet, flag: Flag) -> FlagOperationResult:
        """
        Adds a specified flag to the given set of messages.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs to which the flag will be added.
        flag : Flag
            The flag to add to the messages.

        Returns
        -------
        FlagOperationResult
            Result of the operation including success status and metrics.

        Example
        -------
        >>> result = flag_service.add_flag(msg_ids, Flag.SEEN)
        >>> if result.success:
        ...     print(f"Added {flag.value} to {result.message_count} messages")
        """
        return self._execute_flag_operation(
            msg_ids, [flag], FlagCommand.ADD, "add_flag"
        )

    def remove_flag(self, msg_ids: MessageSet, flag: Flag) -> FlagOperationResult:
        """
        Removes a specified flag from the given set of messages.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs from which the flag will be removed.
        flag : Flag
            The flag to remove from the messages.

        Returns
        -------
        FlagOperationResult
            Result of the operation including success status and metrics.

        Example
        -------
        >>> result = flag_service.remove_flag(msg_ids, Flag.FLAGGED)
        >>> if not result.success:
        ...     print(f"Failed to remove flag: {result.error_message}")
        """
        return self._execute_flag_operation(
            msg_ids, [flag], FlagCommand.REMOVE, "remove_flag"
        )

    def bulk_add_flags(
        self, msg_ids: MessageSet, flags: List[Flag]
    ) -> List[FlagOperationResult]:
        """
        Adds multiple flags to messages in optimized bulk operations.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs to modify.
        flags : List[Flag]
            List of flags to add to the messages.

        Returns
        -------
        List[FlagOperationResult]
            List of results for each flag operation.

        Example
        -------
        >>> results = flag_service.bulk_add_flags(msg_ids, [Flag.SEEN, Flag.FLAGGED])
        >>> successful = [r for r in results if r.success]
        >>> print(f"Successfully added {len(successful)} flags")
        """
        validated_flags = self._validate_flags(flags)
        results = []

        logger.info(
            f"Bulk adding {len(validated_flags)} flags to messages: {msg_ids.msg_ids}"
        )

        for flag in validated_flags:
            result = self.add_flag(msg_ids, flag)
            results.append(result)

        return results

    def bulk_remove_flags(
        self, msg_ids: MessageSet, flags: List[Flag]
    ) -> List[FlagOperationResult]:
        """
        Removes multiple flags from messages in optimized bulk operations.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs to modify.
        flags : List[Flag]
            List of flags to remove from the messages.

        Returns
        -------
        List[FlagOperationResult]
            List of results for each flag operation.

        Example
        -------
        >>> results = flag_service.bulk_remove_flags(msg_ids, [Flag.SEEN, Flag.FLAGGED])
        >>> failed = [r for r in results if not r.success]
        >>> if failed:
        ...     print(f"Failed to remove {len(failed)} flags")
        """
        validated_flags = self._validate_flags(flags)
        results = []

        logger.info(
            f"Bulk removing {len(validated_flags)} flags from messages: {msg_ids.msg_ids}"
        )

        for flag in validated_flags:
            result = self.remove_flag(msg_ids, flag)
            results.append(result)

        return results

    def set_flags(self, msg_ids: MessageSet, flags: List[Flag]) -> FlagOperationResult:
        """
        Sets the exact flags for messages (replaces existing flags).

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs to modify.
        flags : List[Flag]
            List of flags to set (replaces all existing flags).

        Returns
        -------
        FlagOperationResult
            Result of the operation.

        Example
        -------
        >>> result = flag_service.set_flags(msg_ids, [Flag.SEEN, Flag.FLAGGED])
        >>> print(f"Set flags on {result.message_count} messages")
        """
        validated_flags = self._validate_flags(flags)
        flag_string = " ".join(flag.value for flag in validated_flags)

        start_time = time.time()

        try:
            self._validate_message_set(msg_ids)
            self.mailbox.check()

            logger.debug(f"Setting flags {flag_string} on messages: {msg_ids.msg_ids}")

            status, response = self.mailbox.client.store(
                msg_ids.msg_ids, "FLAGS", f"({flag_string})"
            )

            operation_time = time.time() - start_time
            message_count = (
                len(msg_ids.msg_ids.split(","))
                if isinstance(msg_ids.msg_ids, str)
                else 1
            )

            if status != "OK":
                error_msg = f"Failed to set flags: {response}"
                logger.error(error_msg)
                result = FlagOperationResult(
                    success=False,
                    message_count=message_count,
                    flags_modified=[],
                    operation_time=operation_time,
                    error_message=error_msg,
                )
            else:
                logger.info(
                    f"Successfully set flags {flag_string} on {message_count} messages"
                )
                result = FlagOperationResult(
                    success=True,
                    message_count=message_count,
                    flags_modified=validated_flags,
                    operation_time=operation_time,
                )

            self.operation_history.append(result)
            return result

        except Exception as e:
            operation_time = time.time() - start_time
            error_msg = f"Exception during set_flags: {e}"
            logger.error(error_msg)

            result = FlagOperationResult(
                success=False,
                message_count=0,
                flags_modified=[],
                operation_time=operation_time,
                error_message=error_msg,
            )

            self.operation_history.append(result)
            raise IMAPFlagOperationError(error_msg) from e

    def get_message_flags(self, msg_id: str) -> List[Flag]:
        """
        Gets the current flags for a specific message.

        Parameters
        ----------
        msg_id : str
            The message ID to get flags for.

        Returns
        -------
        List[Flag]
            List of flags currently set on the message.

        Example
        -------
        >>> flags = flag_service.get_message_flags("123")
        >>> if Flag.SEEN in flags:
        ...     print("Message has been read")
        """
        try:
            status, response = self.mailbox.client.fetch(msg_id, "(FLAGS)")

            if status != "OK":
                logger.error(f"Failed to fetch flags for message {msg_id}: {response}")
                return []

            # Parse flags from response
            if response and response[0]:
                flag_data = response[0]
                if isinstance(flag_data, tuple) and len(flag_data) > 1:
                    return EmailMessage.extract_flags(flag_data[1])
                elif isinstance(flag_data, bytes):
                    return EmailMessage.extract_flags(flag_data)

            return []

        except Exception as e:
            logger.error(f"Exception getting flags for message {msg_id}: {e}")
            return []

    def sync_flags_with_emails(self, emails: EmailIterator) -> Dict[str, List[Flag]]:
        """
        Synchronizes flags between server and email objects.

        Parameters
        ----------
        emails : EmailIterator
            Iterator of email messages to synchronize.

        Returns
        -------
        Dict[str, List[Flag]]
            Dictionary mapping message IDs to their current flags.

        Example
        -------
        >>> synced_flags = flag_service.sync_flags_with_emails(email_iterator)
        >>> for msg_id, flags in synced_flags.items():
        ...     print(f"Message {msg_id} has flags: {[f.value for f in flags]}")
        """
        synced_flags = {}

        logger.info(f"Synchronizing flags for {len(emails)} emails")

        for email in emails:
            if email.sequence_number:
                msg_id = str(email.sequence_number)
                server_flags = self.get_message_flags(msg_id)

                # Update email object with server flags
                email.flags = server_flags
                synced_flags[msg_id] = server_flags

                logger.debug(
                    f"Synced flags for message {msg_id}: {[f.value for f in server_flags]}"
                )

        return synced_flags

    def mark_as_read(self, msg_ids: MessageSet) -> FlagOperationResult:
        """Convenience method to mark messages as read."""
        return self.add_flag(msg_ids, Flag.SEEN)

    def mark_as_unread(self, msg_ids: MessageSet) -> FlagOperationResult:
        """Convenience method to mark messages as unread."""
        return self.remove_flag(msg_ids, Flag.SEEN)

    def mark_as_important(self, msg_ids: MessageSet) -> FlagOperationResult:
        """Convenience method to mark messages as important."""
        return self.add_flag(msg_ids, Flag.FLAGGED)

    def mark_as_deleted(self, msg_ids: MessageSet) -> FlagOperationResult:
        """Convenience method to mark messages for deletion."""
        return self.add_flag(msg_ids, Flag.DELETED)

    def archive_messages(self, msg_ids: MessageSet) -> List[FlagOperationResult]:
        """
        Archive messages by removing important flags and marking as read.

        Parameters
        ----------
        msg_ids : MessageSet
            Messages to archive.

        Returns
        -------
        List[FlagOperationResult]
            Results of the archiving operations.
        """
        results = []

        # Mark as read
        results.append(self.mark_as_read(msg_ids))

        # Remove important flag
        results.append(self.remove_flag(msg_ids, Flag.FLAGGED))

        logger.info(f"Archived messages: {msg_ids.msg_ids}")
        return results

    def get_operation_statistics(self) -> Dict[str, Any]:
        """
        Returns comprehensive statistics about flag operations.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing operation statistics.

        Example
        -------
        >>> stats = flag_service.get_operation_statistics()
        >>> print(f"Success rate: {stats['success_rate']:.1f}%")
        """
        if not self.operation_history:
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "success_rate": 0.0,
                "average_operation_time": 0.0,
                "total_messages_processed": 0,
                "total_flags_modified": 0,
                "most_common_flags": {},
                "recent_errors": [],
            }

        successful_ops = [op for op in self.operation_history if op.success]
        failed_ops = [op for op in self.operation_history if not op.success]

        # Calculate flag frequency
        flag_counts = {}
        for op in successful_ops:
            for flag in op.flags_modified:
                flag_counts[flag.value] = flag_counts.get(flag.value, 0) + 1

        # Get recent errors
        recent_errors = [
            {
                "error": op.error_message,
                "flags": [f.value for f in op.flags_modified],
                "message_count": op.message_count,
            }
            for op in self.operation_history[-10:]
            if not op.success
        ]

        return {
            "total_operations": len(self.operation_history),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate": (len(successful_ops) / len(self.operation_history)) * 100,
            "average_operation_time": sum(
                op.operation_time for op in self.operation_history
            )
            / len(self.operation_history),
            "total_messages_processed": sum(op.message_count for op in successful_ops),
            "total_flags_modified": sum(
                len(op.flags_modified) for op in successful_ops
            ),
            "most_common_flags": dict(
                sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)
            ),
            "recent_errors": recent_errors,
        }

    def clear_operation_history(self) -> None:
        """Clear the operation history."""
        self.operation_history.clear()
        self._operation_count = 0
        self._total_operation_time = 0.0
        logger.info("Flag operation history cleared")

    def get_flag_summary(self, emails: EmailIterator) -> Dict[str, int]:
        """
        Get a summary of flag distribution across emails.

        Parameters
        ----------
        emails : EmailIterator
            Iterator of emails to analyze.

        Returns
        -------
        Dict[str, int]
            Dictionary mapping flag names to their counts.
        """
        flag_counts = {}

        for email in emails:
            for flag in email.flags:
                flag_counts[flag.value] = flag_counts.get(flag.value, 0) + 1

        return flag_counts

import email
import logging
from typing import Any, List, Optional

from sage_imap.exceptions import (
    IMAPMailboxCheckError,
    IMAPMailboxClosureError,
    IMAPMailboxDeleteError,
    IMAPMailboxFetchError,
    IMAPMailboxMoveError,
    IMAPMailboxPermanentDeleteError,
    IMAPMailboxSaveSentError,
    IMAPMailboxSelectionError,
    IMAPMailboxStatusError,
    IMAPSearchError,
)
from sage_imap.helpers.email import EmailIterator, EmailMessage
from sage_imap.helpers.flags import FlagCommand, Flags
from sage_imap.helpers.mailbox import DefaultMailboxes, MailboxStatusItems
from sage_imap.helpers.message import MessageParts, MessageSet
from sage_imap.helpers.search import IMAPSearchCriteria

logger = logging.getLogger(__name__)

__all__ = ["IMAPMailboxService"]


class IMAPMailboxService:
    """
    A service class for managing IMAP mailbox operations.

    Purpose
    -------
    This class provides methods to perform various operations on an IMAP mailbox,
    such as selecting, closing, checking, searching, deleting, moving, restoring,
    fetching emails, saving sent emails, and getting mailbox status.

    Parameters
    ----------
    client : object
        The IMAP client object that provides the connection to the IMAP server.

    Example
    -------
    >>> client = IMAPClient('imap.example.com', 'username', 'password')
    >>> mailbox_service = IMAPMailboxService(client)
    >>> mailbox_service.select_mailbox('INBOX')
    >>> msg_ids = mailbox_service.search('ALL')
    >>> mailbox_service.delete_temporarily(MessageSet('1,2,3'))
    >>> mailbox_service.delete_permanently(MessageSet('1,2,3'))
    >>> mailbox_service.move_to_folder(MessageSet('1,2,3'), 'Archive')
    >>> mailbox_service.restore_from_trash(MessageSet('1,2,3'), 'INBOX')
    >>> emails = mailbox_service.fetch(MessageSet('1,2,3'), MessageParts.BODY)
    >>> mailbox_service.save_sent_email(raw_email_bytes)
    >>> status = mailbox_service.get_mailbox_status(
                    'INBOX',
                    MailboxStatusItems.MESSAGES
                )
    """

    def __init__(self, client: "IMAPClient") -> None:  # type: ignore[name-defined]
        self.client = client
        self.select_mailbox()
        self.mailbox: Optional[str] = None

    def __enter__(self) -> "IMAPMailboxService":
        logger.debug("Entering IMAPMailboxService context manager.")
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        logger.debug("Exiting IMAPMailboxService context manager.")
        self.close_mailbox()

    def select_mailbox(self, mailbox: Optional[str] = DefaultMailboxes.INBOX) -> None:
        """
        Selects the specified mailbox.

        Purpose
        -------
        This method selects the specified mailbox for subsequent operations.

        Parameters
        ----------
        mailbox : str, optional
            The name of the mailbox to select (default is DefaultMailboxes.INBOX).

        Raises
        ------
        IMAPMailboxSelectionError
            If the mailbox selection fails.

        Example
        -------
        >>> mailbox_service.select_mailbox('INBOX')
        """
        try:
            logger.debug("Selecting mailbox: %s", mailbox)
            status, _ = self.client.select(mailbox)  # type: ignore[attr-defined]
            if status != "OK":
                logger.error("Failed to select mailbox: %s", status)
                raise IMAPMailboxSelectionError("Failed to select mailbox.")
            self.mailbox = mailbox
            logger.info("Mailbox selected: %s", mailbox)
        except Exception as e:
            logger.error("Failed to select mailbox: %s", e)
            raise IMAPMailboxSelectionError("Failed to select mailbox.") from e

    def close_mailbox(self) -> None:
        """
        Closes the currently selected mailbox.

        Purpose
        -------
        This method closes the currently selected mailbox to ensure all changes are
        saved and the connection is properly terminated.

        Raises
        ------
        IMAPMailboxClosureError
            If the mailbox closure fails.

        Example
        -------
        >>> mailbox_service.close_mailbox()
        """
        if self.mailbox:
            try:
                logger.debug("Closing mailbox: %s", self.mailbox)
                status, _ = self.client.close()  # type: ignore[attr-defined]
                if status != "OK":
                    logger.error("Failed to close mailbox: %s", status)
                    raise IMAPMailboxClosureError("Failed to close mailbox.")
                logger.info("Mailbox closed: %s", self.mailbox)
                self.mailbox = None
            except Exception as e:
                logger.error("Failed to close mailbox: %s", e)
                raise IMAPMailboxClosureError("Failed to close mailbox.") from e

    def check(self) -> None:
        """
        Sends a CHECK command to the IMAP server to synchronize the mailbox.

        Purpose
        -------
        This method sends a CHECK command to the IMAP server to ensure that all changes
        are saved and synchronized.

        Raises
        ------
        IMAPMailboxCheckError
            If the CHECK command fails.

        Example
        -------
        >>> mailbox_service.check()
        """
        try:
            logger.debug("Requesting checkpoint for the currently selected mailbox.")
            status, _ = self.client.check()  # type: ignore[attr-defined]
            if status != "OK":
                logger.error("Failed to perform CHECK command: %s", status)
                raise IMAPMailboxCheckError("IMAP CHECK command failed.")
            logger.info("IMAP CHECK command successful.")
        except Exception as e:
            logger.error("Exception occurred during CHECK command: %s", e)
            raise IMAPMailboxCheckError("IMAP CHECK command failed.") from e

    def search(self, criteria: IMAPSearchCriteria) -> List[str]:
        """
        Searches for emails matching the specified criteria.

        Purpose
        -------
        This method searches for emails in the selected mailbox based on the given
        criteria.

        Parameters
        ----------
        criteria : IMAPSearchCriteria
            The search criteria (e.g., 'ALL', 'UNSEEN').

        Returns
        -------
        List[str]
            A list of message IDs that match the search criteria.

        Raises
        ------
        IMAPSearchError
            If the search operation fails.

        Example
        -------
        >>> msg_ids = mailbox_service.search('ALL')
        """
        try:
            logger.debug("Searching emails with criteria: %s", criteria)
            status, data = self.client.search(
                None, criteria
            )  # type: ignore[attr-defined, line-too-long]
            if status != "OK":
                logger.error("Failed to search emails: %s", data)
                raise IMAPSearchError("Failed to search emails.")
            msg_ids = data[0].split()
            msg_id_strs = [
                msg_id.decode("utf-8") for msg_id in msg_ids
            ]  # Convert bytes to strings
            logger.info("Search successful, found %d emails.", len(msg_id_strs))
            return msg_id_strs
        except Exception as e:
            logger.error("Exception occurred during search: %s", e)
            raise IMAPSearchError("Failed to search emails.") from e

    def delete_temporarily(self, msg_set: MessageSet) -> None:
        """
        Marks messages for deletion and moves them to the trash folder.

        Purpose
        -------
        This method marks the specified messages for deletion and moves them to the
        trash folder.

        Parameters
        ----------
        msg_set : MessageSet
            The set of message IDs to be marked for deletion and moved to the trash
            folder.

        Raises
        ------
        IMAPMailboxDeleteError
            If the deletion or move operation fails.

        Example
        -------
        >>> mailbox_service.delete_temporarily(MessageSet('1,2,3'))
        """
        try:
            logger.debug(
                "Marking messages %s for deletion and moving to %s.",
                msg_set.msg_ids,
                DefaultMailboxes.TRASH,
            )
            # Mark the messages as deleted
            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.ADD, Flags.DELETED
            )  # type: ignore[attr-defined]
            if status != "OK":
                logger.error(
                    "Failed to mark messages %s for deletion: %s",
                    msg_set.msg_ids,
                    status,
                )
                raise IMAPMailboxDeleteError(
                    f"Failed to mark messages {msg_set.msg_ids} for deletion."
                )

            # Move the messages to the trash folder
            self.move_to_folder(msg_set, DefaultMailboxes.TRASH)
            self.check()  # Synchronize with server
        except Exception as e:
            logger.error(
                "Exception occurred while marking messages %s for deletion and moving "
                "to %s: %s",
                msg_set.msg_ids,
                DefaultMailboxes.TRASH,
                e,
            )
            raise IMAPMailboxDeleteError(
                f"Failed to mark messages {msg_set.msg_ids} "
                f"for deletion and move to {DefaultMailboxes.TRASH}."
            ) from e

    def delete_permanently(self, msg_set: MessageSet) -> None:
        """
        Permanently deletes messages marked for deletion.

        Purpose
        -------
        This method permanently deletes the specified messages from the mailbox.

        Parameters
        ----------
        msg_set : MessageSet
            The set of message IDs to be permanently deleted.

        Raises
        ------
        IMAPMailboxPermanentDeleteError
            If the permanent deletion operation fails.

        Example
        -------
        >>> mailbox_service.delete_permanently(MessageSet('1,2,3'))
        """
        try:
            logger.debug("Deleting messages %s permanently.", msg_set.msg_ids)
            self.delete_temporarily(
                msg_set
            )  # Mark the messages as deleted and move to trash

            # Permanently remove messages marked as deleted
            self.client.expunge()  # type: ignore[attr-defined]
            self.check()  # Synchronize with server
            logger.info("Messages %s permanently deleted.", msg_set.msg_ids)
        except Exception as e:
            logger.error(
                "Exception occurred while deleting messages %s permanently: %s",
                msg_set.msg_ids,
                e,
            )
            raise IMAPMailboxPermanentDeleteError(
                f"Failed to permanently delete messages {msg_set.msg_ids}."
            ) from e

    def move_to_folder(self, msg_set: MessageSet, folder: str) -> None:
        """
        Moves messages to the specified folder.

        Purpose
        -------
        This method moves the specified messages to the given folder.

        Parameters
        ----------
        msg_set : MessageSet
            The set of message IDs to be moved.
        folder : str
            The name of the target folder.

        Raises
        ------
        IMAPMailboxMoveError
            If the move operation fails.

        Example
        -------
        >>> mailbox_service.move_to_folder(MessageSet('1,2,3'), 'Archive')
        """
        try:
            logger.debug("Moving messages %s to folder %s.", msg_set.msg_ids, folder)
            status, _ = self.client.copy(
                msg_set.msg_ids, folder
            )  # type: ignore[attr-defined]
            if status != "OK":
                logger.error(
                    "Failed to move messages %s to folder %s: %s",
                    msg_set.msg_ids,
                    folder,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to move messages {msg_set.msg_ids} to folder {folder}."
                )
            # Mark the messages as deleted in the current folder
            status, _ = self.client.store(  # type: ignore[attr-defined]
                msg_set.msg_ids, FlagCommand.ADD, Flags.DELETED
            )
            if status != "OK":
                logger.error(
                    "Failed to mark messages %s for deletion in folder %s: %s",
                    msg_set.msg_ids,
                    folder,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to mark messages {msg_set.msg_ids} "
                    f"for deletion in folder {folder}."
                )

            # Permanently remove messages marked as deleted from the source folder
            self.client.expunge()  # type: ignore[attr-defined]
            self.check()  # Synchronize with server
            logger.info("Messages %s moved to folder %s.", msg_set.msg_ids, folder)
        except Exception as e:
            logger.error(
                "Exception occurred while moving messages %s to folder %s: %s",
                msg_set.msg_ids,
                folder,
                e,
            )
            raise IMAPMailboxMoveError(
                f"Failed to move messages {msg_set.msg_ids} to folder {folder}."
            ) from e

    def restore_from_trash(self, msg_set: MessageSet, original_folder: str) -> None:
        """
        Restores messages from the trash to the original folder.

        Purpose
        -------
        This method restores the specified messages from the trash to the original
        folder.

        Parameters
        ----------
        msg_set : MessageSet
            The set of message IDs to be restored.
        original_folder : str
            The name of the original folder to which the messages will be restored.

        Raises
        ------
        IMAPMailboxMoveError
            If the restore operation fails.

        Example
        -------
        >>> mailbox_service.restore_from_trash(MessageSet('1,2,3'), 'INBOX')
        """
        try:
            logger.debug(
                "Restoring messages %s from trash to folder %s.",
                msg_set.msg_ids,
                original_folder,
            )
            self.select_mailbox(DefaultMailboxes.TRASH)
            self.move_to_folder(msg_set, original_folder)
            # Remove the \Deleted flag from the messages in the original folder
            self.select_mailbox(original_folder)
            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.REMOVE, Flags.DELETED
            )  # type: ignore[attr-defined]
            if status != "OK":
                logger.error(
                    "Failed to remove \\Deleted flag from messages %s in folder %s: %s",
                    msg_set.msg_ids,
                    original_folder,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to remove \\Deleted flag from messages {msg_set.msg_ids} "
                    f"in folder {original_folder}."
                )
            self.check()  # Synchronize with server
            logger.info(
                "Messages %s restored from trash to folder %s.",
                msg_set.msg_ids,
                original_folder,
            )
        except Exception as e:
            logger.error(
                "Exception occurred while restoring messages %s from trash to "
                "folder %s: %s",
                msg_set.msg_ids,
                original_folder,
                e,
            )
            raise IMAPMailboxMoveError(
                f"Failed to restore messages {msg_set.msg_ids} from trash to "
                f"folder {original_folder}."
            ) from e

    def fetch(self, msg_set: MessageSet, message_part: MessageParts) -> EmailIterator:
        """
        Fetches specified parts of messages.

        Purpose
        -------
        This method fetches the specified parts (e.g., body, headers) of the given
        messages.

        Parameters
        ----------
        msg_set : MessageSet
            The set of message IDs to be fetched.
        message_part : MessageParts
            The part of the message to fetch (e.g., BODY, FLAGS).

        Returns
        -------
        EmailIterator
            An iterator over the fetched email messages.

        Raises
        ------
        Exception
            If the fetch operation fails.

        Example
        -------
        >>> emails = mailbox_service.fetch(MessageSet('1,2,3'), MessageParts.BODY)
        """
        try:
            logger.debug(
                "Fetching message part %s for messages %s.",
                message_part,
                msg_set.msg_ids,
            )
            status, data = self.client.fetch(  # type: ignore[attr-defined]
                msg_set.msg_ids, f"({message_part.value} FLAGS)"
            )
            logger.debug("Raw fetch data: %s", data)  # Log the raw data
            if status != "OK":
                logger.error(
                    "Failed to fetch message part %s for messages %s: %s",
                    message_part,
                    msg_set.msg_ids,
                    status,
                )
                raise IMAPMailboxFetchError(
                    f"Failed to fetch message part {message_part} for "
                    f"messages {msg_set.msg_ids}."
                )

            fetched_data = []
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg_data = response_part[1]
                    msg = email.message_from_bytes(msg_data)
                    # Extract flags
                    flag_data = response_part[0]
                    if b"FLAGS" in flag_data:
                        flags = (
                            flag_data.split(b"FLAGS")[1].strip().decode("utf-8").split()
                        )
                    else:
                        flags = []
                    message_id = msg["Message-ID"]
                    if not message_id:
                        logger.error("Message-ID is missing for message.")
                        continue
                    fetched_data.append(
                        EmailMessage(message_id, msg, flags)
                    )  # Create EmailMessage object with unique Message-ID and flags
            logger.info(
                "Fetched message part %s for messages %s successfully.",
                message_part,
                msg_set.msg_ids,
            )
            return EmailIterator(fetched_data)
        except Exception as e:
            logger.error(
                "Exception occurred while fetching message part %s for messages %s: %s",
                message_part,
                msg_set.msg_ids,
                e,
            )
            raise IMAPMailboxFetchError(
                f"Failed to fetch message part {message_part} for "
                f"messages {msg_set.msg_ids}."
            ) from e

    def save_sent_email(
        self, raw_email: bytes, sent_folder: str = DefaultMailboxes.SENT
    ) -> None:
        """
        Saves a sent email to the specified folder.

        Purpose
        -------
        This method saves the raw sent email data to the specified sent folder.

        Parameters
        ----------
        raw_email : bytes
            The raw email content to be saved.
        sent_folder : str, optional
            The name of the sent folder (default is DefaultMailboxes.SENT).

        Raises
        ------
        IMAPMailboxSaveSentError
            If the save operation fails.

        Example
        -------
        >>> mailbox_service.save_sent_email(raw_email_bytes)
        """
        try:
            logger.debug("Saving sent email to folder: %s", sent_folder)
            if not isinstance(raw_email, (str, bytes)):
                logger.error("Invalid raw email type: %s", type(raw_email))
                raise IMAPMailboxSaveSentError(
                    "Invalid raw email type. Expected string or bytes."
                )

            # Append the email to the specified folder
            status, _ = self.client.append(  # type: ignore[attr-defined]
                sent_folder, None, None, raw_email
            )
            if status != "OK":
                logger.error("Failed to save sent email to folder: %s", status)
                raise IMAPMailboxSaveSentError("Failed to save sent email.")
            logger.info("Sent email saved to folder: %s", sent_folder)
        except Exception as e:
            logger.error("Exception occurred while saving sent email to folder: %s", e)
            raise IMAPMailboxSaveSentError("Failed to save sent email.") from e

    def get_mailbox_status(
        self, *status_items: MailboxStatusItems, mailbox: str = DefaultMailboxes.INBOX
    ) -> str:
        """
        Gets the status of the specified mailbox.

        Purpose
        -------
        This method retrieves the status of the specified mailbox based on the provided
        status items.
        """
        try:
            logger.debug("Getting status for mailbox: %s", mailbox)
            status_items_str = self.__combine_status_items(*status_items)
            status, response = self.client.status(
                mailbox, status_items_str
            )  # type: ignore[attr-defined]
            if status != "OK":
                logger.error("Failed to get status for mailbox: %s", mailbox)
                raise IMAPMailboxStatusError("Failed to get status for mailbox.")
            logger.info("Status for mailbox %s: %s", mailbox, response)
            return response
        except Exception as e:
            logger.error(
                "Exception occurred while getting status for mailbox %s: %s", mailbox, e
            )
            raise IMAPMailboxStatusError("Failed to get status for mailbox.") from e

    def __combine_status_items(self, *status_items: MailboxStatusItems) -> str:
        """
        Combines the status items into a single string.

        Parameters
        ----------
        *status_items : List[MailboxStatusItems]
            The status items to combine.

        Returns
        -------
        str
            The combined status items string.
        """
        return " ".join(item.value for item in status_items)

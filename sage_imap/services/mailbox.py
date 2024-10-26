import email
import logging
import re
from typing import Any, List, Optional, Union

from sage_imap.decorators import mailbox_selection_required
from sage_imap.exceptions import (
    IMAPMailboxCheckError,
    IMAPMailboxClosureError,
    IMAPMailboxDeleteError,
    IMAPMailboxMoveError,
    IMAPMailboxPermanentDeleteError,
    IMAPMailboxSaveSentError,
    IMAPMailboxSelectionError,
    IMAPMailboxStatusError,
    IMAPMailboxUploadError,
    IMAPSearchError,
)
from sage_imap.helpers.enums import (
    DefaultMailboxes,
    Flag,
    FlagCommand,
    MailboxStatusItems,
    MessagePart,
)
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.helpers.typings import Mailbox, MessageIDList, RawEmail
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import IMAPClient

logger = logging.getLogger(__name__)

__all__ = ["IMAPMailboxService"]


class BaseMailboxService:
    def __init__(self, client: IMAPClient) -> None:  # type: ignore[name-defined]
        self.client: IMAPClient = client
        self.current_selection: Optional[str] = None

    def __enter__(self):
        logger.debug("Entering IMAPMailboxService context manager.")
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        logger.debug("Exiting IMAPMailboxService context manager.")
        self.close()

    def select(self, mailbox: Optional[str]):
        if self.current_selection == mailbox:
            return mailbox

        try:
            logger.debug("Selecting mailbox: %s", mailbox)
            status, _ = self.client.select(mailbox)  # type: ignore[attr-defined]
            if status != "OK":
                logger.error("Failed to select mailbox: %s", status)
                raise IMAPMailboxSelectionError("Failed to select mailbox.")
            self.current_selection = mailbox
            logger.info("Mailbox selected: %s", mailbox)
        except Exception as e:
            logger.error("Failed to select mailbox: %s", e)
            raise IMAPMailboxSelectionError("Failed to select mailbox.") from e
        return mailbox

    def close(self):
        if self.current_selection:
            try:
                logger.debug("Closing mailbox: %s", self.current_selection)
                status, _ = self.client.close()  # type: ignore[attr-defined]
                if status != "OK":
                    logger.error("Failed to close mailbox: %s", status)
                    raise IMAPMailboxClosureError("Failed to close mailbox.")
                logger.info("Mailbox closed: %s", self.current_selection)
                self.current_selection = None
            except Exception as e:
                logger.error("Failed to close mailbox: %s", e)
                raise IMAPMailboxClosureError("Failed to close mailbox.") from e

    def check(self):
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

    def status(self, mailbox: Mailbox, *status_items: MailboxStatusItems):
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
        return " ".join(item.value for item in status_items)


class IMAPMailboxService(BaseMailboxService):
    @mailbox_selection_required
    def search(
        self, criteria: IMAPSearchCriteria, charset: Optional[str] = "UTF-8"
    ) -> MessageIDList:
        try:
            logger.debug("Searching emails with criteria: %s", criteria)
            status, data = self.client.search(
                charset, criteria
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

    @mailbox_selection_required
    def trash(self, msg_set: MessageSet, trash_mailbox: Mailbox):
        try:
            logger.debug(
                "Marking messages %s for deletion and moving to %s.",
                msg_set.msg_ids,
                self.current_selection,
            )
            # Mark the messages as deleted
            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.ADD, Flag.DELETED
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
            self.move(msg_set, trash_mailbox)
            self.check()  # Synchronize with server
            # Reselect the original mailbox
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

    def delete(self, msg_set: MessageSet, trash_mailbox: Mailbox):
        try:
            logger.debug("Deleting messages %s permanently.", msg_set.msg_ids)
            self.trash(
                msg_set, trash_mailbox
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

    @mailbox_selection_required
    def move(self, msg_set: MessageSet, destination_mailbox: Mailbox):
        try:
            logger.debug(
                "Moving messages %s to mailbox %s.",
                msg_set.msg_ids,
                destination_mailbox,
            )
            status, _ = self.client.copy(msg_set.msg_ids, destination_mailbox)
            if status != "OK":
                logger.error(
                    "Failed to move messages %s to mailbox %s: %s",
                    msg_set.msg_ids,
                    destination_mailbox,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to move messages {msg_set.msg_ids} to mailbox {destination_mailbox}."
                )
            # Mark the messages as deleted in the current mailbox
            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.ADD, Flag.DELETED
            )
            if status != "OK":
                logger.error(
                    "Failed to mark messages %s for deletion in mailbox %s: %s",
                    msg_set.msg_ids,
                    destination_mailbox,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to mark messages {msg_set.msg_ids} "
                    f"for deletion in mailbox {destination_mailbox}."
                )

            # Permanently remove messages marked as deleted from the source mailbox
            self.client.expunge()  # type: ignore[attr-defined]
            self.check()  # Synchronize with server
            logger.info(
                "Messages %s moved to mailbox %s.", msg_set.msg_ids, destination_mailbox
            )
        except Exception as e:
            logger.error(
                "Exception occurred while moving messages %s to mailbox %s: %s",
                msg_set.msg_ids,
                destination_mailbox,
                e,
            )
            raise IMAPMailboxMoveError(
                f"Failed to move messages {msg_set.msg_ids} to mailbox {destination_mailbox}."
            ) from e

    def restore(
        self, msg_set: MessageSet, trash_mailbox: Mailbox, safe_mailbox: Mailbox
    ):
        try:
            logger.debug(
                "Restoring messages %s from trash to folder %s.",
                msg_set.msg_ids,
                safe_mailbox,
            )
            self.select(trash_mailbox)
            self.move(msg_set, safe_mailbox)
            # Remove the \Deleted flag from the messages in the original folder
            self.select(safe_mailbox)
            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.REMOVE, Flag.DELETED
            )  # type: ignore[attr-defined]
            if status != "OK":
                logger.error(
                    "Failed to remove \\Deleted flag from messages %s in folder %s: %s",
                    msg_set.msg_ids,
                    safe_mailbox,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to remove \\Deleted flag from messages {msg_set.msg_ids} "
                    f"in folder {safe_mailbox}."
                )
            self.check()  # Synchronize with server
            logger.info(
                "Messages %s restored from trash to folder %s.",
                msg_set.msg_ids,
                safe_mailbox,
            )
        except Exception as e:
            logger.error(
                "Exception occurred while restoring messages %s from trash to "
                "folder %s: %s",
                msg_set.msg_ids,
                safe_mailbox,
                e,
            )
            raise IMAPMailboxMoveError(
                f"Failed to restore messages {msg_set.msg_ids} from trash to "
                f"folder {safe_mailbox}."
            ) from e

    @mailbox_selection_required
    def fetch(self, msg_set: MessageSet, msg_part: MessagePart):
        try:
            print(f"Fetching message part {msg_part} for messages {msg_set}.")
            status, data = self.client.fetch(msg_set.msg_ids, f"({msg_part} FLAGS UID)")

            if status != "OK":
                raise Exception(
                    f"Failed to fetch message part {msg_part} for messages {msg_set}."
                )

            fetched_data = []
            for response_part in data:
                if isinstance(response_part, tuple):
                    flag_data = response_part[0]
                    msg_data = response_part[1]

                    email_message = EmailMessage.read_from_eml_bytes(msg_data)

                    # Extract flags
                    flags = EmailMessage.extract_flags(flag_data)
                    email_message.flags = flags

                    # Extract sequence number and UID
                    match = re.match(
                        r"(\d+) \(.*FLAGS \([^\)]*\) UID (\d+)", flag_data.decode()
                    )

                    if match:
                        email_message.sequence_number = int(match.group(1))
                        email_message.uid = int(match.group(2))

                    # Set the size of the email
                    email_message.size = len(msg_data)

                    fetched_data.append(email_message)

            print(
                f"Fetched message part {msg_part} for messages {msg_set} successfully."
            )
            return fetched_data
        except Exception as e:
            print(
                f"Exception occurred while fetching message part {msg_part} for messages {msg_set}: {e}"
            )
            raise Exception(
                f"Failed to fetch message part {msg_part} for messages {msg_set}."
            ) from e

    @mailbox_selection_required
    def save_sent(
        self,
        sent_mailbox: Mailbox,
        raw: RawEmail,
        flags: Flag = None,
        date_time: str = None,
    ):
        try:
            logger.debug("Saving sent email to folder: %s", Mailbox)
            if not isinstance(raw, (str, bytes)):
                logger.error("Invalid raw email type: %s", type(raw))
                raise IMAPMailboxSaveSentError(
                    "Invalid raw email type. Expected string or bytes."
                )

            # Append the email to the specified folder
            status, _ = self.client.append(  # type: ignore[attr-defined]
                sent_mailbox, flags, date_time, raw
            )
            if status != "OK":
                logger.error("Failed to save sent email to folder: %s", status)
                raise IMAPMailboxSaveSentError("Failed to save sent email.")
            logger.info("Sent email saved to folder: %s", sent_mailbox)
        except Exception as e:
            logger.error("Exception occurred while saving sent email to folder: %s", e)
            raise IMAPMailboxSaveSentError("Failed to save sent email.") from e

    @mailbox_selection_required
    def upload_eml(
        self,
        emails: Union[EmailIterator, List[EmailMessage]],
        flags: Flag,
        mailbox: Mailbox,
    ):
        try:
            if not isinstance(emails, (list, EmailIterator)):
                raise TypeError("emails must be a list or an EmailIterator")
            if not isinstance(mailbox, Mailbox):
                raise TypeError("mailbox must be a Mailbox instance")

            email_count = (
                len(emails) if isinstance(emails, list) else "an unknown number of"
            )
            logger.debug("Uploading .eml %s files to mailbox: %s", email_count, mailbox)

            for email_message in emails:
                if not isinstance(email_message, EmailMessage):
                    raise TypeError("Each email must be an EmailMessage instance")

                if not hasattr(email_message, "date") or not hasattr(
                    email_message, "raw"
                ):
                    raise ValueError("Each email must have 'date' and 'raw' attributes")

                status, _ = self.client.append(
                    mailbox, flags, email_message.date, email_message.raw
                )

                if status != "OK":
                    logger.error("Failed to upload .eml file to mailbox: %s", mailbox)
                    raise IMAPMailboxUploadError("Failed to upload .eml file.")

            logger.info("All .eml files uploaded to mailbox: %s", mailbox)

        except Exception as e:
            logger.error(
                "Exception occurred while uploading .eml files to mailbox: %s", e
            )
            raise IMAPMailboxUploadError("Failed to upload .eml files.") from e


class IMAPMailboxUIDService(BaseMailboxService):
    @mailbox_selection_required
    def uid_search(
        self, criteria: IMAPSearchCriteria, charset: Optional[str] = "UTF-8"
    ) -> MessageIDList:
        try:
            logger.debug("Searching emails with criteria: %s", criteria)
            status, data = self.client.uid("SEARCH", charset, criteria)  # type: ignore[attr-defined, line-too-long]
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

    @mailbox_selection_required
    def uid_trash(self, msg_set: MessageSet, trash_mailbox: Mailbox):
        try:
            logger.debug(
                "Marking messages %s for deletion and moving to %s.",
                msg_set.msg_ids,
                self.current_selection,
            )
            # Mark the messages as deleted
            status, _ = self.client.uid("STORE", msg_set.msg_ids, "+FLAGS", Flag.DELETED)  # type: ignore[attr-defined]
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
            self.uid_move(msg_set, trash_mailbox)
            self.check()  # Synchronize with server
            # Reselect the original mailbox
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

    def uid_delete(self, msg_set: MessageSet, trash_mailbox: Mailbox):
        try:
            logger.debug("Deleting messages %s permanently.", msg_set.msg_ids)
            self.uid_trash(
                msg_set, trash_mailbox
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

    @mailbox_selection_required
    def uid_move(self, msg_set: MessageSet, destination_mailbox: Mailbox):
        try:
            logger.debug(
                "Moving messages %s to mailbox %s.",
                msg_set.msg_ids,
                destination_mailbox,
            )
            status, _ = self.client.uid("COPY", msg_set.msg_ids, destination_mailbox)
            if status != "OK":
                logger.error(
                    "Failed to move messages %s to mailbox %s: %s",
                    msg_set.msg_ids,
                    destination_mailbox,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to move messages {msg_set.msg_ids} to mailbox {destination_mailbox}."
                )
            # Mark the messages as deleted in the current mailbox
            status, _ = self.client.uid(
                "STORE", msg_set.msg_ids, "+FLAGS", Flag.DELETED
            )
            if status != "OK":
                logger.error(
                    "Failed to mark messages %s for deletion in mailbox %s: %s",
                    msg_set.msg_ids,
                    destination_mailbox,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to mark messages {msg_set.msg_ids} "
                    f"for deletion in mailbox {destination_mailbox}."
                )

            # Permanently remove messages marked as deleted from the source mailbox
            self.client.expunge()  # type: ignore[attr-defined]
            self.check()  # Synchronize with server
            logger.info(
                "Messages %s moved to mailbox %s.", msg_set.msg_ids, destination_mailbox
            )
        except Exception as e:
            logger.error(
                "Exception occurred while moving messages %s to mailbox %s: %s",
                msg_set.msg_ids,
                destination_mailbox,
                e,
            )
            raise IMAPMailboxMoveError(
                f"Failed to move messages {msg_set.msg_ids} to mailbox {destination_mailbox}."
            ) from e

    def uid_restore(
        self, msg_set: MessageSet, trash_mailbox: Mailbox, safe_mailbox: Mailbox
    ):
        try:
            logger.debug(
                "Restoring messages %s from trash to folder %s.",
                msg_set.msg_ids,
                safe_mailbox,
            )
            self.select(trash_mailbox)
            self.uid_move(msg_set, safe_mailbox)
            # Remove the \Deleted flag from the messages in the original folder
            self.select(safe_mailbox)
            status, _ = self.client.uid("STORE", msg_set.msg_ids, "-FLAGS", Flag.DELETED)  # type: ignore[attr-defined]
            if status != "OK":
                logger.error(
                    "Failed to remove \\Deleted flag from messages %s in folder %s: %s",
                    msg_set.msg_ids,
                    safe_mailbox,
                    status,
                )
                raise IMAPMailboxMoveError(
                    f"Failed to remove \\Deleted flag from messages {msg_set.msg_ids} "
                    f"in folder {safe_mailbox}."
                )
            self.check()  # Synchronize with server
            logger.info(
                "Messages %s restored from trash to folder %s.",
                msg_set.msg_ids,
                safe_mailbox,
            )
        except Exception as e:
            logger.error(
                "Exception occurred while restoring messages %s from trash to "
                "folder %s: %s",
                msg_set.msg_ids,
                safe_mailbox,
                e,
            )
            raise IMAPMailboxMoveError(
                f"Failed to restore messages {msg_set.msg_ids} from trash to "
                f"folder {safe_mailbox}."
            ) from e

    @mailbox_selection_required
    def uid_fetch(self, msg_set: MessageSet, msg_part: MessagePart):
        try:
            print(f"Fetching message part {msg_part} for messages {msg_set}.")
            status, data = self.client.uid(
                "FETCH", msg_set.msg_ids, f"({msg_part} FLAGS UID)"
            )

            if status != "OK":
                raise Exception(
                    f"Failed to fetch message part {msg_part} for messages {msg_set}."
                )

            breakpoint()
            fetched_data = []
            for response_part in data:
                if isinstance(response_part, tuple):
                    flag_data = response_part[0]
                    msg_data = response_part[1]

                    email_message = EmailMessage.read_from_eml_bytes(msg_data)

                    # Extract flags
                    flags = EmailMessage.extract_flags(flag_data)
                    email_message.flags = flags

                    # Extract sequence number and UID
                    match = re.match(
                        r"(\d+) \(UID (\d+) FLAGS \([^\)]*\)", flag_data.decode()
                    )

                    if match:
                        email_message.sequence_number = int(match.group(1))
                        email_message.uid = int(match.group(2))

                    # Set the size of the email
                    email_message.size = len(msg_data)

                    fetched_data.append(email_message)

            print(
                f"Fetched message part {msg_part} for messages {msg_set} successfully."
            )
            return fetched_data
        except Exception as e:
            print(
                f"Exception occurred while fetching message part {msg_part} for messages {msg_set}: {e}"
            )
            raise Exception(
                f"Failed to fetch message part {msg_part} for messages {msg_set}."
            ) from e

import logging

from sage_imap.exceptions import IMAPFlagOperationError
from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.message import MessageSet

logger = logging.getLogger(__name__)


class IMAPFlagService:
    """
    A service class for managing IMAP flags on email messages.

    Purpose
    -------
    This class provides methods to add or remove flags on email messages in an IMAP
    mailbox.
    It handles the interaction with the IMAP server and ensures that flag operations are
    performed correctly.

    Parameters
    ----------
    mailbox : object
        The mailbox object that provides the connection to the IMAP server.

    Methods
    -------
    add_flag(msg_ids: MessageSet, flag: Flags)
        Adds a specified flag to the given set of messages.
    remove_flag(msg_ids: MessageSet, flag: Flags)
        Removes a specified flag from the given set of messages.

    Example
    -------
    >>> mailbox = IMAPMailbox()  # Assume IMAPMailbox is a predefined class
    >>> flag_service = IMAPFlagService(mailbox)
    >>> msg_ids = MessageSet("1,2,3")
    >>> flag_service.add_flag(msg_ids, Flag.SEEN)
    >>> flag_service.remove_flag(msg_ids, Flag.FLAGGED)
    """

    def __init__(self, mailbox: "IMAPMailboxService"):  # type: ignore[name-defined]
        self.mailbox = mailbox

    def _modify_flag(
        self, msg_ids: MessageSet, flag: Flag, command: FlagCommand
    ) -> None:
        """
        Modifies the specified flag on the given set of messages using the provided
        command.

        Purpose
        -------
        This method is a utility function that adds or removes a flag from the specified
        messages based on the given command. It interacts with the IMAP server to
        perform the operation and handles any errors that occur.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs to modify.
        flag : Flags
            The flag to add or remove.
        command : FlagCommand
            The command to execute (either add or remove the flag).

        Raises
        ------
        IMAPFlagOperationError
            If the flag operation fails.

        Example
        -------
        >>> flag_service._modify_flag(msg_ids, Flag.SEEN, FlagCommand.ADD)
        """
        self.mailbox.check()
        try:
            logger.debug(
                "%s flag %s to/from messages: %s",
                command.value,
                flag.value,
                msg_ids.msg_ids,
            )
            status, response = self.mailbox.client.store(  # type: ignore[attr-defined]
                msg_ids.msg_ids, command.value, flag.value
            )
            if status != "OK":
                logger.error(
                    "Failed to %s flag %s to/from messages: %s",
                    command.value,
                    flag.value,
                    response,
                )
                raise IMAPFlagOperationError(
                    f"Failed to {command.value} flag {flag.value} to/from messages"
                    f" {msg_ids.msg_ids}."
                )
            logger.info(
                "Successfully %s flag %s to/from messages: %s",
                command.value,
                flag.value,
                msg_ids.msg_ids,
            )
        except Exception as e:
            logger.error(
                "Exception occurred while %s flag %s to/from messages %s: %s",
                command.value,
                flag.value,
                msg_ids.msg_ids,
                e,
            )
            raise IMAPFlagOperationError(
                f"Failed to {command.value} flag {flag.value} to/from messages "
                f"{msg_ids.msg_ids}."
            ) from e

    def add_flag(self, msg_ids: MessageSet, flag: Flag) -> None:
        """
        Adds a specified flag to the given set of messages.

        Purpose
        -------
        This method adds a specified flag (e.g., \\Seen, \\Flagged) to the specified
        set of messages in the mailbox.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs to which the flag will be added.
        flag : Flags
            The flag to add to the messages.

        Example
        -------
        >>> flag_service.add_flag(msg_ids, Flag.SEEN)
        """
        self._modify_flag(msg_ids, flag, FlagCommand.ADD)

    def remove_flag(self, msg_ids: MessageSet, flag: Flag) -> None:
        """
        Removes a specified flag from the given set of messages.

        Purpose
        -------
        This method removes a specified flag (e.g., \\Seen, \\Flagged) from the
        specified set of messages in the mailbox.

        Parameters
        ----------
        msg_ids : MessageSet
            The set of message IDs from which the flag will be removed.
        flag : Flags
            The flag to remove from the messages.

        Example
        -------
        >>> flag_service.remove_flag(msg_ids, Flag.FLAGGED)
        """
        self._modify_flag(msg_ids, flag, FlagCommand.REMOVE)

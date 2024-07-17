from dataclasses import dataclass, field
from enum import StrEnum

from sage_imap.helpers.typings import MessageSetType


@dataclass
class MessageSet:
    """
    A class to represent a set of email messages by their IDs.

    Purpose
    -------
    This dataclass defines a set of email messages using their unique IDs.
    It supports validation and conversion of message IDs to ensure they are in a correct
    format for IMAP operations.

    Attributes
    ----------
    msg_ids : MessageSetType
        A string of message IDs, which can be a single ID, a comma-separated list, a
        range, or a list of IDs.

    Methods
    -------
    __post_init__():
        Post-initialization method to convert list of IDs to a string and validate the
        message set.
    _convert_list_to_string():
        Converts a list of message IDs to a comma-separated string.
    _validate_message_set():
        Validates the format of the message IDs.
    """

    msg_ids: MessageSetType = field(default_factory=str)

    def __post_init__(self) -> None:
        self._convert_list_to_string()
        self._validate_message_set()

    def _convert_list_to_string(self) -> None:
        """
        Converts a list of message IDs to a comma-separated string.

        Purpose
        -------
        Ensures that the msg_ids attribute is always stored as a comma-separated string,
        which is the expected format for IMAP operations.

        Notes
        -----
        If msg_ids is already a string, this method does nothing. If msg_ids is a list,
        it converts the list to a comma-separated string of message IDs.
        """
        if isinstance(self.msg_ids, list):
            self.msg_ids = ",".join(map(str, self.msg_ids))

    def _validate_message_set(self) -> None:
        """
        Validates the format of the message IDs.

        Purpose
        -------
        Ensures that the msg_ids attribute contains valid message IDs or ranges, which
        is necessary for correct IMAP operations.

        Raises
        ------
        ValueError
            If msg_ids is empty or contains invalid message IDs or ranges.

        Notes
        -----
        This method checks that:
        - msg_ids is not empty.
        - Each message ID is either a single numeric ID, a valid range (e.g., '1:10'),
        - a comma-separated list of these values.
        - For ranges, both start and end IDs are numeric and the start ID is less than
        or equal to the end ID.
        - Supports '1:*' as a valid range from the first message to the last message.
        """
        if not self.msg_ids:
            raise ValueError("Message IDs cannot be empty")

        if isinstance(self.msg_ids, str):
            msg_ids_list = self.msg_ids.split(",")
            for msg_id in msg_ids_list:
                if ":" in msg_id:
                    start, end = msg_id.split(":")
                    if not (
                        (start.isdigit() or start == "1")
                        and (end.isdigit() or end == "*")
                        and (
                            start.isdigit()
                            and end.isdigit()
                            and int(start) <= int(end)
                            or start == "1"
                            and end == "*"
                        )
                    ):
                        raise ValueError(f"Invalid range in message IDs: {msg_id}")
                elif not msg_id.isdigit():
                    raise ValueError(f"Invalid message ID: {msg_id}")
        else:
            raise TypeError("msg_ids should be a string")

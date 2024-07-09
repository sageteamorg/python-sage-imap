from datetime import datetime, timedelta
from enum import StrEnum


class IMAPSearchCriteria(StrEnum):
    """
    An enumeration and utility class for defining IMAP search criteria.

    This class provides various static methods and enum values to construct
    search criteria for querying emails from an IMAP server. It includes both
    predefined criteria (as enum values) and methods to generate dynamic criteria.

    Example
    -------
    >>> criteria = IMAPSearchCriteria.and_criteria(
    ...    IMAPSearchCriteria.recent(7),
    ...    IMAPSearchCriteria.from_address("example@example.com"),
    ...    IMAPSearchCriteria.subject("Meeting")
    ... )
    >>> print(criteria)

    Attributes
    ----------
    ALL : str
        Fetch all messages.
    SEEN : str
        Fetch messages that have been read.
    UNSEEN : str
        Fetch messages that have not been read.
    FLAGGED : str
        Fetch messages that are flagged.
    UNFLAGGED : str
        Fetch messages that are not flagged.
    ANSWERED : str
        Fetch messages that have been answered.
    UNANSWERED : str
        Fetch messages that have not been answered.
    DELETED : str
        Fetch messages that have been deleted.
    UNDELETED : str
        Fetch messages that have not been deleted.
    DRAFT : str
        Fetch messages that are drafts.
    """

    ALL = "ALL"
    SEEN = "SEEN"
    UNSEEN = "UNSEEN"
    FLAGGED = "FLAGGED"
    UNFLAGGED = "UNFLAGGED"
    ANSWERED = "ANSWERED"
    UNANSWERED = "UNANSWERED"
    DELETED = "DELETED"
    UNDELETED = "UNDELETED"
    DRAFT = "DRAFT"

    @staticmethod
    def before(date: str) -> str:
        """
        Generate search criteria for emails before the specified date.

        Parameters
        ----------
        date : str
            The date in "DD-MMM-YYYY" format.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.before("01-Jan-2023")
        >>> print(criteria)  # Output: BEFORE 01-Jan-2023
        """
        return f"BEFORE {date}"

    @staticmethod
    def on(date: str) -> str:
        """
        Generate search criteria for emails on the specified date.

        Parameters
        ----------
        date : str
            The date in "DD-MMM-YYYY" format.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.on("01-Jan-2023")
        >>> print(criteria)  # Output: ON 01-Jan-2023
        """
        return f"ON {date}"

    @staticmethod
    def since(date: str) -> str:
        """
        Generate search criteria for emails since the specified date.

        Parameters
        ----------
        date : str
            The date in "DD-MMM-YYYY" format.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.since("01-Jan-2023")
        >>> print(criteria)  # Output: SINCE 01-Jan-2023
        """
        return f"SINCE {date}"

    @staticmethod
    def from_address(email: str) -> str:
        """
        Generate search criteria for emails from the specified email address.

        Parameters
        ----------
        email : str
            The email address.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.from_address("example@example.com")
        >>> print(criteria)  # Output: FROM "example@example.com"
        """
        return f'FROM "{email}"'

    @staticmethod
    def to_address(email: str) -> str:
        """
        Generate search criteria for emails to the specified email address.

        Parameters
        ----------
        email : str
            The email address.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.to_address("example@example.com")
        >>> print(criteria)  # Output: TO "example@example.com"
        """
        return f'TO "{email}"'

    @staticmethod
    def subject(subject: str) -> str:
        """
        Generate search criteria for emails with the specified subject.

        Parameters
        ----------
        subject : str
            The email subject.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.subject("Meeting")
        >>> print(criteria)  # Output: SUBJECT "Meeting"
        """
        return f'SUBJECT "{subject}"'

    @staticmethod
    def body(text: str) -> str:
        """
        Generate search criteria for emails with the specified body text.

        Parameters
        ----------
        text : str
            The body text.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.body("Project update")
        >>> print(criteria)  # Output: BODY "Project update"
        """
        return f'BODY "{text}"'

    @staticmethod
    def text(text: str) -> str:
        """
        Generate search criteria for emails with the specified text anywhere in the
        email.

        Parameters
        ----------
        text : str
            The text to search for.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.text("Important")
        >>> print(criteria)  # Output: TEXT "Important"
        """
        return f'TEXT "{text}"'

    @staticmethod
    def header(field: str, value: str) -> str:
        """
        Generate search criteria for emails with the specified header field and value.

        Parameters
        ----------
        field : str
            The header field.
        value : str
            The value of the header field.

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.header("X-Priority", "1")
        >>> print(criteria)  # Output: HEADER "X-Priority" "1"
        """
        return f'HEADER "{field}" "{value}"'

    @staticmethod
    def and_criteria(*criteria: str) -> str:
        """
        Combine multiple criteria with a logical AND.

        Parameters
        ----------
        *criteria : str
            The criteria to combine.

        Returns
        -------
        str
            The combined search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.and_criteria(
        ...     IMAPSearchCriteria.seen(),
        ...     IMAPSearchCriteria.from_address("example@example.com")
        ... )
        >>> print(criteria)  # Output: (SEEN FROM "example@example.com")
        """
        return f'({" ".join(criteria)})'

    @staticmethod
    def or_criteria(*criteria: str) -> str:
        """
        Combine multiple criteria with a logical OR.

        Parameters
        ----------
        *criteria : str
            The criteria to combine.

        Returns
        -------
        str
            The combined search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.or_criteria(
        ...     IMAPSearchCriteria.seen(),
        ...     IMAPSearchCriteria.unseen()
        ... )
        >>> print(criteria)  # Output: (OR SEEN UNSEEN)
        """
        return f'(OR {" ".join(criteria)})'

    @staticmethod
    def not_criteria(criteria: str) -> str:
        """
        Negate a criteria.

        Parameters
        ----------
        criteria : str
            The criteria to negate.

        Returns
        -------
        str
            The negated search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.seen())
        >>> print(criteria)  # Output: NOT (SEEN)
        """
        return f"NOT ({criteria})"

    @staticmethod
    def recent(days: int = 7) -> str:
        """
        Generate search criteria for recent emails within the specified number of days.

        Parameters
        ----------
        days : int, optional
            The number of days to look back (default is 7).

        Returns
        -------
        str
            The constructed search criteria.

        Example
        -------
        >>> criteria = IMAPSearchCriteria.recent(7)
        >>> print(criteria)  # Output: SINCE 24-Jun-2023 (if today is 01-Jul-2023)
        """
        recent_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        return IMAPSearchCriteria.since(recent_date)

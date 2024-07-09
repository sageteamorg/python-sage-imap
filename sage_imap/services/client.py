import imaplib
import logging
import socket
from typing import Optional

from sage_imap.exceptions import (
    IMAPAuthenticationError,
    IMAPConnectionError,
    IMAPUnexpectedError,
)

logger = logging.getLogger(__name__)


class IMAPClient:
    """
    A context manager class for managing IMAP connections.

    Purpose
    -------
    This class provides a convenient way to establish and manage a connection
    to an IMAP server, handling the connection, login, and logout processes
    within a context manager. It ensures proper cleanup and error handling.

    Parameters
    ----------
    host : str
        The hostname of the IMAP server.
    username : str
        The username for logging into the IMAP server.
    password : str
        The password for logging into the IMAP server.

    Attributes
    ----------
    host : str
        The hostname of the IMAP server.
    username : str
        The username for logging into the IMAP server.
    password : str
        The password for logging into the IMAP server.
    connection : imaplib.IMAP4_SSL or None
        The IMAP connection object, initialized to None.

    Methods
    -------
    __enter__()
        Establishes an IMAP connection and logs in.
    __exit__(exc_type, exc_value, traceback)
        Logs out from the IMAP server and closes the connection.

    Example
    -------
    >>> with IMAPClient('imap.example.com', 'username', 'password') as client:
    ...     status, messages = client.select("INBOX")
    ...     # Process messages
    """

    def __init__(self, host: str, username: str, password: str):
        self.host: str = host
        self.username: str = username
        self.password: str = password
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        logger.debug("IMAPClient initialized with host: %s", self.host)

    def __enter__(self) -> imaplib.IMAP4_SSL:
        """
        Establishes an IMAP connection and logs in.

        This method resolves the IMAP server hostname, establishes a secure IMAP
        connection,
        and logs in using the provided username and password. If any error occurs during
        these steps, appropriate custom exceptions are raised.

        Raises
        ------
        IMAPConnectionError
            If there is an issue with resolving the hostname or establishing the
            connection.
        IMAPAuthenticationError
            If login to the IMAP server fails.

        Returns
        -------
        imaplib.IMAP4_SSL
            The established IMAP connection object.
        """
        try:
            logger.debug("Resolving IMAP server hostname: %s", self.host)
            resolved_host = socket.gethostbyname(self.host)
            logger.debug("Resolved hostname to IP: %s", resolved_host)

            logger.debug("Establishing IMAP connection...")
            self.connection = imaplib.IMAP4_SSL(self.host)
            logger.info("IMAP connection established successfully.")
        except socket.gaierror as e:
            logger.error("Failed to resolve hostname: %s", e)
            raise IMAPConnectionError("Failed to resolve hostname.") from e
        except imaplib.IMAP4.error as e:
            logger.error("Failed to establish IMAP connection: %s", e)
            raise IMAPConnectionError("Failed to establish IMAP connection.") from e

        try:
            logger.debug("Logging in to IMAP server...")
            self.connection.login(self.username, self.password)
            logger.info("Logged in to IMAP server successfully.")
        except imaplib.IMAP4.error as e:
            logger.error("IMAP login failed: %s", e)
            raise IMAPAuthenticationError("IMAP login failed.") from e

        return self.connection

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[object],
    ) -> None:
        """
        Logs out from the IMAP server and closes the connection.

        This method logs out from the IMAP server and ensures that the connection is
        properly closed.
        If an error occurs during logout, an appropriate custom exception is raised.

        Parameters
        ----------
        exc_type : type
            The exception type, if an exception was raised.
        exc_value : Exception
            The exception instance, if an exception was raised.
        traceback : traceback
            The traceback object, if an exception was raised.

        Raises
        ------
        IMAPUnexpectedError
            If logout from the IMAP server fails.
        """
        if self.connection:
            try:
                logger.debug("Logging out from IMAP server...")
                self.connection.logout()
                logger.info("Logged out from IMAP server successfully.")
            except imaplib.IMAP4.error as e:
                logger.error("IMAP logout failed: %s", e)
                raise IMAPUnexpectedError("IMAP logout failed.") from e
        else:
            logger.debug("No connection to logout from.")

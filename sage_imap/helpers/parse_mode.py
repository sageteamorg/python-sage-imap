"""Email body/header parsing depth for FETCH results."""

from enum import StrEnum


class ParseMode(StrEnum):
    """
    Controls how much of a fetched RFC822 message is parsed into :class:`EmailMessage`.

    FULL
        Parse headers, bodies, and attachments (default).
    HEADERS
        Parse headers and metadata only; skip body walk and attachments.
    MINIMAL
        Message-ID, Subject, From, Date, and size only.
    RAW
        Keep raw bytes only; no MIME parsing.
    """

    FULL = "full"
    HEADERS = "headers"
    MINIMAL = "minimal"
    RAW = "raw"

from _typeshed import Incomplete
from pathlib import Path
from sage_imap.exceptions import EmailException as EmailException
from sage_imap.helpers.email import AutoResponseSuppress as AutoResponseSuppress, ContentTransferEncoding as ContentTransferEncoding, ContentType as ContentType, Priority as Priority, SpamResult as SpamResult
from typing import Any

EmailAddress = str
HeaderDict = dict[str, str]
AttachmentList = list[Path]

class SmartEmailMessage:
    subject: Incomplete
    body: Incomplete
    body_html: Incomplete
    from_email: Incomplete
    to: Incomplete
    cc: Incomplete
    bcc: Incomplete
    attachments: Incomplete
    message_id: Incomplete
    date: Incomplete
    originating_ip: Incomplete
    has_attach: str
    received_header: Incomplete
    default_headers: Incomplete
    extra_headers: Incomplete
    def __init__(self, subject: str, body: str, from_email: EmailAddress | None = None, to: list[EmailAddress] | None = None, cc: list[EmailAddress] | None = None, bcc: list[EmailAddress] | None = None, extra_headers: HeaderDict | None = None, body_html: str | None = None, **kwargs: Any) -> None: ...
    def update_attachment_status(self) -> None: ...
    content_type: str
    content_transfer_encoding: Incomplete
    def update_content_type_and_encoding(self) -> None: ...
    def merge_headers(self, extra_headers: HeaderDict) -> HeaderDict: ...
    def validate_headers(self) -> None: ...
    def send(self, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str, use_tls: bool = True, use_ssl: bool = False) -> None: ...

import logging
import os
import re
import smtplib
import socket
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from sage_imap.exceptions import EmailException
from sage_imap.helpers.email import (
    AutoResponseSuppress,
    ContentTransferEncoding,
    ContentType,
    Priority,
    SpamResult,
)

EmailAddress = str
HeaderDict = Dict[str, str]
AttachmentList = List[Path]


class SmartEmailMessage:
    def __init__(
        self,
        subject: str,
        body: str,
        from_email: Optional[EmailAddress] = None,
        to: Optional[List[EmailAddress]] = None,
        cc: Optional[List[EmailAddress]] = None,
        bcc: Optional[List[EmailAddress]] = None,
        extra_headers: Optional[HeaderDict] = None,
        body_html: Optional[str] = None,  # Add body_html parameter
        **kwargs: Any,
    ):
        logging.info("Initializing SmartEmailMessage")
        self.subject = subject
        self.body = body
        self.body_html = body_html  # Store HTML body
        self.from_email = from_email
        self.to = self._sanitize_email_list(to)
        self.cc = self._sanitize_email_list(cc)
        self.bcc = self._sanitize_email_list(bcc)

        self.attachments: AttachmentList = kwargs.get("attachments", [])

        self.message_id = self._generate_message_id()
        self.date = self._generate_date()
        self.originating_ip = self._get_originating_ip()
        self.has_attach = "no"
        self.received_header = self._generate_received_header()

        self.update_attachment_status()
        self.update_content_type_and_encoding()

        self.default_headers: HeaderDict = {
            "MIME-Version": "1.0",
            "Content-Type": self.content_type,
            "Content-Transfer-Encoding": self.content_transfer_encoding,
            "X-Mailer": "sage_imap",
            "List-Unsubscribe": "",
            "Return-Path": "",
            "Received": self.received_header,
            "Message-ID": self.message_id,
            "In-Reply-To": "",
            "References": "",
            "Reply-To": "",
            "X-Originating-IP": self.originating_ip,
            "X-Priority": Priority.NORMAL,
            "X-MS-Has-Attach": self.has_attach,
            "X-Report-Abuse-To": "",
            "X-Spamd-Result": SpamResult.DEFAULT,
            "X-Auto-Response-Suppress": AutoResponseSuppress.ALL,
        }

        self.extra_headers: HeaderDict = self.merge_headers(extra_headers or {})
        self.validate_headers()

    def _generate_message_id(self) -> str:
        logging.debug("Generating message ID")
        return make_msgid()

    def _generate_date(self) -> str:
        logging.debug("Generating date")
        return formatdate(localtime=True)

    def _get_originating_ip(self) -> str:
        logging.debug("Getting originating IP")
        try:
            ip = requests.get("https://api.ipify.org", timeout=5, verify=True).text
            logging.info(f"Originating IP: {ip}")
            return ip
        except requests.RequestException as e:
            logging.error(f"Failed to get originating IP: {e}")
            return "127.0.0.1"

    def update_attachment_status(self) -> None:
        logging.debug("Updating attachment status")
        self.has_attach = "yes" if self.attachments else "no"

    def update_content_type_and_encoding(self) -> None:
        logging.debug("Updating content type and encoding")
        if self.attachments:
            self.content_type = "multipart/mixed"
            self.content_transfer_encoding = ContentTransferEncoding.BASE64
        elif self.body_html:
            self.content_type = "multipart/alternative"
            self.content_transfer_encoding = ContentTransferEncoding.SEVEN_BIT
        else:
            self.content_type = ContentType.PLAIN
            self.content_transfer_encoding = ContentTransferEncoding.SEVEN_BIT

    def _generate_received_header(self) -> str:
        logging.debug("Generating received header")
        try:
            domain = socket.getfqdn()
            header = (
                f"from {domain} (localhost [{self.originating_ip}]) "
                f"by {domain} with ESMTP id {self.message_id} "
                f'for <{", ".join(self.to)}>; {self.date}'
            )
            logging.info(f"Received header: {header}")
            return header
        except socket.error as e:
            logging.error(f"Failed to generate received header: {e}")
            header = (
                f"from localhost (localhost [{self.originating_ip}]) "
                f"by localhost with ESMTP id {self.message_id} "
                f'for <{", ".join(self.to)}>; {self.date}'
            )
            return header

    def merge_headers(self, extra_headers: HeaderDict) -> HeaderDict:
        logging.debug("Merging extra headers with default headers")
        headers = self.default_headers.copy()
        headers.update(extra_headers)
        return headers

    def validate_headers(self) -> None:
        logging.debug("Validating headers")
        priority = self.extra_headers.get("X-Priority")
        if priority and priority != Priority.NORMAL:
            logging.error(f"Invalid X-Priority header value: {priority}")
            raise EmailException(f"Invalid X-Priority header value: {priority}")

        spamd_result = self.extra_headers.get("X-Spamd-Result")
        if spamd_result and spamd_result != SpamResult.DEFAULT:
            logging.error(f"Invalid X-Spamd-Result header value: {spamd_result}")
            raise EmailException(f"Invalid X-Spamd-Result header value: {spamd_result}")

        auto_response_suppress = self.extra_headers.get("X-Auto-Response-Suppress")
        if (
            auto_response_suppress
            and auto_response_suppress != AutoResponseSuppress.ALL
        ):
            logging.error(
                f"Invalid X-Auto-Response-Suppress header value: {auto_response_suppress}"
            )
            raise EmailException(
                f"Invalid X-Auto-Response-Suppress header value: {auto_response_suppress}"
            )

        content_type = self.extra_headers.get("Content-Type")
        valid_content_types = [
            ContentType.PLAIN,
            "multipart/mixed",
            "multipart/alternative",
        ]
        if content_type and content_type not in valid_content_types:
            logging.error(f"Invalid Content-Type header value: {content_type}")
            raise EmailException(f"Invalid Content-Type header value: {content_type}")

        content_transfer_encoding = self.extra_headers.get("Content-Transfer-Encoding")
        valid_encodings = [
            ContentTransferEncoding.SEVEN_BIT,
            ContentTransferEncoding.BASE64,
        ]
        if (
            content_transfer_encoding
            and content_transfer_encoding not in valid_encodings
        ):
            logging.error(
                f"Invalid Content-Transfer-Encoding header value: {content_transfer_encoding}"
            )
            raise EmailException(
                f"Invalid Content-Transfer-Encoding header value: {content_transfer_encoding}"
            )

    def send(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        use_tls: bool = True,  # Default to TLS
        use_ssl: bool = False,
    ) -> None:
        logging.info("Sending email")
        try:
            if self.body_html:
                msg = MIMEMultipart("alternative")
            else:
                msg = MIMEMultipart()

            msg["Subject"] = self.subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to)
            msg["Cc"] = ", ".join(self.cc)
            msg["Date"] = self.date
            msg["Message-ID"] = self.message_id

            for header, value in self.extra_headers.items():
                if value:
                    msg.add_header(header, value)

            msg.attach(MIMEText(self.body, "plain"))
            if self.body_html:
                msg.attach(MIMEText(self.body_html, "html"))

            for attachment_path in self.attachments:
                if not os.path.isfile(attachment_path):
                    logging.error(f"Attachment file does not exist: {attachment_path}")
                    raise EmailException(
                        f"Attachment file does not exist: {attachment_path}"
                    )

                with open(attachment_path, "rb") as file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{os.path.basename(attachment_path)}"',
                    )
                    msg.attach(part)

            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    server.starttls()

            with server:
                server.login(smtp_user, smtp_password)
                server.sendmail(
                    self.from_email, self.to + self.cc + self.bcc, msg.as_string()
                )
            logging.info("Email sent successfully")
        except smtplib.SMTPException as e:
            logging.error(f"SMTP error occurred: {e}")
            raise EmailException(f"Failed to send email: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise EmailException(f"An unexpected error occurred: {e}")

    def _sanitize_email_list(
        self, email_list: Optional[List[EmailAddress]]
    ) -> List[EmailAddress]:
        email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_list:
            return []
        sanitized_list: List[EmailAddress] = []
        for email in email_list:
            sanitized_email = email.strip()
            if not email_regex.match(sanitized_email):
                logging.error(f"Invalid email address: {sanitized_email}")
                raise EmailException(f"Invalid email address: {sanitized_email}")
            sanitized_list.append(sanitized_email)
        return sanitized_list

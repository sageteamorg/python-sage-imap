import logging
import os
import smtplib
import socket
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
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


class SmartEmailMessage:
    def __init__(
        self,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        to: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ):
        logging.info("Initializing SmartEmailMessage")
        self.subject = subject
        self.body = body
        self.from_email = from_email
        self.to = to or []
        self.cc = cc or []
        self.bcc = bcc or []

        # Combine additional attributes into dictionaries
        self.attachments = kwargs.get("attachments", [])

        self.message_id = self._generate_message_id()
        self.date = self._generate_date()
        self.originating_ip = self._get_originating_ip()
        self.has_attach = "no"
        self.received_header = self._generate_received_header()

        self.update_attachment_status()
        self.update_content_type_and_encoding()

        # Default headers
        self.default_headers = {
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
            "X-Priority": Priority.NORMAL.value,
            "X-MS-Has-Attach": self.has_attach,
            "X-Report-Abuse-To": "",
            "X-Spamd-Result": SpamResult.DEFAULT.value,
            "X-Auto-Response-Suppress": AutoResponseSuppress.ALL.value,
        }

        self.extra_headers = self.merge_headers(extra_headers or {})
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
            ip = requests.get("https://api.ipify.org", timeout=5).text
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
            self.content_type = ContentType.MULTIPART.value
            self.content_transfer_encoding = ContentTransferEncoding.BASE64.value
        else:
            self.content_type = ContentType.PLAIN.value
            self.content_transfer_encoding = ContentTransferEncoding.SEVEN_BIT.value

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

    def merge_headers(self, extra_headers: Dict[str, str]) -> Dict[str, str]:
        logging.debug("Merging extra headers with default headers")
        headers = self.default_headers.copy()
        headers.update(extra_headers)
        return headers

    def validate_headers(self) -> None:
        logging.debug("Validating headers")
        priority = self.extra_headers.get("X-Priority")
        if priority and priority not in Priority._value2member_map_:
            logging.error(f"Invalid X-Priority header value: {priority}")
            raise EmailException(f"Invalid X-Priority header value: {priority}")

        spamd_result = self.extra_headers.get("X-Spamd-Result")
        if spamd_result and spamd_result not in SpamResult._value2member_map_:
            logging.error(f"Invalid X-Spamd-Result header value: {spamd_result}")
            raise EmailException(f"Invalid X-Spamd-Result header value: {spamd_result}")

        auto_response_suppress = self.extra_headers.get("X-Auto-Response-Suppress")
        if (
            auto_response_suppress
            and auto_response_suppress not in AutoResponseSuppress._value2member_map_
        ):
            logging.error(
                f"Invalid X-Auto-Response-Suppress header value: {auto_response_suppress}"
            )
            raise EmailException(
                f"Invalid X-Auto-Response-Suppress header value: {auto_response_suppress}"
            )

        content_type = self.extra_headers.get("Content-Type")
        if content_type and content_type not in ContentType._value2member_map_:
            logging.error(f"Invalid Content-Type header value: {content_type}")
            raise EmailException(f"Invalid Content-Type header value: {content_type}")

        content_transfer_encoding = self.extra_headers.get("Content-Transfer-Encoding")
        if (
            content_transfer_encoding
            and content_transfer_encoding
            not in ContentTransferEncoding._value2member_map_
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
        use_tls: bool = False,
        use_ssl: bool = False,
    ) -> None:
        logging.info("Sending email")
        try:
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

            for attachment_path in self.attachments:
                with open(attachment_path, "rb") as file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(attachment_path),
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

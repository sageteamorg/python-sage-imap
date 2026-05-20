#!/usr/bin/env python3
"""Example: sync IMAP ORM (requires python-sage-imap[orm])."""

import os

from sage_imap.orm import ImapAccountConfig, ImapMessage, ImapORM, LoadLevel
from sage_imap.orm.schemas import ImapMessageSummarySchema


def main() -> None:
    config = ImapAccountConfig(
        account_id="demo",
        host=os.environ.get("IMAP_HOST", "localhost"),
        username=os.environ.get("IMAP_USER", "user@example.com"),
        password=os.environ.get("IMAP_PASSWORD", "secret"),
    )
    with ImapORM.open("demo", config=config) as orm:
        orm.select_mailbox("INBOX")
        qs = (
            ImapMessage.objects.filter(unread=True)
            .limit(10)
            .with_load_level(LoadLevel.HEADERS)
        )
        for msg in qs.iter():
            schema = ImapMessageSummarySchema.from_imap_message(msg)
            print(schema.model_dump(mode="json"))


if __name__ == "__main__":
    main()

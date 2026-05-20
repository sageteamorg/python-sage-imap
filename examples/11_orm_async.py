#!/usr/bin/env python3
"""Example: async IMAP ORM (requires python-sage-imap[orm,async])."""

import asyncio
import os

from sage_imap.orm import ImapAccountConfig, ImapMessage, LoadLevel
from sage_imap.orm.async_session import AsyncImapORM


async def main() -> None:
    config = ImapAccountConfig(
        account_id="demo",
        host=os.environ.get("IMAP_HOST", "localhost"),
        username=os.environ.get("IMAP_USER", "user@example.com"),
        password=os.environ.get("IMAP_PASSWORD", "secret"),
    )
    async with AsyncImapORM.open("demo", config=config) as orm:
        await orm.select_mailbox("INBOX")
        qs = (
            ImapMessage.objects.filter(unread=True)
            .limit(5)
            .with_load_level(LoadLevel.HEADERS)
        )
        async for msg in qs.iter_async():
            print(msg.uid, msg.subject)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Example: async IMAP session (requires python-sage-imap[async])."""

import asyncio
import os

from sage_imap.aio import AsyncIMAPSession
from sage_imap.helpers.search import IMAPSearchCriteria


async def main() -> None:
    host = os.environ.get("IMAP_HOST", "localhost")
    user = os.environ.get("IMAP_USER", "user@example.com")
    password = os.environ.get("IMAP_PASSWORD", "secret")

    async with AsyncIMAPSession(
        host, user, password, port=int(os.environ.get("IMAP_PORT", "993"))
    ) as session:
        await session.select("INBOX")
        result = await session.search(IMAPSearchCriteria.ALL)
        if not result.success:
            print("Search failed:", result.error_message)
            return
        msg_set = result.to_uid_message_set()
        count = 0
        async for msg in session.iter_messages(msg_set, batch_size=25):
            count += 1
            print(msg.uid, msg.subject)
        print(f"Fetched {count} messages")


if __name__ == "__main__":
    asyncio.run(main())

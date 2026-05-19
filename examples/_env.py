"""Shared IMAP connection settings for example scripts."""

from __future__ import annotations

import os

IMAP_HOST = os.environ.get("IMAP_HOST", "localhost")
IMAP_USER = os.environ.get("IMAP_USER", "user@example.com")
IMAP_PASSWORD = os.environ.get("IMAP_PASSWORD", "secret")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))


def client_kwargs(**overrides):
    """Keyword arguments for ``IMAPClient`` / ``ConnectionConfig``."""
    base = {
        "host": IMAP_HOST,
        "username": IMAP_USER,
        "password": IMAP_PASSWORD,
        "port": IMAP_PORT,
    }
    base.update(overrides)
    return base

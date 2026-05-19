"""Integration test fixtures (real IMAP server)."""

import os

import pytest

from sage_imap.services.client import IMAPClient


def _imap_configured() -> bool:
    return bool(os.environ.get("IMAP_HOST") and os.environ.get("IMAP_USER"))


pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def imap_config():
    if not _imap_configured():
        pytest.skip("IMAP_HOST and IMAP_USER required for integration tests")
    return {
        "host": os.environ["IMAP_HOST"],
        "port": int(os.environ.get("IMAP_PORT", "993")),
        "username": os.environ["IMAP_USER"],
        "password": os.environ.get("IMAP_PASSWORD", ""),
        "use_ssl": os.environ.get("IMAP_USE_SSL", "true").lower() == "true",
    }


@pytest.fixture
def imap_client(imap_config):
    client = IMAPClient(
        host=imap_config["host"],
        username=imap_config["username"],
        password=imap_config["password"],
        port=imap_config["port"],
        use_ssl=imap_config["use_ssl"],
    )
    client.connect()
    yield client
    client.disconnect()

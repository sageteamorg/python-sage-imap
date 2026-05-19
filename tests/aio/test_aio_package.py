"""Tests for sage_imap.aio package lazy imports."""

import importlib
import sys

import pytest


class TestAioPackageImports:
    def test_missing_extra_raises(self, monkeypatch):
        import sage_imap.aio as aio_pkg

        monkeypatch.setitem(sys.modules, "aioimaplib", None)
        with pytest.raises(ImportError, match="\\[async\\]"):
            aio_pkg.__getattr__("AsyncIMAPClient")

    def test_lazy_import_client(self):
        from sage_imap.aio import AsyncIMAPClient

        assert AsyncIMAPClient.__name__ == "AsyncIMAPClient"

    def test_lazy_import_idle(self):
        from sage_imap.aio import AsyncIMAPIdleSession, AsyncIMAPIdleWatcher

        assert AsyncIMAPIdleSession is not None
        assert AsyncIMAPIdleWatcher is not None

    def test_reload_aio_submodule(self):
        import sage_imap.aio.client as client_mod

        importlib.reload(client_mod)
        assert hasattr(client_mod, "AsyncIMAPClient")

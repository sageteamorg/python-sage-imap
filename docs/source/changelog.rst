.. _changelog:

Changelog
=========

All notable changes are documented here and in `CHANGELOG.md <https://github.com/sageteamorg/python-sage-imap/blob/main/CHANGELOG.md>`_.

Format based on `Keep a Changelog <https://keepachangelog.com/en/1.1.0/>`_,
`Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Changed
~~~~~~~

- Shared sync/async core: ``transport_ops``, ``sync/ops``, ``helpers/folder_list``, async mailbox read-path via ``_ops``.

[2.0.0] - 2026-05-19
--------------------

Added
~~~~~

- **Async API** (``sage_imap.aio``) — ``AsyncIMAPSession``, transport on **aioimaplib**, mailbox/folder/flag/sync/IDLE parity.
- Optional extra ``[async]`` → ``aioimaplib``, ``httpx``.
- **Transport protocol** — ``IMAPTransportProtocol``.
- **Shared mailbox read-path** — ``services/mailbox/_ops``.
- **Async OAuth** — ``oauth2_async``.
- Docs: async guide, v2 migration, example ``09_async_session.py``.
- CI job and ``tests/aio/`` with pytest-asyncio.

Breaking
~~~~~~~~

- Version **2.0.0**; async is **not** exported from top-level ``sage_imap`` (use ``sage_imap.aio``).

[1.0.0] - 2026-05-19
--------------------

Added
~~~~~

- ``IMAPSession`` facade, SPECIAL-USE / NAMESPACE, OAuth refresh, TLS options.
- IDLE, CONDSTORE sync, streaming ``iter_uid_fetch`` with ``ParseMode``.
- Performance improvements (LIST, STATUS, batched STORE/FETCH).

Earlier releases
----------------

See `GitHub releases <https://github.com/sageteamorg/python-sage-imap/releases>`_ for v0.x history.

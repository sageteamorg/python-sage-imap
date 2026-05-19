# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **IDLE**: `IMAPIdleSession`, `IMAPIdleWatcher`, and transport `idle_start` / `idle_done` for push-style mailbox notifications with reconnect via `IMAPClient.reconnect()`.
- **CONDSTORE sync**: `MailboxSyncState`, `IMAPSyncService`, and `IMAPMailboxUIDService.sync` for STATUS/MODSEQ checkpoints and `CHANGEDSINCE` UID search.
- **Streaming fetch**: `IMAPMailboxUIDService.iter_uid_fetch()` with batched FETCH and `ParseMode` (`FULL`, `HEADERS`, `MINIMAL`, `RAW`) on `EmailMessage.parse_eml_content()`.

### Performance

- `list_folders(enrich=False)` by default (one LIST); pass `enrich=True` for per-folder STATUS counts.
- `folder_exists` / `get_folder_info` use targeted LIST (+ optional STATUS) instead of full tree listing.
- Flag bulk add/remove use a single combined STORE; `sync_flags_with_emails` uses one batched FETCH.
- `MessageSetBatchIterator` preserves IMAP range syntax (`1:1000`) instead of expanding large sets in memory.
- Mailbox upload uses `transport.append`; move/delete/trash skip CHECK by default (`sync_check=True` to enable).
- `IMAPClient` caches DNS lookups; monitoring wrapper no longer double-locks with transport.

## [1.0.0] - 2026-05-19

First stable release on PyPI. This version consolidates the modular IMAP client, mailbox
services, transport layer, OAuth2 helpers, and a comprehensive unit test suite.

### Breaking

- `with IMAPClient(...) as client` now yields `IMAPClient` (not raw `imaplib`). Use
  `client.connection` for low-level access.
- Background auto-reconnect is disabled by default (`enable_background_health=False`).
- Removed the monolithic `sage_imap.services.mailbox` module; use
  `sage_imap.services.mailbox` package (`IMAPMailboxService`, `IMAPMailboxUIDService`).
- Removed unused `requests` dependency (stdlib-only runtime).

### Added

- `IMAPTransport` for capability-aware, thread-safe IMAP command routing (UID vs sequence,
  MOVE, charset, COPYUID).
- OAuth2 / XOAUTH2 helpers (`sage_imap.auth.oauth2`) and `IMAPClient.connect_oauth2()`.
- STARTTLS support when `use_ssl=False` on port 143.
- Split mailbox implementation: `base`, `operations`, `models` with UID-first APIs.
- Mailcow-compatible Docker stack and GitHub Actions integration workflow.
- Unit and integration tests for client, transport, flag, folder, mailbox, search, models,
  decorators, and utils (99%+ combined coverage; 100% line coverage).
- Examples `06`–`08` for mailbox operations and UID workflows.
- `scripts/wait-for-imap.sh` for CI and local integration testing.

### Changed

- Refactored flag, folder, and client services to use `IMAPTransport`.
- Improved `MessageSet` validation, batching, and range handling.
- Folder list cache TTL and hierarchical mailbox names (`/` delimiter supported).
- Pytest defaults exclude integration tests (`-m "not integration"`).

### Fixed

- Flag operations use UID STORE when `MessageSet.is_uid` is true.
- SEARCH passes charset for non-ASCII criteria.
- Mailbox restore resolves destination UIDs after move (COPYUID / Message-ID).
- `MessageSetBatchIterator` expands UID ranges correctly.
- IMAP search string escaping for quotes and backslashes.
- Circuit breaker recovery when `last_failure_time` is falsy (e.g. `0.0`).

[1.0.0]: https://github.com/sageteamorg/python-sage-imap/compare/v0.4.0...v1.0.0

## [0.4.0] - 2024-07-17

### Added

- Enhanced IMAP service and `EmailMessage` dataclass.
- `.eml` file upload functionality on `IMAPMailboxService`.

### Fixed

- Merge conflict resolution and utils fixes.

[0.4.0]: https://github.com/sageteamorg/python-sage-imap/releases/tag/v0.4.0

## [0.3.0] - 2024-07-13

### Added

- HTML support for email messages.

### Changed

- README updates.

[0.3.0]: https://github.com/sageteamorg/python-sage-imap/releases/tag/v0.3.0

## [0.2.0] - 2024-07-13

### Added

- Email sender support.
- Message-ID header on fetch and MessageSet improvements.
- Search criteria helpers.

[0.2.0]: https://github.com/sageteamorg/python-sage-imap/releases/tag/v0.2.0

## [0.1.3] - 2024-07-09

### Added

- Core IMAP service code.

### Fixed

- Documentation and Read the Docs configuration.

[0.1.3]: https://github.com/sageteamorg/python-sage-imap/releases/tag/v0.1.3

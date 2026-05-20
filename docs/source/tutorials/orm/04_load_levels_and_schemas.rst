Lesson 4 — Load levels and Pydantic schemas
===========================================

Goal
----

Control how much data each FETCH retrieves and serialize messages for JSON APIs.

Why load levels matter
----------------------

Fetching full MIME bodies for 10,000 UIDs is slow and memory-heavy. ``LoadLevel`` tells the ORM how much to parse per message:

+------------------+------------------------------------------+
| Level            | Behavior                                 |
+==================+==========================================+
| ``IDENTITY``     | UID (+ mailbox metadata) only — no FETCH |
| ``HEADERS``      | Envelope + key headers (default)         |
| ``FULL``         | Full parsed message (attachments, body)  |
+------------------+------------------------------------------+

Set per queryset:

.. code-block:: python

   from sage_imap.orm import LoadLevel

   qs = (
       ImapMessage.objects
       .filter(unread=True)
       .limit(50)
       .with_load_level(LoadLevel.HEADERS)
   )

Account default:

.. code-block:: python

   config = ImapAccountConfig(
       account_id="demo",
       host="...",
       username="...",
       password="...",
       default_load_level=LoadLevel.HEADERS,
   )

``IDENTITY`` for UID-only pipelines
-----------------------------------

.. code-block:: python

   uids = [
       m.uid
       for m in ImapMessage.objects.filter(unread=True)
       .with_load_level(LoadLevel.IDENTITY)
       .iter()
   ]

The ORM runs SEARCH but skips FETCH — ideal when you only need counts or will fetch later in batches.

Pydantic schemas
----------------

Install ``[orm]`` pulls in Pydantic. Use schemas at API boundaries:

.. code-block:: python

   from sage_imap.orm.schemas import ImapMessageSummarySchema, ImapMessageDetailSchema

   for msg in qs.iter():
       summary = ImapMessageSummarySchema.from_imap_message(msg)
       payload = summary.model_dump(mode="json")
       # {"uid": 42, "account_id": "demo", "subject": "...", ...}

``ImapMessageDetailSchema`` includes more fields when you used ``LoadLevel.FULL``.

Other schemas
-------------

- ``ErrorSchema`` — structured error payloads
- ``OperationResultSchema`` — success/failure for mailbox operations

Pattern for a REST handler
--------------------------

.. code-block:: python

   def list_unread(account_id: str, config: ImapAccountConfig) -> list[dict]:
       with ImapORM.open(account_id, config=config) as orm:
           orm.select_mailbox("INBOX")
           qs = (
               ImapMessage.objects.filter(unread=True)
               .limit(25)
               .with_load_level(LoadLevel.HEADERS)
           )
           return [
               ImapMessageSummarySchema.from_imap_message(m).model_dump(mode="json")
               for m in qs.fetch_all()
           ]

.. tip::

   Keep ``LoadLevel.HEADERS`` for list endpoints; upgrade to ``FULL`` only on a single-message detail route.

Next: :doc:`05_pagination_and_actions`

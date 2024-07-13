Features
========

- Context manager for managing IMAP connections
- Handling IMAP flags (add/remove)
- Managing IMAP folders (create/rename/delete/list)
- Searching emails with various criteria
- Sending emails using SMTP with support for attachments and templates
- Parsing and handling email messages

Context Manager for IMAP Connections
------------------------------------

The `IMAPClient` class provides a context manager for managing IMAP connections, ensuring that the connection is properly opened and closed. This approach simplifies resource management and error handling.

Mailbox Full Control with Best Practices
----------------------------------------

The `IMAPMailboxService` class offers comprehensive control over your mailbox operations, including selecting, closing, checking, searching, deleting, moving, restoring, fetching emails, saving sent emails, and getting mailbox status.

Context Manager and Non-Context Manager Usage
---------------------------------------------

The `IMAPMailboxService` can be used within a context manager to automatically handle connection setup and teardown. However, if you prefer to manage the connection manually to avoid indentation complexity, you can instantiate and use the service without a context manager.

Example with Context Manager:

.. code-block:: python

    try:
        with IMAPClient(host, username, password) as client:
            print(client.capabilities)
            with IMAPMailboxService(client) as mailbox:
                pass
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

Example without Context Manager:

.. code-block:: python

    try:
        with IMAPClient(host, username, password) as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.select_mailbox('INBOX')
            emails = mailbox_service.fetch(MessageSet('1,2,3'), MessageParts.BODY)
            mailbox_service.close_mailbox()
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

Search Features with AND and OR Criteria
----------------------------------------

The search functionality in `IMAPMailboxService` supports complex search criteria using logical AND and OR operations. This allows you to create refined and powerful search queries.

Example of AND Criteria:

.. code-block:: python

    criteria = IMAPSearchCriteria.and_criteria(
        IMAPSearchCriteria.from_address("example@example.com"),
        IMAPSearchCriteria.subject("Meeting"),
        IMAPSearchCriteria.since("01-Jan-2023")
    )
    msg_ids = mailbox_service.search(criteria)

Example of OR Criteria:

.. code-block:: python

    criteria = IMAPSearchCriteria.or_criteria(
        IMAPSearchCriteria.seen(),
        IMAPSearchCriteria.unseen()
    )
    msg_ids = mailbox_service.search(criteria)

Fetch Method Supporting All States
-----------------------------------

The `fetch` method in `IMAPMailboxService` is designed to work with all message states, allowing you to retrieve various parts of an email such as the body, headers, and attachments.

Example of Fetching Message Parts:

.. code-block:: python

    emails = mailbox_service.fetch(MessageSet('1,2,3'), MessageParts.BODY)
    for email in emails:
        print(email.body)

Message Set for Improved Value Control
--------------------------------------

The `MessageSet` class is designed to represent a set of email messages by their unique IDs, facilitating IMAP operations. This class includes methods to validate and convert message IDs, ensuring they are in the correct format required for IMAP operations.

The `MessageSet` class provides the following features:
- Conversion of a list of message IDs to a comma-separated string.
- Validation of message IDs to ensure they are in a valid format.
- Handling of single IDs, ranges of IDs, and comma-separated lists of IDs.

Here are some examples to demonstrate how to use the `MessageSet` class in the `python-sage-imap` package.

Example 1: Single Message ID
----------------------------

Creating a `MessageSet` with a single message ID.

.. code-block:: python

    from sage_imap.helpers.message import MessageSet

    # Single message ID
    message_set = MessageSet(msg_ids="123")
    print(message_set.msg_ids)
    # Output: "123"

Example 2: Comma-separated Message IDs
--------------------------------------

Creating a `MessageSet` with a comma-separated list of message IDs.

.. code-block:: python

    from sage_imap.helpers.message import MessageSet

    # Comma-separated message IDs
    message_set = MessageSet(msg_ids="123,124,125")
    print(message_set.msg_ids)
    # Output: "123,124,125"

Example 3: Range of Message IDs
-------------------------------

Creating a `MessageSet` with a range of message IDs.

.. code-block:: python

    from sage_imap.helpers.message import MessageSet

    # Range of message IDs
    message_set = MessageSet(msg_ids="123:125")
    print(message_set.msg_ids)
    # Output: "123:125"

Example 4: List of Message IDs
------------------------------

Creating a `MessageSet` with a list of message IDs.

.. code-block:: python

    from sage_imap.helpers.message import MessageSet

    # List of message IDs
    message_set = MessageSet(msg_ids=[123, 124, 125])
    print(message_set.msg_ids)
    # Output: "123,124,125"

Example 5: Invalid Message ID
-----------------------------

Handling an invalid message ID.

.. code-block:: python

    from sage_imap.helpers.message import MessageSet

    try:
        # Invalid message ID
        message_set = MessageSet(msg_ids="abc")
    except ValueError as e:
        print(e)
    # Output: "Invalid message ID: abc"

Example 6: Empty Message ID
---------------------------

Handling an empty message ID.

.. code-block:: python

    from sage_imap.helpers.message import MessageSet

    try:
        # Empty message ID
        message_set = MessageSet(msg_ids="")
    except ValueError as e:
        print(e)
    # Output: "Message IDs cannot be empty"

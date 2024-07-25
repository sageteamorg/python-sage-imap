Example 3: Mailbox Management
=============================

The `IMAPMailboxService` class provides methods to manage IMAP mailboxes, including selecting, closing, checking, searching, deleting, moving, restoring, fetching emails, saving sent emails, and getting mailbox status. Below are the detailed explanations and examples of how to use each method in different scenarios.

Overview
--------
The `IMAPMailboxService` class interacts with the IMAP server through an `IMAPClient` instance and handles mailbox-related operations with appropriate error handling and logging.

Initialization
--------------
To use the `IMAPMailboxService`, first, you need to create an instance of `IMAPClient` and pass it to the `IMAPMailboxService`:

.. code-block:: python

    from sage_imap.services.client import IMAPClient
    from sage_imap.services.mailbox import IMAPMailboxService

    with IMAPClient('imap.example.com', 'username', 'password') as client:
        mailbox_service = IMAPMailboxService(client)
        # Now you can use the mailbox_service to manage mailboxes

Method: `select`
------------------------
This method selects the specified mailbox for subsequent operations.

**Purpose:**
Selects a mailbox.

**Parameters:**
- `mailbox` (str): The name of the mailbox to select (default is DefaultMailboxes.INBOX).

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.select('INBOX')
            print("Mailbox 'INBOX' selected.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `select` method attempts to select the 'INBOX' mailbox.
- If the selection fails, it raises an `IMAPMailboxSelectionError`.

Method: `close`
-----------------------
This method closes the currently selected mailbox.

**Purpose:**
Closes the current mailbox.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.close()
            print("Mailbox closed.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `close` method ensures that the currently selected mailbox is closed properly.
- If the closure fails, it raises an `IMAPMailboxClosureError`.

Method: `check`
---------------
This method sends a CHECK command to the IMAP server to synchronize the mailbox.

**Purpose:**
Synchronizes the mailbox.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.check()
            print("Mailbox synchronized.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `check` method sends a CHECK command to ensure all changes are saved and synchronized.
- If the CHECK command fails, it raises an `IMAPMailboxCheckError`.

Method: `search`
----------------
This method searches for emails matching the specified criteria.

**Purpose:**
Searches for emails.

**Parameters:**
- `criteria` (str): The search criteria (e.g., 'ALL', 'UNSEEN').

**Returns:**
- `List[str]`: A list of message IDs that match the search criteria.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            msg_ids = mailbox_service.search('ALL')
            print("Found emails:", msg_ids)
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `search` method searches for emails based on the provided criteria.
- If the search operation fails, it raises an `IMAPSearchError`.

Method: `trash`
----------------------------
This method marks messages for deletion and moves them to the trash folder.

**Purpose:**
Marks messages for deletion and moves to trash.

**Parameters:**
- `msg_set` (MessageSet): The set of message IDs to be marked for deletion and moved to the trash folder.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.trash(MessageSet('1,2,3'))
            print("Messages marked for deletion and moved to trash.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `trash` method marks the specified messages for deletion and moves them to the trash folder.
- If the deletion or move operation fails, it raises an `IMAPMailboxDeleteError`.

Method: `delete`
----------------------------
This method permanently deletes messages marked for deletion.

**Purpose:**
Permanently deletes messages.

**Parameters:**
- `msg_set` (MessageSet): The set of message IDs to be permanently deleted.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.delete(MessageSet('1,2,3'))
            print("Messages permanently deleted.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `delete` method permanently deletes the specified messages from the mailbox.
- If the permanent deletion operation fails, it raises an `IMAPMailboxPermanentDeleteError`.

Method: `move`
------------------------
This method moves messages to the specified folder.

**Purpose:**
Moves messages to a folder.

**Parameters:**
- `msg_set` (MessageSet): The set of message IDs to be moved.
- `folder` (str): The name of the target folder.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.move(MessageSet('1,2,3'), 'Archive')
            print("Messages moved to 'Archive'.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `move` method moves the specified messages to the given folder.
- If the move operation fails, it raises an `IMAPMailboxMoveError`.

Method: `restore`
----------------------------
This method restores messages from the trash to the original folder.

**Purpose:**
Restores messages from trash.

**Parameters:**
- `msg_set` (MessageSet): The set of message IDs to be restored.
- `original_folder` (str): The name of the original folder to which the messages will be restored.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.restore(MessageSet('1,2,3'), 'INBOX')
            print("Messages restored to 'INBOX'.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `restore` method restores the specified messages from the trash to the original folder.
- If the restore operation fails, it raises an `IMAPMailboxMoveError`.

Method: `fetch`
---------------
This method fetches specified parts of messages.

**Purpose:**
Fetches parts of messages.

**Parameters:**
- `msg_set` (MessageSet): The set of message IDs to be fetched.
- `message_part` (MessagePart): The part of the message to fetch (e.g., BODY, FLAGS).

**Returns:**
- `EmailIterator`: An iterator over the fetched email messages.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            emails = mailbox_service.fetch(MessageSet('1,2,3'), MessageParts.BODY)
            print("Fetched emails:", emails)
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `fetch` method retrieves specified parts of the given messages.
- If the fetch operation fails, it raises an exception.

Method: `save_sent`
-------------------------
This method saves a sent email to the specified folder.

**Purpose:**
Saves a sent email.

**Parameters:**
- `raw_email` (bytes): The raw email content to be saved.
- `sent_folder` (str): The name of the sent folder (default is DefaultMailboxes.SENT).

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            raw_email_bytes = b"raw email content here"
            mailbox_service.save_sent(raw_email_bytes)
            print("Sent email saved to 'SENT'.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `save_sent` method saves the raw sent email data to the specified sent folder.
- If the save operation fails, it raises an `IMAPMailboxSaveSentError`.

Method: `status`
----------------------------
This method retrieves the status of the specified mailbox.

**Purpose:**
Gets mailbox status.

**Parameters:**
- `mailbox` (str): The name of the mailbox to get the status for (default is DefaultMailboxes.INBOX).
- `*status_items` (List[MailboxStatusItems]): The status items to retrieve (e.g., MESSAGES, UNSEEN).

**Returns:**
- `str`: The status response from the IMAP server.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            status = mailbox_service.status('INBOX', MailboxStatusItems.MESSAGES)
            print("Mailbox status:", status)
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `status` method retrieves the status of the specified mailbox based on the provided status items.
- If the status retrieval operation fails, it raises an `IMAPMailboxStatusError`.

Usage in Different Scenarios
----------------------------

1. **Selecting and Checking a Mailbox:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.select_mailbox('INBOX')
            mailbox_service.check()
            print("Mailbox 'INBOX' selected and checked.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

2. **Searching for Unseen Emails:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            unseen_emails = mailbox_service.search('UNSEEN')
            print("Unseen emails:", unseen_emails)
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

3. **Moving Emails to Archive:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.move(MessageSet('1,2,3'), 'Archive')
            print("Emails moved to 'Archive'.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

4. **Restoring Emails from Trash:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            mailbox_service.restore(MessageSet('1,2,3'), 'INBOX')
            print("Emails restored to 'INBOX'.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

5. **Fetching Email Bodies:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            mailbox_service = IMAPMailboxService(client)
            email_bodies = mailbox_service.fetch(MessageSet('1,2,3'), MessageParts.BODY)
            for email in email_bodies:
                print("Email body:", email.body)
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

These examples show how to use each method of the `IMAPMailboxService` class in different scenarios, providing a clear understanding of their usage and the expected behavior.

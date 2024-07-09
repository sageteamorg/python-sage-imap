# python-sage-imap

[![Coverage Status](https://coveralls.io/repos/github/yourusername/yourrepository/badge.svg?branch=main)](https://coveralls.io/github/yourusername/yourrepository?branch=main)
[![codecov](https://codecov.io/gh/yourusername/yourrepository/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/yourrepository)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Pylint](https://img.shields.io/badge/pylint-your_score-brightgreen)

## Table of Contents
- [python-sage-imap](#python-sage-imap)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Examples](#examples)
    - [Example 1: Creating an IMAP Client](#example-1-creating-an-imap-client)
      - [Explanation](#explanation)
    - [Example 2: Working with Folder Service](#example-2-working-with-folder-service)
    - [Example 3: Working with Mailbox Methods](#example-3-working-with-mailbox-methods)
    - [IMAPMailboxService Example](#imapmailboxservice-example)
      - [Example Usage with Nested Context Managers:](#example-usage-with-nested-context-managers)
    - [Methods of IMAPMailboxService Explained](#methods-of-imapmailboxservice-explained)
  - [License](#license)

## Introduction
`python-sage-imap` is a robust Python package designed for managing IMAP connections and performing various email operations. It provides easy-to-use interfaces for managing email folders, flags, searching emails, and sending emails using SMTP. This package is ideal for developers looking to integrate email functionalities into their applications seamlessly.

## Features
- Context manager for managing IMAP connections
- Handling IMAP flags (add/remove)
- Managing IMAP folders (create/rename/delete/list)
- Searching emails with various criteria
- Sending emails using SMTP with support for attachments and templates
- Parsing and handling email messages

## Installation
To install `python-sage-imap`, use pip:
```bash
pip install python-sage-imap
```

## Configuration
Before using the package, you need to set up logging for better debugging and monitoring:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## Examples

### Example 1: Creating an IMAP Client

This example demonstrates how to create an IMAP client using the `IMAPClient` class.

```python
from services_client import IMAPClient

with IMAPClient('imap.example.com', 'username', 'password') as client:
    # Use the client for IMAP operations
    capabilities = client.capability()
    print(f"Server capabilities: {capabilities}")

    status, messages = client.select("INBOX")
    print(f"Selected INBOX with status: {status}")
```

#### Explanation

This example illustrates a low-level approach to working with IMAP. If you want to use `imaplib` directly but need the added convenience of managing the connection lifecycle, the `IMAPClient` class is a perfect choice. It allows you to create a connection with the IMAP server and then use all the capabilities of `imaplib` to customize your workflow.

1. **IMAPClient Context Manager**:
   - The `IMAPClient` class is used within a context manager (`with` statement). This ensures that the connection to the IMAP server is properly opened and closed.
   - When the `with` block is entered, the connection to the IMAP server is established, and the user is authenticated.
   - When the `with` block is exited, the connection is automatically closed, ensuring that resources are cleaned up properly.

2. **Why Use IMAPClient**:
   - The `IMAPClient` exists to simplify the management of IMAP connections. By using it as a context manager, you don't have to worry about manually opening and closing the connection. This reduces the risk of resource leaks and makes your code cleaner and more maintainable.
   - Within the context manager, you have access to the `imaplib` capabilities directly through the `client` object. This allows you to perform various IMAP operations seamlessly.

3. **Capabilities and Select Methods**:
   - The `.capability()` method is called to retrieve the server's capabilities, providing information about what commands and features the server supports.
   - The `.select("INBOX")` method is used to select the "INBOX" mailbox for further operations. It returns the status of the selection and the number of messages in the mailbox.

By using the `IMAPClient` class in this way, you can take advantage of the full power of `imaplib` while benefiting from the convenience and safety of automatic connection management.


### Example 2: Working with Folder Service
This example demonstrates how to work with folders using the `IMAPFolderService`.

```python
from services_client import IMAPClient
from services_folder import IMAPFolderService

with IMAPClient('imap.example.com', 'username', 'password') as client:
    folder_service = IMAPFolderService(client)

    # Create a new folder
    folder_service.create_folder('NewFolder')

    # Rename the folder
    folder_service.rename_folder('NewFolder', 'RenamedFolder')

    # List all folders
    folders = folder_service.list_folders()
    print(f"Folders: {folders}")

    # Delete the folder
    folder_service.delete_folder('RenamedFolder')
```

### Example 3: Working with Mailbox Methods

Below are usage examples of the `IMAPClient` and `IMAPMailboxService` classes, demonstrating their context manager capabilities and various methods:

### IMAPMailboxService Example

The `IMAPMailboxService` class provides methods for managing mailbox operations such as selecting, closing, checking, deleting, moving, and getting status of mailboxes.

**Purpose:** This class allows for performing various mailbox-related operations within the context of an IMAP connection, ensuring proper error handling and cleanup.

#### Example Usage with Nested Context Managers:

```python
from services_client import IMAPClient
from services_mailbox import IMAPMailboxService, DefaultMailboxes, MessageSet, MailboxStatusItems
from helpers.exceptions import IMAPClientError, IMAPMailboxCheckError, IMAPMailboxClosureError

username = 'username'
password = 'password'

try:
    with IMAPClient('imap.example.com', username, password) as client:
        with IMAPMailboxService(client) as mailbox:
            # Select a mailbox
            mailbox.select_mailbox(DefaultMailboxes.INBOX)

            # Delete messages temporarily (move to trash)
            msg_set = MessageSet('1,2,3')
            mailbox.delete_temporarily(msg_set)

            # Restore messages from trash to original folder
            mailbox.restore_from_trash(msg_set, DefaultMailboxes.INBOX)

            # Permanently delete messages
            mailbox.delete_permanently(msg_set)

            # Get the status of a mailbox
            status = mailbox.get_mailbox_status(
                DefaultMailboxes.INBOX,
                MailboxStatusItems.MESSAGES
            )
            print(f"Mailbox status: {status}")

except IMAPClientError as e:
    print(f"An error occurred with the IMAP client: {e}")
```

### Methods of IMAPMailboxService Explained

1. **select_mailbox(mailbox=DefaultMailboxes.INBOX)**
   - **Purpose:** Selects the specified mailbox for subsequent operations.
   - **Example:**
     ```python
     mailbox_service.select_mailbox('INBOX')
     ```

2. **close_mailbox()**
   - **Purpose:** Closes the currently selected mailbox to ensure all changes are saved and the connection is properly terminated.
   - **Example:**
     ```python
     mailbox_service.close_mailbox()
     ```

3. **check()**
   - **Purpose:** Sends a CHECK command to the IMAP server to synchronize the mailbox.
   - **Example:**
     ```python
     mailbox_service.check()
     ```

4. **delete_temporarily(msg_set: MessageSet)**
   - **Purpose:** Marks messages for deletion and moves them to the trash folder.
   - **Example:**
     ```python
     mailbox_service.delete_temporarily(MessageSet('1,2,3'))
     ```

5. **delete_permanently(msg_set: MessageSet)**
   - **Purpose:** Permanently deletes messages marked for deletion.
   - **Example:**
     ```python
     mailbox_service.delete_permanently(MessageSet('1,2,3'))
     ```

6. **move_to_folder(msg_set: MessageSet, folder: str)**
   - **Purpose:** Moves messages to the specified folder.
   - **Example:**
     ```python
     mailbox_service.move_to_folder(MessageSet('1,2,3'), 'Archive')
     ```

7. **restore_from_trash(msg_set: MessageSet, original_folder: str)**
   - **Purpose:** Restores messages from the trash to the original folder.
   - **Example:**
     ```python
     mailbox_service.restore_from_trash(MessageSet('1,2,3'), 'INBOX')
     ```

8. **get_mailbox_status(mailbox=DefaultMailboxes.INBOX, *status_items: List[MailboxStatusItems

])**
   - **Purpose:** Gets the status of the specified mailbox based on the provided status items.
   - **Example:**
     ```python
     status = mailbox_service.get_mailbox_status('INBOX', MailboxStatusItems.MESSAGES)
     print(f"Mailbox status: {status}")
     ```

By utilizing these classes and methods, you can manage your IMAP mailboxes effectively and perform necessary email operations in a robust and error-handling manner.

## License
This project is licensed under the MIT License.

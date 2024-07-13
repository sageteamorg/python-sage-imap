Example 2: Folder Management of IMAP
====================================

The `IMAPFolderService` class provides methods to manage IMAP folders, including creating, renaming, deleting, and listing folders. Below are the detailed explanations and examples of how to use each method in different scenarios.

Overview
--------
The `IMAPFolderService` class interacts with the IMAP server through an `IMAPClient` instance and handles folder-related operations with appropriate error handling and logging.

Initialization
--------------
To use the `IMAPFolderService`, first, you need to create an instance of `IMAPClient` and pass it to the `IMAPFolderService`:

.. code-block:: python

    from sage_imap.services.client import IMAPClient
    from sage_imap.services.folder import IMAPFolderService

    with IMAPClient('imap.example.com', 'username', 'password') as client:
        folder_service = IMAPFolderService(client)
        # Now you can use the folder_service to manage folders

Method: `create_folder`
-----------------------
This method creates a new folder with the specified name.

**Purpose:**
Creates a new folder in the IMAP mailbox.

**Parameters:**
- `folder_name` (str): The name of the folder to be created.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            folder_service = IMAPFolderService(client)
            folder_service.create_folder('NewFolder')
            print("Folder 'NewFolder' created successfully.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `create_folder` method attempts to create a folder named 'NewFolder'.
- If the folder already exists, it raises an `IMAPFolderExistsError`.
- If the folder creation fails for other reasons, it raises an `IMAPFolderOperationError`.

Method: `rename_folder`
-----------------------
This method renames an existing folder from `old_name` to `new_name`.

**Purpose:**
Renames an existing folder.

**Parameters:**
- `old_name` (str): The current name of the folder.
- `new_name` (str): The new name for the folder.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            folder_service = IMAPFolderService(client)
            folder_service.rename_folder('OldFolder', 'NewFolder')
            print("Folder renamed from 'OldFolder' to 'NewFolder'.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `rename_folder` method renames the folder 'OldFolder' to 'NewFolder'.
- If the folder 'OldFolder' does not exist, it raises an `IMAPFolderNotFoundError`.
- If the renaming operation fails for other reasons, it raises an `IMAPFolderOperationError`.

Method: `delete_folder`
-----------------------
This method deletes a specified folder.

**Purpose:**
Deletes a folder with the given `folder_name`. It cannot delete default folders.

**Parameters:**
- `folder_name` (str): The name of the folder to be deleted.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            folder_service = IMAPFolderService(client)
            folder_service.delete_folder('FolderName')
            print("Folder 'FolderName' deleted successfully.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `delete_folder` method deletes the folder named 'FolderName'.
- If 'FolderName' is a default folder, it raises an `IMAPUnexpectedError`.
- If the folder 'FolderName' does not exist, it raises an `IMAPFolderNotFoundError`.
- If the deletion operation fails for other reasons, it raises an `IMAPFolderOperationError`.

Method: `list_folders`
----------------------
This method lists all folders in the mailbox.

**Purpose:**
Retrieves a list of all folders in the mailbox.

**Returns:**
- `List[str]`: A list of folder names.

**Example:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            folder_service = IMAPFolderService(client)
            folders = folder_service.list_folders()
            print("Folders:", folders)
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

**Explanation:**
- The `list_folders` method retrieves all folders in the mailbox and returns their names.
- If the listing operation fails, it raises an `IMAPFolderOperationError`.

Usage in Different Scenarios
----------------------------

1. **Creating a Folder Only if It Doesn't Exist:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            folder_service = IMAPFolderService(client)
            folders = folder_service.list_folders()
            if 'NewFolder' not in folders:
                folder_service.create_folder('NewFolder')
                print("Folder 'NewFolder' created successfully.")
            else:
                print("Folder 'NewFolder' already exists.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

2. **Renaming a Folder if It Exists:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            folder_service = IMAPFolderService(client)
            folders = folder_service.list_folders()
            if 'OldFolder' in folders:
                folder_service.rename_folder('OldFolder', 'RenamedFolder')
                print("Folder renamed from 'OldFolder' to 'RenamedFolder'.")
            else:
                print("Folder 'OldFolder' does not exist.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

3. **Deleting a Folder if It Exists and Is Not a Default Folder:**

.. code-block:: python

    try:
        with IMAPClient("imap.example.com", "username", "password") as client:
            folder_service = IMAPFolderService(client)
            folders = folder_service.list_folders()
            if 'DeletableFolder' in folders:
                folder_service.delete_folder('DeletableFolder')
                print("Folder 'DeletableFolder' deleted successfully.")
            else:
                print("Folder 'DeletableFolder' does not exist.")
    except IMAPClientError as e:
        logging.critical("An error occurred: %s", e)

These examples show how to use each method of the `IMAPFolderService` class in different scenarios, providing a clear understanding of their usage and the expected behavior.

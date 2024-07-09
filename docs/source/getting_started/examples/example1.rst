Example 1: Creating an IMAP Client
==================================

This example demonstrates how to create an IMAP client using the `IMAPClient` class.

.. code-block:: python

    from services_client import IMAPClient

    with IMAPClient('imap.example.com', 'username', 'password') as client:
        # Use the client for IMAP operations
        capabilities = client.capability()
        print(f"Server capabilities: {capabilities}")

        status, messages = client.select("INBOX")
        print(f"Selected INBOX with status: {status}")

Explanation
-----------

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

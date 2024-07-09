Configuration Guide
===================

Configuration
-------------

In the configuration, you need to specify variables for both IMAP and SMTP connections to establish and manage email communication effectively.

This library offers flexibility to accommodate both single-user and multi-user scenarios:

- **Single User Configuration**: If you are integrating this library into a Django application or any other single-user setup, you can define the necessary variables within your application's settings. This approach ensures that the configuration behaves as a single user, maintaining a consistent and straightforward setup.

- **Multi-User Configuration**: For applications requiring support for multiple users, such as a web application with various user accounts, the library allows you to dynamically change the configuration variables upon each instantiation. This flexibility ensures that each user can have their own IMAP and SMTP connection settings, enabling personalized email management and communication.

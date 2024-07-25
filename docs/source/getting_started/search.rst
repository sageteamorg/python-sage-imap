IMAP Search Criteria
====================

The `IMAPSearchCriteria` class provides a comprehensive set of static methods and enum values to construct search criteria for querying emails from an IMAP server. Here’s a detailed explanation of each variation, categorized into single commands and complex commands.

Single Commands
---------------

These are simple search criteria that can be used independently to query emails.

1. **Basic Criteria**:

   - `ALL`: Selects all messages in the mailbox.

     ::

        IMAPSearchCriteria.ALL  # Output: "ALL"

   - `SEEN`: Selects messages that have been read.

     ::

        IMAPSearchCriteria.SEEN  # Output: "SEEN"

   - `UNSEEN`: Selects messages that have not been read.

     ::

        IMAPSearchCriteria.UNSEEN  # Output: "UNSEEN"

   - `FLAGGED`: Selects messages that are marked.

     ::

        IMAPSearchCriteria.FLAGGED  # Output: "FLAGGED"

   - `UNFLAGGED`: Selects messages that are not marked.

     ::

        IMAPSearchCriteria.UNFLAGGED  # Output: "UNFLAGGED"

   - `ANSWERED`: Selects messages that have been replied to.

     ::

        IMAPSearchCriteria.ANSWERED  # Output: "ANSWERED"

   - `UNANSWERED`: Selects messages that have not been replied to.

     ::

        IMAPSearchCriteria.UNANSWERED  # Output: "UNANSWERED"

   - `DELETED`: Selects messages that are marked for deletion.

     ::

        IMAPSearchCriteria.DELETED  # Output: "DELETED"

   - `UNDELETED`: Selects messages that are not marked for deletion.

     ::

        IMAPSearchCriteria.UNDELETED  # Output: "UNDELETED"

   - `DRAFT`: Selects messages that are drafts.

     ::

        IMAPSearchCriteria.DRAFT  # Output: "DRAFT"

2. **Date-Based Criteria**:

   - `before(date: str)`: Selects messages before the specified date.

     ::

        IMAPSearchCriteria.before("01-Jan-2023")  # Output: "BEFORE 01-Jan-2023"

   - `on(date: str)`: Selects messages on the specified date.

     ::

        IMAPSearchCriteria.on("01-Jan-2023")  # Output: "ON 01-Jan-2023"

   - `since(date: str)`: Selects messages since the specified date.

     ::

        IMAPSearchCriteria.since("01-Jan-2023")  # Output: "SINCE 01-Jan-2023"

3. **Address-Based Criteria**:

   - `from_address(email: str)`: Selects messages from the specified email address.

     ::

        IMAPSearchCriteria.from_address("example@example.com")  # Output: 'FROM "example@example.com"'

   - `to_address(email: str)`: Selects messages to the specified email address.

     ::

        IMAPSearchCriteria.to_address("example@example.com")  # Output: 'TO "example@example.com"'

4. **Content-Based Criteria**:

   - `subject(subject: str)`: Selects messages with the specified subject.

     ::

        IMAPSearchCriteria.subject("Meeting")  # Output: 'SUBJECT "Meeting"'

   - `body(text: str)`: Selects messages with the specified body text.

     ::

        IMAPSearchCriteria.body("Project update")  # Output: 'BODY "Project update"'

   - `text(text: str)`: Selects messages with the specified text anywhere in the email.

     ::

        IMAPSearchCriteria.text("Important")  # Output: 'TEXT "Important"'

5. **Header-Based Criteria**:

   - `header(field: str, value: str)`: Selects messages with the specified header field and value.

     ::

        IMAPSearchCriteria.header("X-Priority", "1")  # Output: 'HEADER "X-Priority" "1"'

6. **Other Criteria**:

   - `message_id(message_id: str)`: Selects messages with the specified Message-ID.

     ::

        IMAPSearchCriteria.message_id("<unique-id@example.com>")  # Output: 'HEADER "Message-ID" "<unique-id@example.com>"'

   - `uid(uid: str)`: Selects messages with the specified UID or range of UIDs.

     ::

        IMAPSearchCriteria.uid("100")  # Output: "UID 100"
        IMAPSearchCriteria.uid("100:200")  # Output: "UID 100:200"

Complex Commands
----------------

These involve combining multiple criteria using logical operations (AND, OR, NOT) to form more advanced queries.

1. **AND Criteria**:

   - Combines multiple criteria with a logical AND.

     ::

        criteria = IMAPSearchCriteria.and_criteria(
            IMAPSearchCriteria.SEEN,
            IMAPSearchCriteria.from_address("example@example.com"),
            IMAPSearchCriteria.subject("Meeting")
        )
        # Output: (SEEN FROM "example@example.com" SUBJECT "Meeting")

   - This command ensures that all combined criteria must be met for an email to be selected. For example, it will select emails that are both seen, from a specific sender, and with a specific subject.

2. **OR Criteria**:

   - Combines multiple criteria with a logical OR.

     ::

        criteria = IMAPSearchCriteria.or_criteria(
            IMAPSearchCriteria.SEEN,
            IMAPSearchCriteria.UNSEEN
        )
        # Output: (OR SEEN UNSEEN)

   - This command ensures that if any of the combined criteria are met, the email will be selected. For example, it will select emails that are either seen or unseen.

3. **NOT Criteria**:

   - Negates a criteria.

     ::

        criteria = IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.SEEN)
        # Output: NOT (SEEN)

   - This command selects emails that do not meet the specified criteria. For example, it will select emails that are not seen.

4. **Recent Criteria**:

   - Selects emails within the specified number of recent days.

     ::

        criteria = IMAPSearchCriteria.recent(7)
        # Output: SINCE <date 7 days ago>

   - This command uses the current date and calculates the date from a specified number of days ago to select emails received within that timeframe.

Examples
--------

**Simple Criteria:**

::

    criteria = IMAPSearchCriteria.SEEN
    print(criteria)  # Output: "SEEN"

    criteria = IMAPSearchCriteria.before("01-Jan-2023")
    print(criteria)  # Output: "BEFORE 01-Jan-2023"

    criteria = IMAPSearchCriteria.from_address("example@example.com")
    print(criteria)  # Output: 'FROM "example@example.com"'

**Complex Criteria:**

::

    criteria = IMAPSearchCriteria.and_criteria(
        IMAPSearchCriteria.SEEN,
        IMAPSearchCriteria.from_address("example@example.com"),
        IMAPSearchCriteria.subject("Meeting")
    )
    print(criteria)  # Output: (SEEN FROM "example@example.com" SUBJECT "Meeting")

    criteria = IMAPSearchCriteria.or_criteria(
        IMAPSearchCriteria.SEEN,
        IMAPSearchCriteria.UNSEEN
    )
    print(criteria)  # Output: (OR SEEN UNSEEN)

    criteria = IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.SEEN)
    print(criteria)  # Output: NOT (SEEN)

    criteria = IMAPSearchCriteria.recent(7)
    print(criteria)  # Output: SINCE <date 7 days ago>

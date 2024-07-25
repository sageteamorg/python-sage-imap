What is MessageSet
=======================

Example 1: Single ID
--------------------

::

    message_set = MessageSet("123")
    print(message_set.msg_ids)  # Output: "123"

**Description:** A single email ID is provided. The `msg_ids` attribute stores this ID as a string.

Example 2: Comma-Separated List of IDs
--------------------------------------

::

    message_set = MessageSet("123,456,789")
    print(message_set.msg_ids)  # Output: "123,456,789"

**Description:** Multiple email IDs are provided as a comma-separated string. The `msg_ids` attribute retains this format.

Example 3: Range of IDs
-----------------------

::

    message_set = MessageSet("100:200")
    print(message_set.msg_ids)  # Output: "100:200"

**Description:** A range of email IDs is provided. The `msg_ids` attribute stores this range in the same format.

Example 4: List of IDs
----------------------

::

    message_set = MessageSet([123, 456, 789])
    print(message_set.msg_ids)  # Output: "123,456,789"

**Description:** A list of email IDs is provided. The `msg_ids` attribute converts the list to a comma-separated string.

Example 5: Mixed Format with Validations
----------------------------------------

::

    message_set = MessageSet("123,200:300,400")
    print(message_set.msg_ids)  # Output: "123,200:300,400"

**Description:** A mix of individual IDs and ranges is provided. The `msg_ids` attribute stores these in a comma-separated string format.

Example 6: Valid Range with Wildcard
------------------------------------

::

    message_set = MessageSet("1:*")
    print(message_set.msg_ids)  # Output: "1:*"

**Description:** A range from the first message to the last message using a wildcard. The `msg_ids` attribute retains this format.

Example 7: Invalid Range (Raises Error)
---------------------------------------

::

    try:
        message_set = MessageSet("300:200")
    except ValueError as e:
        print(e)  # Output: "Invalid range in message IDs: 300:200"

**Description:** An invalid range where the start ID is greater than the end ID. This raises a `ValueError`.

Example 8: Invalid Message ID (Raises Error)
--------------------------------------------

::

    try:
        message_set = MessageSet("abc")
    except ValueError as e:
        print(e)  # Output: "Invalid message ID: abc"

**Description:** An invalid message ID that is not numeric. This raises a `ValueError`.

Example 9: Empty Message IDs (Raises Error)
-------------------------------------------

::

    try:
        message_set = MessageSet("")
    except ValueError as e:
        print(e)  # Output: "Message IDs cannot be empty"

**Description:** An empty string is provided for message IDs. This raises a `ValueError`.

Example 10: Invalid Data Type (Raises Error)
--------------------------------------------

::

    try:
        message_set = MessageSet(123)
    except TypeError as e:
        print(e)  # Output: "msg_ids should be a string"

**Description:** An invalid data type (integer) is provided for message IDs. This raises a `TypeError`.
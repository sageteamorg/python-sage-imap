from typing import Dict, List, NewType, Union

MessageId = Union[str, int]
MessageIDList = List[MessageId]
MessageSetType = Union[str, MessageIDList]

EmailDate = NewType("EmailDate", str)
EmailHeaders = Dict[str, str]
EmailAddress = NewType("EmailAddress", str)
RawEmail = NewType("RawEmail", bytes)

Mailbox = NewType("Mailbox", str)

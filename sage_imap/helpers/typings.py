from typing import List, Union, NewType, Dict

MessageId = Union[str, int]
MessageIDList = List[MessageId]
MessageSetType = Union[str, MessageIDList]

EmailDate = NewType('EmailDate', str)
EmailHeaders = Dict[str, str]
EmailAddress = NewType('EmailAddress', str)
RawEmail = NewType('RawEmail', bytes)

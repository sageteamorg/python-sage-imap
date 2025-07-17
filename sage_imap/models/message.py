import logging
import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Optional, Set, Union

from sage_imap.helpers.typings import MessageSetType

logger = logging.getLogger(__name__)


@dataclass
class MessageSet:
    """
    Enhanced message set class for reliable IMAP message operations.
    
    This class provides comprehensive support for both sequence numbers and UIDs,
    with strong emphasis on UID-based operations for reliability. It includes
    validation, conversion utilities, and batch operation support.
    
    **⚠️ IMPORTANT: Always use UIDs for production applications!**
    
    Purpose
    -------
    This class manages sets of email messages for IMAP operations, providing:
    - Reliable UID-based message identification
    - Batch operation support for large message sets
    - Conversion utilities between sequence numbers and UIDs
    - Comprehensive validation and error handling
    - Performance optimizations for large datasets
    
    Attributes
    ----------
    msg_ids : MessageSetType
        Message identifiers (UIDs recommended, sequence numbers supported)
    is_uid : bool
        Whether the message set contains UIDs (True) or sequence numbers (False)
    mailbox : Optional[str]
        Mailbox name for context (important for UID validation)
    
    Methods
    -------
    from_uids(uids: List[int], mailbox: Optional[str] = None) -> MessageSet
        Create message set from UIDs (recommended approach)
    from_sequence_numbers(seq_nums: List[int], mailbox: Optional[str] = None) -> MessageSet
        Create message set from sequence numbers (use with caution)
    from_email_messages(messages: List[EmailMessage]) -> MessageSet
        Create message set from EmailMessage objects
    from_range(start: int, end: int, is_uid: bool = True) -> MessageSet
        Create message set from range of IDs
    
    Examples
    --------
    **Recommended UID-based approach:**
    
    >>> # Create from UIDs (recommended)
    >>> msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
    >>> print(msg_set.msg_ids)  # "1001,1002,1003"
    >>> print(msg_set.is_uid)   # True
    
    >>> # Create from EmailMessage objects
    >>> msg_set = MessageSet.from_email_messages(email_list)
    >>> print(f"Processing {len(msg_set)} messages")
    
    **Range operations:**
    
    >>> # UID range (recommended)
    >>> msg_set = MessageSet.from_range(1000, 2000, is_uid=True)
    >>> print(msg_set.msg_ids)  # "1000:2000"
    
    >>> # Get all messages with UIDs
    >>> all_msgs = MessageSet.from_range(1, "*", is_uid=True)
    
    **Batch operations:**
    
    >>> # Process large message sets in batches
    >>> large_set = MessageSet.from_uids(list(range(1000, 10000)))
    >>> for batch in large_set.iter_batches(batch_size=100):
    ...     process_batch(batch)
    """
    
    msg_ids: MessageSetType = field(default_factory=str)
    is_uid: bool = field(default=True)  # Default to UID for reliability
    mailbox: Optional[str] = field(default=None)
    
    # Internal fields for caching and validation
    _validated: bool = field(default=False, init=False, repr=False)
    _parsed_ids: Optional[List[int]] = field(default=None, init=False, repr=False)
    _id_ranges: Optional[List[tuple]] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Post-initialization validation and setup."""
        try:
            self._convert_list_to_string()
            self._validate_message_set()
            self._validated = True
        except Exception as e:
            logger.error(f"MessageSet initialization failed: {e}")
            raise

    @classmethod
    def from_uids(
        cls, 
        uids: List[int], 
        mailbox: Optional[str] = None
    ) -> "MessageSet":
        """
        Create MessageSet from UIDs (recommended approach).
        
        Parameters
        ----------
        uids : List[int]
            List of unique identifiers
        mailbox : Optional[str]
            Mailbox name for context
            
        Returns
        -------
        MessageSet
            New message set with UIDs
            
        Examples
        --------
        >>> msg_set = MessageSet.from_uids([1001, 1002, 1003], "INBOX")
        >>> print(msg_set.is_uid)  # True
        """
        if not uids:
            raise ValueError("UID list cannot be empty")
        
        # Validate and sort UIDs
        validated_uids = sorted(set(uid for uid in uids if isinstance(uid, int) and uid > 0))
        
        if not validated_uids:
            raise ValueError("No valid UIDs provided")
        
        return cls(
            msg_ids=validated_uids,
            is_uid=True,
            mailbox=mailbox
        )
    
    @classmethod
    def from_sequence_numbers(
        cls, 
        seq_nums: List[int], 
        mailbox: Optional[str] = None
    ) -> "MessageSet":
        """
        Create MessageSet from sequence numbers (use with caution).
        
        **⚠️ WARNING: Sequence numbers are unreliable for production use!**
        
        Parameters
        ----------
        seq_nums : List[int]
            List of sequence numbers
        mailbox : Optional[str]
            Mailbox name for context
            
        Returns
        -------
        MessageSet
            New message set with sequence numbers
            
        Examples
        --------
        >>> # Only for immediate, positional operations
        >>> msg_set = MessageSet.from_sequence_numbers([1, 2, 3], "INBOX")
        >>> print(msg_set.is_uid)  # False
        """
        if not seq_nums:
            raise ValueError("Sequence number list cannot be empty")
        
        # Validate and sort sequence numbers
        validated_seq_nums = sorted(set(seq for seq in seq_nums if isinstance(seq, int) and seq > 0))
        
        if not validated_seq_nums:
            raise ValueError("No valid sequence numbers provided")
        
        logger.warning(
            "Using sequence numbers for MessageSet. "
            "Consider using UIDs for reliable operations."
        )
        
        return cls(
            msg_ids=validated_seq_nums,
            is_uid=False,
            mailbox=mailbox
        )
    
    @classmethod
    def from_email_messages(
        cls, 
        messages: List["EmailMessage"]
    ) -> "MessageSet":
        """
        Create MessageSet from EmailMessage objects.
        
        Prefers UIDs when available, falls back to sequence numbers.
        
        Parameters
        ----------
        messages : List[EmailMessage]
            List of email message objects
            
        Returns
        -------
        MessageSet
            New message set from messages
            
        Examples
        --------
        >>> msg_set = MessageSet.from_email_messages(email_list)
        >>> print(f"Created set with {len(msg_set)} messages")
        """
        if not messages:
            raise ValueError("Email message list cannot be empty")
        
        # Try to use UIDs first (recommended)
        uids = [msg.uid for msg in messages if msg.uid is not None]
        
        if uids:
            # Get mailbox from first message if available
            mailbox = messages[0].mailbox if hasattr(messages[0], 'mailbox') else None
            return cls.from_uids(uids, mailbox)
        
        # Fall back to sequence numbers (not recommended)
        seq_nums = [msg.sequence_number for msg in messages if msg.sequence_number is not None]
        
        if seq_nums:
            mailbox = messages[0].mailbox if hasattr(messages[0], 'mailbox') else None
            logger.warning(
                "Using sequence numbers from EmailMessage objects. "
                "Ensure UIDs are available for reliable operations."
            )
            return cls.from_sequence_numbers(seq_nums, mailbox)
        
        raise ValueError("No valid UIDs or sequence numbers found in EmailMessage objects")
    
    @classmethod
    def from_range(
        cls, 
        start: Union[int, str], 
        end: Union[int, str], 
        is_uid: bool = True,
        mailbox: Optional[str] = None
    ) -> "MessageSet":
        """
        Create MessageSet from range of IDs.
        
        Parameters
        ----------
        start : Union[int, str]
            Start of range (or "1" for first message)
        end : Union[int, str]
            End of range (or "*" for last message)
        is_uid : bool
            Whether range contains UIDs (True) or sequence numbers (False)
        mailbox : Optional[str]
            Mailbox name for context
            
        Returns
        -------
        MessageSet
            New message set with range
            
        Examples
        --------
        >>> # UID range (recommended)
        >>> msg_set = MessageSet.from_range(1000, 2000, is_uid=True)
        >>> print(msg_set.msg_ids)  # "1000:2000"
        
        >>> # Get all messages
        >>> all_msgs = MessageSet.from_range(1, "*", is_uid=True)
        """
        if not is_uid:
            logger.warning(
                "Using sequence number range for MessageSet. "
                "Consider using UIDs for reliable operations."
            )
        
        range_str = f"{start}:{end}"
        
        return cls(
            msg_ids=range_str,
            is_uid=is_uid,
            mailbox=mailbox
        )
    
    @classmethod
    def all_messages(cls, is_uid: bool = True, mailbox: Optional[str] = None) -> "MessageSet":
        """
        Create MessageSet for all messages in mailbox.
        
        Parameters
        ----------
        is_uid : bool
            Whether to use UIDs (True) or sequence numbers (False)
        mailbox : Optional[str]
            Mailbox name for context
            
        Returns
        -------
        MessageSet
            Message set for all messages
        """
        return cls.from_range(1, "*", is_uid=is_uid, mailbox=mailbox)
    
    def _convert_list_to_string(self) -> None:
        """
        Convert list of message IDs to comma-separated string.
        
        Enhanced version with better optimization and validation.
        """
        if isinstance(self.msg_ids, list):
            if not self.msg_ids:
                raise ValueError("Message ID list cannot be empty")
            
            # Validate and convert to integers
            validated_ids = []
            for msg_id in self.msg_ids:
                if isinstance(msg_id, (int, str)):
                    try:
                        validated_ids.append(int(msg_id))
                    except ValueError:
                        raise ValueError(f"Invalid message ID: {msg_id}")
                else:
                    raise TypeError(f"Message ID must be int or string, got {type(msg_id)}")
            
            # Sort and remove duplicates for efficiency
            validated_ids = sorted(set(validated_ids))
            
            # Convert to optimized string representation
            self.msg_ids = self._optimize_id_string(validated_ids)
    
    def _optimize_id_string(self, ids: List[int]) -> str:
        """
        Optimize ID list to use ranges where possible.
        
        Examples: [1, 2, 3, 5, 6, 7, 10] -> "1:3,5:7,10"
        """
        if not ids:
            return ""
        
        if len(ids) == 1:
            return str(ids[0])
        
        # Group consecutive IDs into ranges
        ranges = []
        start = ids[0]
        prev = ids[0]
        
        for current in ids[1:]:
            if current == prev + 1:
                # Consecutive ID, continue range
                prev = current
            else:
                # Gap found, close current range
                if start == prev:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}:{prev}")
                start = current
                prev = current
        
        # Add final range
        if start == prev:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}:{prev}")
        
        return ",".join(ranges)
    
    def _validate_message_set(self) -> None:
        """
        Enhanced validation with better error messages and edge case handling.
        """
        if not self.msg_ids:
            raise ValueError("Message IDs cannot be empty")
        
        if not isinstance(self.msg_ids, str):
            raise TypeError("msg_ids should be a string after conversion")
        
        # Parse and validate each component
        components = self.msg_ids.split(",")
        
        for component in components:
            component = component.strip()
            if not component:
                raise ValueError("Empty component in message ID string")
            
            self._validate_component(component)
    
    def _validate_component(self, component: str) -> None:
        """Validate individual component (single ID or range)."""
        if ":" in component:
            # Range validation
            parts = component.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid range format: {component}")
            
            start, end = parts
            
            # Validate start
            if start == "1" or start.isdigit():
                start_val = int(start)
            else:
                raise ValueError(f"Invalid range start: {start}")
            
            # Validate end
            if end == "*":
                # Valid: open-ended range
                pass
            elif end.isdigit():
                end_val = int(end)
                if start_val > end_val:
                    raise ValueError(f"Invalid range: start ({start_val}) > end ({end_val})")
            else:
                raise ValueError(f"Invalid range end: {end}")
        else:
            # Single ID validation
            if not component.isdigit():
                raise ValueError(f"Invalid message ID: {component}")
            
            if int(component) <= 0:
                raise ValueError(f"Message ID must be positive: {component}")
    
    @cached_property
    def parsed_ids(self) -> List[int]:
        """
        Get parsed individual message IDs (excluding ranges).
        
        Returns
        -------
        List[int]
            List of individual message IDs
        """
        if self._parsed_ids is not None:
            return self._parsed_ids
        
        ids = []
        components = self.msg_ids.split(",")
        
        for component in components:
            component = component.strip()
            if ":" not in component:
                ids.append(int(component))
        
        self._parsed_ids = sorted(set(ids))
        return self._parsed_ids
    
    @cached_property
    def id_ranges(self) -> List[tuple]:
        """
        Get parsed ID ranges.
        
        Returns
        -------
        List[tuple]
            List of (start, end) tuples for ranges
        """
        if self._id_ranges is not None:
            return self._id_ranges
        
        ranges = []
        components = self.msg_ids.split(",")
        
        for component in components:
            component = component.strip()
            if ":" in component:
                start, end = component.split(":")
                start_val = int(start) if start.isdigit() else start
                end_val = int(end) if end.isdigit() else end
                ranges.append((start_val, end_val))
        
        self._id_ranges = ranges
        return self._id_ranges
    
    @cached_property
    def estimated_count(self) -> int:
        """
        Estimate total number of messages (approximate for ranges).
        
        Returns
        -------
        int
            Estimated message count
        """
        count = len(self.parsed_ids)
        
        for start, end in self.id_ranges:
            if isinstance(start, int) and isinstance(end, int):
                count += end - start + 1
            else:
                # Can't estimate ranges with "*"
                count += 1  # Conservative estimate
        
        return count
    
    def __len__(self) -> int:
        """Return estimated count of messages."""
        return self.estimated_count
    
    def __bool__(self) -> bool:
        """Check if message set has any messages."""
        return bool(self.msg_ids)
    
    def __contains__(self, msg_id: int) -> bool:
        """Check if message ID is in the set."""
        # Check individual IDs
        if msg_id in self.parsed_ids:
            return True
        
        # Check ranges
        for start, end in self.id_ranges:
            if isinstance(start, int) and isinstance(end, int):
                if start <= msg_id <= end:
                    return True
            elif isinstance(start, int) and end == "*":
                if msg_id >= start:
                    return True
        
        return False
    
    def __iter__(self):
        """Iterate over individual message IDs (excludes ranges)."""
        return iter(self.parsed_ids)
    
    def __str__(self) -> str:
        """String representation."""
        id_type = "UID" if self.is_uid else "SEQ"
        mailbox_info = f" (mailbox: {self.mailbox})" if self.mailbox else ""
        return f"MessageSet({id_type}: {self.msg_ids}{mailbox_info})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"MessageSet(msg_ids='{self.msg_ids}', is_uid={self.is_uid}, "
            f"mailbox='{self.mailbox}', estimated_count={self.estimated_count})"
        )
    
    def is_empty(self) -> bool:
        """Check if message set is empty."""
        return not self.msg_ids
    
    def is_single_message(self) -> bool:
        """Check if message set contains only one message."""
        return len(self.parsed_ids) == 1 and not self.id_ranges
    
    def is_range_only(self) -> bool:
        """Check if message set contains only ranges."""
        return not self.parsed_ids and bool(self.id_ranges)
    
    def has_open_range(self) -> bool:
        """Check if message set has open-ended ranges (ending with '*')."""
        return any(end == "*" for _, end in self.id_ranges)
    
    def get_first_id(self) -> Optional[int]:
        """Get first message ID (if deterministic)."""
        if self.parsed_ids:
            return min(self.parsed_ids)
        
        if self.id_ranges:
            first_range = self.id_ranges[0]
            if isinstance(first_range[0], int):
                return first_range[0]
        
        return None
    
    def get_last_id(self) -> Optional[int]:
        """Get last message ID (if deterministic)."""
        if self.parsed_ids:
            return max(self.parsed_ids)
        
        if self.id_ranges:
            last_range = self.id_ranges[-1]
            if isinstance(last_range[1], int):
                return last_range[1]
        
        return None
    
    def union(self, other: "MessageSet") -> "MessageSet":
        """
        Combine with another message set.
        
        Parameters
        ----------
        other : MessageSet
            Other message set to combine with
            
        Returns
        -------
        MessageSet
            Combined message set
        """
        if self.is_uid != other.is_uid:
            raise ValueError("Cannot combine UID and sequence number message sets")
        
        if self.mailbox and other.mailbox and self.mailbox != other.mailbox:
            logger.warning(
                f"Combining message sets from different mailboxes: "
                f"{self.mailbox} and {other.mailbox}"
            )
        
        # Combine IDs
        combined_ids = f"{self.msg_ids},{other.msg_ids}"
        
        return MessageSet(
            msg_ids=combined_ids,
            is_uid=self.is_uid,
            mailbox=self.mailbox or other.mailbox
        )
    
    def intersection(self, other: "MessageSet") -> "MessageSet":
        """
        Get intersection with another message set.
        
        Note: Only works with individual IDs, not ranges.
        """
        if self.is_uid != other.is_uid:
            raise ValueError("Cannot intersect UID and sequence number message sets")
        
        # Get intersection of individual IDs
        common_ids = set(self.parsed_ids) & set(other.parsed_ids)
        
        if not common_ids:
            raise ValueError("No common messages found")
        
        return MessageSet(
            msg_ids=list(common_ids),
            is_uid=self.is_uid,
            mailbox=self.mailbox or other.mailbox
        )
    
    def subtract(self, other: "MessageSet") -> "MessageSet":
        """
        Remove messages from another set.
        
        Note: Only works with individual IDs, not ranges.
        """
        if self.is_uid != other.is_uid:
            raise ValueError("Cannot subtract UID and sequence number message sets")
        
        # Remove other's IDs from this set
        remaining_ids = set(self.parsed_ids) - set(other.parsed_ids)
        
        if not remaining_ids:
            raise ValueError("No messages remaining after subtraction")
        
        return MessageSet(
            msg_ids=list(remaining_ids),
            is_uid=self.is_uid,
            mailbox=self.mailbox
        )
    
    def iter_batches(self, batch_size: int = 100) -> "MessageSetBatchIterator":
        """
        Iterate over message set in batches.
        
        Parameters
        ----------
        batch_size : int
            Size of each batch
            
        Returns
        -------
        MessageSetBatchIterator
            Iterator for batches
            
        Examples
        --------
        >>> large_set = MessageSet.from_uids(list(range(1000, 10000)))
        >>> for batch in large_set.iter_batches(batch_size=100):
        ...     process_batch(batch)
        """
        return MessageSetBatchIterator(self, batch_size)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation
        """
        return {
            "msg_ids": self.msg_ids,
            "is_uid": self.is_uid,
            "mailbox": self.mailbox,
            "estimated_count": self.estimated_count,
            "individual_ids": self.parsed_ids,
            "ranges": [(str(start), str(end)) for start, end in self.id_ranges],
            "has_open_range": self.has_open_range(),
            "first_id": self.get_first_id(),
            "last_id": self.get_last_id(),
        }
    
    def split_by_size(self, max_size: int) -> List["MessageSet"]:
        """
        Split message set into smaller sets based on estimated size.
        
        Parameters
        ----------
        max_size : int
            Maximum size for each resulting set
            
        Returns
        -------
        List[MessageSet]
            List of smaller message sets
        """
        if self.estimated_count <= max_size:
            return [self]
        
        # For individual IDs, split directly
        if self.parsed_ids and not self.id_ranges:
            chunks = []
            ids = self.parsed_ids
            
            for i in range(0, len(ids), max_size):
                chunk_ids = ids[i:i + max_size]
                chunks.append(MessageSet(
                    msg_ids=chunk_ids,
                    is_uid=self.is_uid,
                    mailbox=self.mailbox
                ))
            
            return chunks
        
        # For ranges, this is more complex and depends on actual message counts
        # For now, return the original set
        logger.warning("Cannot split message set containing ranges")
        return [self]
    
    def validate_for_mailbox(self, mailbox: str) -> None:
        """
        Validate message set for specific mailbox.
        
        Parameters
        ----------
        mailbox : str
            Mailbox name to validate against
        """
        if self.mailbox and self.mailbox != mailbox:
            raise ValueError(
                f"MessageSet is for mailbox '{self.mailbox}' but trying to use "
                f"with mailbox '{mailbox}'"
            )
        
        if not self.is_uid:
            logger.warning(
                f"Using sequence numbers for mailbox '{mailbox}'. "
                f"Consider using UIDs for reliable operations."
            )


class MessageSetBatchIterator:
    """
    Iterator for processing message sets in batches.
    
    This iterator helps process large message sets efficiently by breaking
    them into smaller, manageable batches.
    """
    
    def __init__(self, message_set: MessageSet, batch_size: int):
        self.message_set = message_set
        self.batch_size = batch_size
        self.current_index = 0
        self.individual_ids = message_set.parsed_ids
        
        # For ranges, we can't easily batch, so we'll work with what we have
        if message_set.id_ranges:
            logger.warning("Batching with ranges is not fully supported")
    
    def __iter__(self):
        return self
    
    def __next__(self) -> MessageSet:
        if self.current_index >= len(self.individual_ids):
            raise StopIteration
        
        # Get next batch of IDs
        batch_ids = self.individual_ids[
            self.current_index:self.current_index + self.batch_size
        ]
        
        self.current_index += self.batch_size
        
        # Create new MessageSet for this batch
        return MessageSet(
            msg_ids=batch_ids,
            is_uid=self.message_set.is_uid,
            mailbox=self.message_set.mailbox
        )
    
    def __len__(self) -> int:
        """Get total number of batches."""
        return (len(self.individual_ids) + self.batch_size - 1) // self.batch_size


# Utility functions for message set operations
def create_uid_set(uids: List[int], mailbox: Optional[str] = None) -> MessageSet:
    """Convenience function to create UID-based message set."""
    return MessageSet.from_uids(uids, mailbox)


def create_sequence_set(seq_nums: List[int], mailbox: Optional[str] = None) -> MessageSet:
    """Convenience function to create sequence-based message set (not recommended)."""
    return MessageSet.from_sequence_numbers(seq_nums, mailbox)


def merge_message_sets(sets: List[MessageSet]) -> MessageSet:
    """
    Merge multiple message sets into one.
    
    Parameters
    ----------
    sets : List[MessageSet]
        List of message sets to merge
        
    Returns
    -------
    MessageSet
        Merged message set
    """
    if not sets:
        raise ValueError("Cannot merge empty list of message sets")
    
    if len(sets) == 1:
        return sets[0]
    
    # Ensure all sets have the same type
    first_set = sets[0]
    for msg_set in sets[1:]:
        if msg_set.is_uid != first_set.is_uid:
            raise ValueError("Cannot merge UID and sequence number message sets")
    
    # Combine all msg_ids
    combined_ids = []
    mailbox = first_set.mailbox
    
    for msg_set in sets:
        if msg_set.mailbox and msg_set.mailbox != mailbox:
            logger.warning(f"Merging message sets from different mailboxes")
        
        combined_ids.append(msg_set.msg_ids)
    
    return MessageSet(
        msg_ids=",".join(combined_ids),
        is_uid=first_set.is_uid,
        mailbox=mailbox
    )

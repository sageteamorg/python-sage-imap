from functools import wraps

from sage_imap.exceptions import IMAPMailboxSelectionError


def mailbox_selection_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.current_selection:
            raise IMAPMailboxSelectionError("No mailbox selected.")
        return func(self, *args, **kwargs)

    return wrapper

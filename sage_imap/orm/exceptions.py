"""ORM-layer errors and mapping to structured JSON schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from sage_imap.exceptions import IMAPClientError

if TYPE_CHECKING:
    from sage_imap.orm.schemas.error import ErrorSchema


class OrmError(Exception):
    """Base ORM error."""

    code: str = "orm_error"
    message: str = "An ORM error occurred."
    details: Optional[dict[str, Any]] = None

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        self.details = details

    def to_schema(self) -> "ErrorSchema":
        from sage_imap.orm.schemas.error import ErrorSchema

        return ErrorSchema(
            code=self.code,
            message=self.message,
            type=self.__class__.__name__,
            details=self.details,
        )


class OrmConfigurationError(OrmError):
    code = "orm_configuration_error"


class OrmNotConnectedError(OrmError):
    code = "orm_not_connected"


class OrmMailboxNotSelectedError(OrmError):
    code = "orm_mailbox_not_selected"


def error_schema_from_imap(exc: IMAPClientError) -> "ErrorSchema":
    from sage_imap.orm.schemas.error import ErrorSchema

    return ErrorSchema(
        code=exc.code,
        message=exc.detail,
        type=exc.__class__.__name__,
        status_code=exc.status_code,
        details=None,
    )

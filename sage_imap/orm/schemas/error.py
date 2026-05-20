"""Pydantic schemas for JSON-friendly ORM output."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorSchema(BaseModel):
    code: str
    message: str
    type: str
    status_code: Optional[int] = None
    details: Optional[dict[str, Any]] = None


class OperationResultSchema(BaseModel):
    success: bool
    operation: str
    message_count: int = 0
    affected_uids: list[int] = Field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[ErrorSchema] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def raise_safe_http_exception(
    status_code: int,
    message: str,
    *,
    log_message: str | None = None,
    exc: Exception | None = None,
) -> None:
    if exc is not None:
        logger.exception(log_message or message, exc_info=exc)
    elif log_message:
        logger.error(log_message)

    raise HTTPException(status_code=status_code, detail=message)


def safe_internal_error(
    message: str = "An unexpected error occurred.",
) -> dict[str, str]:
    return {"error": {"message": message, "code": "internal_error"}}


def safe_error_response(message: str, code: str) -> dict[str, dict[str, str]]:
    return {"error": {"message": message, "code": code}}

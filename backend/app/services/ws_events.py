from __future__ import annotations

from typing import Any, Optional


def ws_event(event: str, data: dict[str, Any] | None = None, correlation_id: Optional[str] = None) -> dict[str, Any]:
    return {
        "event": event,
        "correlation_id": correlation_id,
        "data": data or {},
    }


def ws_error(message: str, correlation_id: Optional[str] = None) -> dict[str, Any]:
    return ws_event("error", {"message": message}, correlation_id)

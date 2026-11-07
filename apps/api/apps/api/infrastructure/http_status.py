from __future__ import annotations

from starlette import status as starlette_status


def _unprocessable_entity_status() -> int:
    status_code = getattr(starlette_status, "HTTP_422_UNPROCESSABLE_CONTENT", None)
    if status_code is None:
        status_code = getattr(starlette_status, "HTTP_422_UNPROCESSABLE_ENTITY", None)
    if not isinstance(status_code, int):
        raise RuntimeError("Starlette does not define HTTP 422 status")
    return status_code


HTTP_422_UNPROCESSABLE_ENTITY = _unprocessable_entity_status()

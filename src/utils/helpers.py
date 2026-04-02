"""Response formatting and pagination helpers."""

from typing import Any

from flask import jsonify, request, Response


def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple[Response, int]:
    """Build a standardised JSON success response.

    Args:
        data: The payload to include under the ``data`` key.
        message: A human-readable message.
        status_code: HTTP status code (default 200).

    Returns:
        tuple[Response, int]: Flask response and status code.
    """
    body: dict = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def error_response(message: str, status_code: int = 400, errors: Any = None) -> tuple[Response, int]:
    """Build a standardised JSON error response.

    Args:
        message: A human-readable error message.
        status_code: HTTP status code (default 400).
        errors: Optional detailed error information.

    Returns:
        tuple[Response, int]: Flask response and status code.
    """
    body: dict = {"success": False, "message": message}
    if errors is not None:
        body["errors"] = errors
    return jsonify(body), status_code


def paginate_query(query, schema_fn=None) -> dict:
    """Paginate a SQLAlchemy query using ``page`` and ``per_page`` query params.

    Args:
        query: A SQLAlchemy query object.
        schema_fn: Optional callable to serialise each result item. Defaults to
                   calling ``.to_dict()`` on each item.

    Returns:
        dict: Pagination envelope with ``items``, ``total``, ``page``,
              ``per_page``, ``pages`` fields.
    """
    from src.config import get_config

    cfg = get_config()

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(
            cfg.MAX_PAGE_SIZE,
            max(1, int(request.args.get("per_page", cfg.DEFAULT_PAGE_SIZE))),
        )
    except (ValueError, TypeError):
        page = 1
        per_page = cfg.DEFAULT_PAGE_SIZE

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    serialise = schema_fn or (lambda item: item.to_dict())

    return {
        "items": [serialise(item) for item in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }

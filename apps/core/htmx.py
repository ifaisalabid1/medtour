"""Helpers for requests made by htmx (https://four.htmx.org)."""


def is_partial_request(request) -> bool:
    """True when htmx is swapping part of the page and wants only that fragment.

    htmx 4 sends HX-Request-Type "full" when it needs the whole page, for
    example to restore a page from history on Back, so those get the full page.
    """
    return (
        request.headers.get("HX-Request") == "true"
        and request.headers.get("HX-Request-Type") == "partial"
    )

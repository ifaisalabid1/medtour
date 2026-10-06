import pytest

from apps.core.htmx import is_partial_request


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({}, False),
        ({"HX-Request": "true", "HX-Request-Type": "partial"}, True),
        # htmx asks for the full page to restore history on Back.
        ({"HX-Request": "true", "HX-Request-Type": "full"}, False),
        ({"HX-Request-Type": "partial"}, False),
    ],
)
def test_only_htmx_swaps_of_part_of_the_page_are_partial(rf, headers, expected):
    assert is_partial_request(rf.get("/", headers=headers)) is expected

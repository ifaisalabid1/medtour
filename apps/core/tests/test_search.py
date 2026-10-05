import pytest
from django.contrib.postgres.search import SearchQuery

from apps.core.search import build_prefix_search_query


@pytest.mark.parametrize("text", ["", "   ", "& | !", "a b c", "'); --"])
def test_returns_none_when_nothing_is_searchable(text):
    assert build_prefix_search_query(text) is None


def test_returns_a_query_for_real_words():
    assert isinstance(build_prefix_search_query("knee replac"), SearchQuery)

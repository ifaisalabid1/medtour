"""Turn free text typed by visitors into safe PostgreSQL full-text queries."""

import operator
import re
from functools import reduce

from django.contrib.postgres.search import Lexeme, SearchQuery

SEARCH_CONFIG = "english"
MAX_QUERY_LENGTH = 100
MAX_TERMS = 8
MIN_TERM_LENGTH = 2


def build_prefix_search_query(text: str) -> SearchQuery | None:
    """Build an AND query where every word may be partial ("kne replac").

    Only real words are kept, and Lexeme escapes each one, so operators typed
    by a visitor (& | ! :) are never interpreted. Returns None when nothing
    searchable is left.
    """
    terms = [
        term
        for term in re.findall(r"\w+", text[:MAX_QUERY_LENGTH])
        if len(term) >= MIN_TERM_LENGTH
    ][:MAX_TERMS]
    if not terms:
        return None
    lexemes = reduce(operator.and_, (Lexeme(term, prefix=True) for term in terms))
    return SearchQuery(lexemes, config=SEARCH_CONFIG)

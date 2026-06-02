"""Lightweight lexical relevance scoring.

Used by skill routing, guide loading, and memory recall to decide what is
relevant to a request, without pulling in an embeddings dependency. The
scoring is deliberately simple and explainable: tokenize, weight by overlap,
boost exact trigger/keyword hits. Good enough to route, and easy to reason
about in an interview.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Common English words that carry no routing signal.
_STOPWORDS = frozenset(
    """
    a an and are as at be by for from has have how i in is it its of on or
    that the to was what when where which who will with you your me my our
    can could should would do does did this these those there here please
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens with stopwords removed."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


def relevance(query: str, *, text: str = "", keywords: Iterable[str] = ()) -> float:
    """Score how relevant `text`/`keywords` are to `query`, in [0, ~).

    - Each shared content token contributes 1.0 (scaled by query length).
    - Each exact keyword/trigger match contributes a 2.0 boost, keywords are
      curated, so a hit there is a stronger signal than incidental word overlap.
    """
    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0
    q_counts = Counter(q_tokens)

    text_tokens = set(tokenize(text))
    overlap = sum(q_counts[t] for t in text_tokens)

    keyword_hits = 0
    kw_tokens = {k.lower() for k in keywords}
    for tok in q_tokens:
        if tok in kw_tokens:
            keyword_hits += 1

    raw = overlap + 2.0 * keyword_hits
    # Normalize by query length so long queries don't inflate scores.
    return raw / len(q_tokens)

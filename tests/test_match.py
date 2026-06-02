from agent_ops._match import relevance, tokenize


def test_tokenize_strips_stopwords():
    assert tokenize("What is the MRR for the quarter") == ["mrr", "quarter"]


def test_relevance_rewards_keyword_hits():
    with_kw = relevance("how is churn trending", keywords=["churn"], text="")
    without_kw = relevance("how is churn trending", keywords=[], text="retention")
    assert with_kw > without_kw


def test_relevance_zero_for_empty_query():
    assert relevance("", text="anything", keywords=["x"]) == 0.0


def test_relevance_zero_for_no_overlap():
    assert relevance("revenue expansion", text="weather forecast", keywords=["rain"]) == 0.0

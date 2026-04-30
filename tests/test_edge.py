from app.engine.edge import calculate_edge, implied_probability


def test_implied_probability_from_decimal_odds():
    assert implied_probability(2.0) == 0.5
    assert round(implied_probability("1.80"), 4) == 0.5556


def test_positive_edge():
    assert round(calculate_edge(0.58, 2.0), 2) == 8.0


def test_negative_edge():
    assert round(calculate_edge(0.40, 2.0), 2) == -10.0


def test_invalid_odds_are_ignored():
    assert calculate_edge(0.55, 1.0) is None
    assert calculate_edge(0.55, None) is None
    assert calculate_edge(0.55, "bad") is None


def test_invalid_probability_is_ignored():
    assert calculate_edge(None, 2.0) is None
    assert calculate_edge(0, 2.0) is None
    assert calculate_edge(1, 2.0) is None

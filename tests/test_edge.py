import json
from pathlib import Path

import pytest

from app.engine.edge import calculate_edge, edge_confidence, implied_probability


# ── implied_probability ──────────────────────────────────────────────────────

def test_implied_probability_from_decimal_odds():
    assert implied_probability(2.0) == 0.5
    assert round(implied_probability("1.80"), 4) == 0.5556


def test_implied_probability_rejects_nonsense():
    assert implied_probability(None) is None
    assert implied_probability("") is None
    assert implied_probability("abc") is None
    assert implied_probability(0) is None
    assert implied_probability(1.0) is None
    assert implied_probability(-2.0) is None
    assert implied_probability(float("inf")) is None
    assert implied_probability(float("nan")) is None


# ── calculate_edge ───────────────────────────────────────────────────────────

def test_positive_edge():
    assert round(calculate_edge(0.58, 2.0), 2) == 8.0


def test_negative_edge():
    assert round(calculate_edge(0.40, 2.0), 2) == -10.0


def test_zero_edge_when_market_matches_model():
    assert calculate_edge(0.5, 2.0) == pytest.approx(0.0, abs=1e-6)


def test_invalid_odds_are_ignored():
    assert calculate_edge(0.55, 1.0) is None
    assert calculate_edge(0.55, None) is None
    assert calculate_edge(0.55, "bad") is None


def test_invalid_probability_is_ignored():
    assert calculate_edge(None, 2.0) is None
    assert calculate_edge(0, 2.0) is None
    assert calculate_edge(1, 2.0) is None
    assert calculate_edge(-0.1, 2.0) is None
    assert calculate_edge(1.5, 2.0) is None
    assert calculate_edge("oops", 2.0) is None


# ── edge_confidence ──────────────────────────────────────────────────────────

def test_confidence_unknown_when_edge_is_none():
    assert edge_confidence(None) == "unknown"


def test_confidence_medium_with_strong_signal():
    assert edge_confidence(7.0, home_matches=8, away_matches=6) == "medium"


def test_confidence_low_with_weaker_sample():
    assert edge_confidence(3.0, home_matches=4, away_matches=3) == "low"


def test_confidence_watch_when_thin():
    assert edge_confidence(0.5, home_matches=10, away_matches=10) == "watch"
    assert edge_confidence(8.0, home_matches=2, away_matches=10) == "watch"


def test_confidence_never_medium_for_negative_edge():
    assert edge_confidence(-5.0, home_matches=10, away_matches=10) == "watch"


# ── edges.json contract ──────────────────────────────────────────────────────

EDGES_PATH = Path(__file__).parent.parent / "docs" / "data" / "edges.json"


@pytest.mark.skipif(not EDGES_PATH.exists(), reason="edges.json not generated yet")
def test_edges_feed_top_level_keys():
    feed = json.loads(EDGES_PATH.read_text(encoding="utf-8"))
    for key in ("updated_at", "source", "items"):
        assert key in feed, f"missing top-level key: {key}"
    assert isinstance(feed["items"], list)


@pytest.mark.skipif(not EDGES_PATH.exists(), reason="edges.json not generated yet")
def test_edges_feed_items_have_required_fields():
    feed = json.loads(EDGES_PATH.read_text(encoding="utf-8"))
    required = {
        "league", "date", "home", "away",
        "market", "odds",
        "probability", "implied_probability", "edge_pct",
    }
    for i, item in enumerate(feed["items"][:20]):
        missing = required - set(item.keys())
        assert not missing, f"items[{i}] missing fields: {missing}"


@pytest.mark.skipif(not EDGES_PATH.exists(), reason="edges.json not generated yet")
def test_edges_feed_math_consistent():
    feed = json.loads(EDGES_PATH.read_text(encoding="utf-8"))
    for item in feed["items"][:20]:
        expected = (item["probability"] - item["implied_probability"]) * 100
        assert item["edge_pct"] == pytest.approx(expected, abs=0.05), (
            f"item {item.get('id')} edge_pct {item['edge_pct']} != "
            f"(prob {item['probability']} - implied {item['implied_probability']}) * 100"
        )

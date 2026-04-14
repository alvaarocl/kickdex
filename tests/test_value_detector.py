"""Tests para el motor de value detection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.probability import calculate_probabilities, MatchProbabilities
from app.engine.value_detector import calculate_value, ValueResult

PROBS_HOME_FAVORED = MatchProbabilities(home=0.60, draw=0.25, away=0.15, over25=0.65, btts=0.55)
PROBS_BALANCED = MatchProbabilities(home=0.40, draw=0.30, away=0.30, over25=0.50, btts=0.50)


def test_value_detected_when_odds_too_generous():
    """Cuota 2.50 implica 40% pero nosotros calculamos 60% → VALUE."""
    results = calculate_value(PROBS_HOME_FAVORED, b365h=2.50, b365d=3.40, b365a=6.00)
    home_result = next((r for r in results if "Local" in r.market), None)
    assert home_result is not None
    assert home_result.is_value is True
    assert home_result.ev > 0


def test_no_value_when_odds_too_tight():
    """Cuota 1.50 implica 66.7% pero nosotros calculamos 40% → NO value."""
    results = calculate_value(PROBS_BALANCED, b365h=1.50, b365d=3.40, b365a=6.00)
    home_result = next((r for r in results if "Local" in r.market), None)
    assert home_result is not None
    assert home_result.is_value is False


def test_none_odds_excluded():
    """Si B365H es None, no debe aparecer en resultados."""
    results = calculate_value(PROBS_HOME_FAVORED, b365h=None, b365d=3.40, b365a=6.00)
    markets = [r.market for r in results]
    assert not any("Local" in m for m in markets)


def test_invalid_odds_excluded():
    """Cuotas < 1.01 o > 50 deben ignorarse."""
    results = calculate_value(PROBS_HOME_FAVORED, b365h=0.5, b365d=100.0, b365a=2.10)
    # Solo el away debería aparecer
    assert len(results) <= 1


def test_ev_formula():
    """EV = (prob * odds) - 1."""
    results = calculate_value(PROBS_HOME_FAVORED, b365h=2.00, b365d=None, b365a=None)
    if results:
        r = results[0]
        expected_ev = round(r.our_prob * r.odds - 1, 4)
        assert abs(r.ev - expected_ev) < 0.001


def test_results_sorted_value_first():
    """Los value bets deben aparecer primero."""
    results = calculate_value(PROBS_HOME_FAVORED, b365h=2.50, b365d=3.40, b365a=6.00)
    if len(results) >= 2:
        # Si el primero tiene value, los siguientes pueden no tenerlo
        if results[0].is_value:
            pass  # OK
        else:
            # Si el primero no tiene value, ninguno debe tenerlo
            assert all(not r.is_value for r in results)

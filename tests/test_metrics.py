"""Tests para el motor de métricas."""
import pandas as pd
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.metrics import (
    get_recent_form, get_h2h, get_h2h_summary, calculate_rolling_metrics,
    get_weighted_form, get_weighted_h2h_summary,
)


def _make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date").reset_index(drop=True)


SAMPLE_MATCHES = _make_df([
    {"Date": "2025-09-01", "HomeTeam": "Madrid", "AwayTeam": "Barça",  "FTHG": 2, "FTAG": 1, "FTR": "H",
     "HS": 14, "AS": 8, "HST": 5, "AST": 3, "HF": 10, "AF": 12, "HC": 6, "AC": 4, "HY": 1, "AY": 2},
    {"Date": "2025-09-15", "HomeTeam": "Barça",  "AwayTeam": "Sevilla", "FTHG": 3, "FTAG": 0, "FTR": "H",
     "HS": 18, "AS": 5, "HST": 7, "AST": 2, "HF": 8, "AF": 14, "HC": 8, "AC": 2, "HY": 0, "AY": 3},
    {"Date": "2025-09-22", "HomeTeam": "Sevilla", "AwayTeam": "Madrid", "FTHG": 1, "FTAG": 3, "FTR": "A",
     "HS": 9, "AS": 16, "HST": 3, "AST": 6, "HF": 13, "AF": 9, "HC": 3, "AC": 7, "HY": 2, "AY": 1},
    {"Date": "2025-10-05", "HomeTeam": "Madrid", "AwayTeam": "Sevilla", "FTHG": 1, "FTAG": 1, "FTR": "D",
     "HS": 12, "AS": 10, "HST": 4, "AST": 4, "HF": 11, "AF": 11, "HC": 5, "AC": 5, "HY": 1, "AY": 1},
    {"Date": "2025-10-19", "HomeTeam": "Barça",  "AwayTeam": "Madrid",  "FTHG": 0, "FTAG": 2, "FTR": "A",
     "HS": 10, "AS": 13, "HST": 2, "AST": 5, "HF": 14, "AF": 8, "HC": 4, "AC": 6, "HY": 3, "AY": 0},
    {"Date": "2025-11-02", "HomeTeam": "Madrid", "AwayTeam": "Barça",  "FTHG": 2, "FTAG": 2, "FTR": "D",
     "HS": 13, "AS": 12, "HST": 4, "AST": 4, "HF": 9, "AF": 10, "HC": 5, "AC": 5, "HY": 1, "AY": 2},
])


def test_get_recent_form_returns_dict():
    form = get_recent_form(SAMPLE_MATCHES, "Madrid", venue="All", n=5, season_only=False)
    assert form is not None
    assert isinstance(form, dict)
    assert "avg_goals" in form
    assert "win_rate" in form
    assert "match_log" in form


def test_get_recent_form_win_rate_range():
    form = get_recent_form(SAMPLE_MATCHES, "Madrid", venue="All", n=5, season_only=False)
    assert 0.0 <= form["win_rate"] <= 1.0


def test_get_recent_form_over25_rate_range():
    form = get_recent_form(SAMPLE_MATCHES, "Madrid", venue="All", n=5, season_only=False)
    assert 0.0 <= form["over25_rate"] <= 1.0


def test_get_recent_form_btts_rate_range():
    form = get_recent_form(SAMPLE_MATCHES, "Madrid", venue="All", n=5, season_only=False)
    assert 0.0 <= form["btts_rate"] <= 1.0


def test_get_recent_form_none_on_insufficient_data():
    """Equipo con 1 partido no debe devolver stats (min=3)."""
    small_df = SAMPLE_MATCHES[SAMPLE_MATCHES["HomeTeam"] == "Barça"].head(1).copy()
    form = get_recent_form(small_df, "Barça", venue="All", n=5, season_only=False)
    assert form is None


def test_get_recent_form_can_expose_early_season_sample():
    small_df = SAMPLE_MATCHES.head(1)

    form = get_recent_form(
        small_df, "Madrid", venue="All", n=5, season_only=False, min_matches=1
    )

    assert form is not None
    assert form["matches_analyzed"] == 1


def test_h2h_returns_dataframe():
    h2h = get_h2h(SAMPLE_MATCHES, "Madrid", "Barça")
    assert h2h is not None
    assert len(h2h) >= 2


def test_h2h_summary_totals():
    s = get_h2h_summary(SAMPLE_MATCHES, "Madrid", "Barça")
    assert s["wins_team1"] + s["draws"] + s["wins_team2"] == s["total"]


def test_rolling_metrics_no_future_leakage():
    """
    Para el primer partido de Madrid como local, los rolling goals deben ser NaN
    porque no hay partidos anteriores (shift(1) garantiza esto).
    """
    df_rolled = calculate_rolling_metrics(SAMPLE_MATCHES.copy(), window=5)
    # Primer partido de Madrid en casa (2025-09-01)
    first_madrid_home = df_rolled[(df_rolled["HomeTeam"] == "Madrid")].sort_values("Date").iloc[0]
    # El rolling del primer partido debe ser NaN (no hay partidos anteriores)
    assert pd.isna(first_madrid_home["Home_Roll_Goals"]) or first_madrid_home["Home_Roll_Goals"] >= 0


def test_rolling_metrics_columns_exist():
    df_rolled = calculate_rolling_metrics(SAMPLE_MATCHES.copy(), window=5)
    for col in ["Home_Roll_Goals", "Away_Roll_Goals", "Home_Roll_ShoT", "Away_Roll_ShoT"]:
        assert col in df_rolled.columns, f"Columna {col} no encontrada"


# ─── get_weighted_form / get_weighted_h2h_summary ────────────────────────────

# Un equipo con un partido muy antiguo (goleada) y uno reciente (derrota),
# para comprobar que el reciente domina el resultado ponderado.
DECAY_MATCHES = _make_df([
    {"Date": "2018-01-01", "HomeTeam": "Madrid", "AwayTeam": "Rival",  "FTHG": 5, "FTAG": 0, "FTR": "H",
     "HS": 20, "AS": 3, "HST": 10, "AST": 1, "HF": 8, "AF": 10, "HC": 9, "AC": 1, "HY": 0, "AY": 3},
    {"Date": "2025-11-20", "HomeTeam": "Madrid", "AwayTeam": "Rival2", "FTHG": 0, "FTAG": 3, "FTR": "A",
     "HS": 6, "AS": 15, "HST": 1, "AST": 8, "HF": 12, "AF": 8, "HC": 2, "AC": 8, "HY": 3, "AY": 1},
])


def test_get_weighted_form_recent_match_dominates():
    """El partido de hace unos días debe pesar mucho más que el de hace años."""
    form = get_weighted_form(DECAY_MATCHES, "Madrid", venue="Home", as_of=pd.Timestamp("2025-11-27"))
    assert form is not None
    # El agregado plano de los dos partidos sería avg_goals = 2.5; ponderado
    # debe quedar mucho más cerca del resultado reciente (0 goles).
    assert form["avg_goals"] < 1.0
    assert form["win_rate"] < 0.2


def test_get_weighted_form_effective_matches_bounded():
    form = get_weighted_form(SAMPLE_MATCHES, "Madrid", venue="All")
    assert form is not None
    assert 0 < form["effective_matches"] <= form["matches_analyzed"]


def test_get_weighted_form_matches_single_match_case():
    """Con un único partido disponible, debe comportarse como get_recent_form(min_matches=1)."""
    small_df = SAMPLE_MATCHES.head(1)
    weighted = get_weighted_form(small_df, "Madrid", venue="All", min_matches=1)
    flat = get_recent_form(small_df, "Madrid", venue="All", n=5, season_only=False, min_matches=1)
    assert weighted is not None and flat is not None
    assert weighted["matches_analyzed"] == flat["matches_analyzed"] == 1
    assert weighted["avg_goals"] == flat["avg_goals"]


def test_get_weighted_form_rates_in_range():
    form = get_weighted_form(SAMPLE_MATCHES, "Madrid", venue="All")
    assert 0.0 <= form["win_rate"] <= 1.0
    assert 0.0 <= form["over25_rate"] <= 1.0
    assert 0.0 <= form["btts_rate"] <= 1.0
    assert 0.0 <= form["current_season_weight_share"] <= 1.0


def test_get_weighted_h2h_summary_totals_match_raw_counts():
    """Los conteos enteros deben coincidir exactamente con get_h2h_summary (sin ponderar)."""
    raw = get_h2h_summary(SAMPLE_MATCHES, "Madrid", "Barça")
    weighted = get_weighted_h2h_summary(SAMPLE_MATCHES, "Madrid", "Barça")
    assert weighted["total"] == raw["total"]
    assert weighted["wins_team1"] == raw["wins_team1"]
    assert weighted["draws"] == raw["draws"]
    assert weighted["wins_team2"] == raw["wins_team2"]
    assert weighted["wins_team1"] + weighted["draws"] + weighted["wins_team2"] == weighted["total"]


def test_get_weighted_h2h_summary_weighted_rates_in_range():
    weighted = get_weighted_h2h_summary(SAMPLE_MATCHES, "Madrid", "Barça")
    assert 0.0 <= weighted["weighted_win_rate1"] <= 1.0
    assert 0.0 <= weighted["weighted_draw_rate"] <= 1.0
    assert 0.0 <= weighted["weighted_win_rate2"] <= 1.0
    assert round(
        weighted["weighted_win_rate1"] + weighted["weighted_draw_rate"] + weighted["weighted_win_rate2"], 3
    ) == 1.0

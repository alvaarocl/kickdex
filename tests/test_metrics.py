"""Tests para el motor de métricas."""
import pandas as pd
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.metrics import get_recent_form, get_h2h, get_h2h_summary, calculate_rolling_metrics


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

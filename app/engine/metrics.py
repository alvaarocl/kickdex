"""
Motor de métricas — calcula forma reciente y estadísticas de equipo.
Usa shift(1) para evitar data leakage: cada partido solo ve partidos anteriores.
"""

import logging
from typing import Literal

import numpy as np
import pandas as pd

from app.config import (
    CURRENT_SEASON_START,
    MIN_MATCHES_FOR_STATS,
    ROLLING_WINDOW_DEFAULT,
)

logger = logging.getLogger(__name__)

Venue = Literal["Home", "Away", "All"]


# ─── Rolling metrics sobre el DataFrame completo ─────────────────────────────

def calculate_rolling_metrics(df: pd.DataFrame, window: int = ROLLING_WINDOW_DEFAULT) -> pd.DataFrame:
    """
    Añade columnas de forma reciente al DataFrame de partidos.
    Anti-leakage: cada fila solo usa partidos ANTERIORES (shift(1)).

    Columnas añadidas por equipo (Home/Away):
      {side}_Roll_Goals, {side}_Roll_Shots, {side}_Roll_ShoT,
      {side}_Roll_Fouls, {side}_Roll_Corners, {side}_Roll_Cards

    Args:
        df: DataFrame de partidos ordenado por fecha.
        window: Ventana de partidos para el rolling mean.
    Returns:
        DataFrame con columnas adicionales de rolling metrics.
    """
    df = df.copy().sort_values("Date").reset_index(drop=True)

    metrics_home = {
        "Home_Roll_Goals":   "FTHG",
        "Home_Roll_Shots":   "HS",
        "Home_Roll_ShoT":    "HST",
        "Home_Roll_Fouls":   "HF",
        "Home_Roll_Corners": "HC",
        "Home_Roll_Cards":   "HY",
    }
    metrics_away = {
        "Away_Roll_Goals":   "FTAG",
        "Away_Roll_Shots":   "AS",
        "Away_Roll_ShoT":    "AST",
        "Away_Roll_Fouls":   "AF",
        "Away_Roll_Corners": "AC",
        "Away_Roll_Cards":   "AY",
    }

    for col in list(metrics_home) + list(metrics_away):
        df[col] = np.nan

    all_teams = set(df["HomeTeam"].dropna()) | set(df["AwayTeam"].dropna())

    for team in all_teams:
        home_idx = df.index[df["HomeTeam"] == team].tolist()
        away_idx = df.index[df["AwayTeam"] == team].tolist()

        # --- Métricas como LOCAL ---
        if home_idx:
            h = df.loc[home_idx].sort_values("Date").copy()
            for out_col, src_col in metrics_home.items():
                if src_col in h.columns:
                    vals = pd.to_numeric(h[src_col], errors="coerce")
                    rolled = vals.shift(1).rolling(window=window, min_periods=1).mean()
                    df.loc[rolled.index, out_col] = rolled.values

        # --- Métricas como VISITANTE ---
        if away_idx:
            a = df.loc[away_idx].sort_values("Date").copy()
            for out_col, src_col in metrics_away.items():
                if src_col in a.columns:
                    vals = pd.to_numeric(a[src_col], errors="coerce")
                    rolled = vals.shift(1).rolling(window=window, min_periods=1).mean()
                    df.loc[rolled.index, out_col] = rolled.values

    return df


# ─── Forma reciente de un equipo concreto ────────────────────────────────────

def get_recent_form(
    df: pd.DataFrame,
    team: str,
    venue: Venue = "All",
    n: int = ROLLING_WINDOW_DEFAULT,
    season_only: bool = True,
) -> dict | None:
    """
    Calcula la forma reciente de un equipo basada en sus últimos N partidos.

    Args:
        df: DataFrame completo de partidos.
        team: Nombre del equipo (normalizado).
        venue: "Home", "Away" o "All".
        n: Número de partidos a considerar.
        season_only: Si True, limita a la temporada actual.
    Returns:
        Dict con promedios, historial de partidos y conteos, o None si no hay datos.
    """
    source = df[df["Date"] >= CURRENT_SEASON_START].copy() if season_only else df.copy()

    if venue == "Home":
        matches = source[source["HomeTeam"] == team]
    elif venue == "Away":
        matches = source[source["AwayTeam"] == team]
    else:
        matches = source[(source["HomeTeam"] == team) | (source["AwayTeam"] == team)]

    matches = matches.sort_values("Date", ascending=True).tail(n)

    if len(matches) < MIN_MATCHES_FOR_STATS:
        return None

    stats: dict[str, list] = {
        "goals": [], "goals_against": [], "shots": [], "shots_on": [],
        "corners": [], "cards": [], "fouls": [],
        "xg_proxy": [],
    }
    match_log: list[dict] = []
    wins = draws = losses = 0

    for _, r in matches.iterrows():
        is_home = r["HomeTeam"] == team
        opp = r["AwayTeam"] if is_home else r["HomeTeam"]

        gf = float(r["FTHG"] if is_home else r["FTAG"]) if pd.notna(r.get("FTHG")) else 0.0
        ga = float(r["FTAG"] if is_home else r["FTHG"]) if pd.notna(r.get("FTAG")) else 0.0

        sot = float(r.get("HST" if is_home else "AST", 0) or 0)
        stats["goals"].append(gf)
        stats["goals_against"].append(ga)
        stats["shots"].append(float(r.get("HS" if is_home else "AS", 0) or 0))
        stats["shots_on"].append(sot)
        stats["corners"].append(float(r.get("HC" if is_home else "AC", 0) or 0))
        stats["cards"].append(float(r.get("HY" if is_home else "AY", 0) or 0))
        stats["fouls"].append(float(r.get("HF" if is_home else "AF", 0) or 0))
        stats["xg_proxy"].append(round(sot * 0.35, 2))  # Aproximación xG

        if gf > ga:
            result, wins = "W", wins + 1
        elif gf < ga:
            result, losses = "L", losses + 1
        else:
            result, draws = "D", draws + 1

        match_log.append({
            "date": r["Date"].strftime("%d/%m/%Y") if pd.notna(r["Date"]) else "?",
            "opponent": opp,
            "score": f"{int(gf)}-{int(ga)}",
            "result": result,
            "venue": "C" if is_home else "F",
        })

    def _avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0.0

    total = wins + draws + losses
    return {
        "team": team,
        "matches_analyzed": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": round(wins / total, 3) if total else 0.0,
        "avg_goals": _avg(stats["goals"]),
        "avg_goals_against": _avg(stats["goals_against"]),
        "avg_shots": _avg(stats["shots"]),
        "avg_shots_on": _avg(stats["shots_on"]),
        "avg_corners": _avg(stats["corners"]),
        "avg_cards": _avg(stats["cards"]),
        "avg_fouls": _avg(stats["fouls"]),
        "avg_xg_proxy": _avg(stats["xg_proxy"]),
        # Tasas para smart alerts
        "over25_rate": round(
            sum(1 for g, ga in zip(stats["goals"], stats["goals_against"]) if g + ga > 2.5) / total, 3
        ) if total else 0.0,
        "btts_rate": round(
            sum(1 for g, ga in zip(stats["goals"], stats["goals_against"]) if g > 0 and ga > 0) / total, 3
        ) if total else 0.0,
        "clean_sheet_rate": round(
            sum(1 for ga in stats["goals_against"] if ga == 0) / total, 3
        ) if total else 0.0,
        "match_log": match_log,
    }


# ─── H2H ────────────────────────────────────────────────────────────────────

def get_h2h(df: pd.DataFrame, team1: str, team2: str) -> pd.DataFrame | None:
    """
    Devuelve todos los enfrentamientos entre team1 y team2, ordenados por fecha desc.
    Incluye resultado y cuotas Bet365 si están disponibles.
    """
    mask = (
        ((df["HomeTeam"] == team1) & (df["AwayTeam"] == team2)) |
        ((df["HomeTeam"] == team2) & (df["AwayTeam"] == team1))
    )
    h2h = df[mask].sort_values("Date", ascending=False).copy()

    if h2h.empty:
        return None

    h2h["Resultado"] = h2h.apply(
        lambda r: f"{r['HomeTeam']} {int(r['FTHG'])}-{int(r['FTAG'])} {r['AwayTeam']}"
        if pd.notna(r["FTHG"]) and pd.notna(r["FTAG"]) else "?-?",
        axis=1,
    )

    cols = ["Date", "Resultado"]
    for c in ["B365H", "B365D", "B365A", "Liga"]:
        if c in h2h.columns:
            cols.append(c)

    return h2h[cols]


def get_h2h_summary(df: pd.DataFrame, team1: str, team2: str) -> dict:
    """
    Resumen estadístico del H2H entre dos equipos.
    Returns dict con wins1, draws, wins2, avg_goals, over25_rate.
    """
    h2h = get_h2h(df, team1, team2)
    if h2h is None or h2h.empty:
        return {}

    full = df[
        ((df["HomeTeam"] == team1) & (df["AwayTeam"] == team2)) |
        ((df["HomeTeam"] == team2) & (df["AwayTeam"] == team1))
    ].copy()

    wins1 = draws = wins2 = 0
    total_goals = []
    over25 = 0

    for _, r in full.iterrows():
        hg = float(r["FTHG"]) if pd.notna(r["FTHG"]) else 0
        ag = float(r["FTAG"]) if pd.notna(r["FTAG"]) else 0
        total = hg + ag
        total_goals.append(total)
        if total > 2.5:
            over25 += 1

        if r["HomeTeam"] == team1:
            if hg > ag: wins1 += 1
            elif hg == ag: draws += 1
            else: wins2 += 1
        else:
            if ag > hg: wins1 += 1
            elif hg == ag: draws += 1
            else: wins2 += 1

    n = len(full)
    return {
        "total": n,
        "wins_team1": wins1,
        "draws": draws,
        "wins_team2": wins2,
        "avg_goals": round(sum(total_goals) / n, 2) if n else 0,
        "over25_rate": round(over25 / n, 3) if n else 0,
        "btts_rate": round(
            sum(1 for _, r in full.iterrows()
                if pd.notna(r["FTHG"]) and pd.notna(r["FTAG"])
                and float(r["FTHG"]) > 0 and float(r["FTAG"]) > 0) / n, 3
        ) if n else 0,
    }

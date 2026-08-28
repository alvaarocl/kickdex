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
    HALF_LIFE_DAYS,
    MAX_LOOKBACK_MATCHES,
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
    min_matches: int = MIN_MATCHES_FOR_STATS,
) -> dict | None:
    """
    Calcula la forma reciente de un equipo basada en sus últimos N partidos.

    Args:
        df: DataFrame completo de partidos.
        team: Nombre del equipo (normalizado).
        venue: "Home", "Away" o "All".
        n: Número de partidos a considerar.
        season_only: Si True, limita a la temporada actual.
        min_matches: Muestra mínima exigida; el frontend puede usar 1 al
            inicio de temporada y presentar el tamaño de muestra.
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

    if len(matches) < min_matches:
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


def get_weighted_form(
    df: pd.DataFrame,
    team: str,
    venue: Venue = "All",
    as_of: pd.Timestamp | str | None = None,
    half_life_days: float = HALF_LIFE_DAYS,
    max_matches: int = MAX_LOOKBACK_MATCHES,
    min_matches: int = 1,
) -> dict | None:
    """
    Forma de un equipo ponderada por antigüedad, sobre todo el historial
    disponible (no solo temporada actual ni un tail(5) fijo).

    Cada partido pesa `0.5 ** (dias_desde_el_partido / half_life_days)`, así
    que un partido reciente pesa más que uno antiguo sin necesidad de elegir
    entre "temporada actual" o "histórico" como hace `get_recent_form`.

    Args:
        df: DataFrame completo de partidos (todas las temporadas).
        team: Nombre del equipo (normalizado).
        venue: "Home", "Away" o "All".
        as_of: Fecha de referencia para el decaimiento; None = fecha máxima
            disponible en `df` (build_edges debe pasar la fecha del fixture
            para no filtrar por "hoy" y respetar el anti-leakage).
        half_life_days: Días para que el peso de un partido caiga a la mitad.
        max_matches: Tope de partidos más recientes a incluir (rendimiento;
            con el decaimiento por defecto, un partido de hace 3 años ya
            pesa ~6%, así que un tope generoso no cambia el resultado).
        min_matches: Partidos mínimos para devolver algo (no None).

    Returns:
        Mismo shape que `get_recent_form()` (avg_goals, win_rate, over25_rate,
        etc.) más `effective_matches` (tamaño de muestra efectivo, ponderado)
        y `current_season_weight_share` (fracción del peso que viene de la
        temporada en curso), o None si no hay datos suficientes.
    """
    if venue == "Home":
        matches = df[df["HomeTeam"] == team]
    elif venue == "Away":
        matches = df[df["AwayTeam"] == team]
    else:
        matches = df[(df["HomeTeam"] == team) | (df["AwayTeam"] == team)]

    matches = matches.sort_values("Date", ascending=True).tail(max_matches)

    if len(matches) < min_matches:
        return None

    reference_date = pd.Timestamp(as_of) if as_of is not None else matches["Date"].max()
    season_start = pd.Timestamp(CURRENT_SEASON_START)

    rows: list[dict] = []
    match_log: list[dict] = []

    for _, r in matches.iterrows():
        match_date = r["Date"]
        if pd.isna(match_date):
            continue
        days_since = (reference_date - match_date).days
        if days_since < 0:
            # Nunca debería pasar (anti-leakage aguas arriba lo evita), pero
            # por seguridad no dejamos que un partido "futuro" tenga peso >1.
            days_since = 0
        weight = 0.5 ** (days_since / half_life_days) if half_life_days > 0 else 1.0

        is_home = r["HomeTeam"] == team
        opp = r["AwayTeam"] if is_home else r["HomeTeam"]

        gf = float(r["FTHG"] if is_home else r["FTAG"]) if pd.notna(r.get("FTHG")) else 0.0
        ga = float(r["FTAG"] if is_home else r["FTHG"]) if pd.notna(r.get("FTAG")) else 0.0
        sot = float(r.get("HST" if is_home else "AST", 0) or 0)

        if gf > ga:
            result = "W"
        elif gf < ga:
            result = "L"
        else:
            result = "D"

        rows.append({
            "weight": weight,
            "in_current_season": match_date >= season_start,
            "goals": gf,
            "goals_against": ga,
            "shots": float(r.get("HS" if is_home else "AS", 0) or 0),
            "shots_on": sot,
            "corners": float(r.get("HC" if is_home else "AC", 0) or 0),
            "cards": float(r.get("HY" if is_home else "AY", 0) or 0),
            "fouls": float(r.get("HF" if is_home else "AF", 0) or 0),
            "xg_proxy": round(sot * 0.35, 2),
            "win": 1.0 if result == "W" else 0.0,
            "draw": 1.0 if result == "D" else 0.0,
            "loss": 1.0 if result == "L" else 0.0,
            "over25": 1.0 if (gf + ga) > 2.5 else 0.0,
            "btts": 1.0 if (gf > 0 and ga > 0) else 0.0,
            "clean_sheet": 1.0 if ga == 0 else 0.0,
        })

        match_log.append({
            "date": match_date.strftime("%d/%m/%Y") if pd.notna(match_date) else "?",
            "opponent": opp,
            "score": f"{int(gf)}-{int(ga)}",
            "result": result,
            "venue": "C" if is_home else "F",
        })

    if not rows:
        return None

    total_weight = sum(r["weight"] for r in rows)
    if total_weight <= 0:
        return None

    def _wavg(key: str) -> float:
        return round(sum(r["weight"] * r[key] for r in rows) / total_weight, 3)

    current_season_weight = sum(r["weight"] for r in rows if r["in_current_season"])
    current_season_matches = sum(1 for r in rows if r["in_current_season"])

    return {
        "team": team,
        "matches_analyzed": len(rows),
        "current_season_matches": current_season_matches,
        "effective_matches": round(total_weight, 1),
        "current_season_weight_share": round(current_season_weight / total_weight, 3),
        "wins": round(sum(r["win"] for r in rows), 1),
        "draws": round(sum(r["draw"] for r in rows), 1),
        "losses": round(sum(r["loss"] for r in rows), 1),
        "win_rate": _wavg("win"),
        "avg_goals": round(_wavg("goals"), 2),
        "avg_goals_against": round(_wavg("goals_against"), 2),
        "avg_shots": round(_wavg("shots"), 2),
        "avg_shots_on": round(_wavg("shots_on"), 2),
        "avg_corners": round(_wavg("corners"), 2),
        "avg_cards": round(_wavg("cards"), 2),
        "avg_fouls": round(_wavg("fouls"), 2),
        "avg_xg_proxy": round(_wavg("xg_proxy"), 2),
        "over25_rate": _wavg("over25"),
        "btts_rate": _wavg("btts"),
        "clean_sheet_rate": _wavg("clean_sheet"),
        "match_log": match_log[-10:],
    }


def get_weighted_referee_form(
    df: pd.DataFrame,
    as_of: pd.Timestamp | str | None = None,
    half_life_days: float = HALF_LIFE_DAYS,
    max_matches: int = MAX_LOOKBACK_MATCHES,
    min_matches: int = 3,
) -> dict | None:
    """
    Forma de un árbitro ponderada por antigüedad — mismo principio que
    `get_weighted_form()` para equipos (decaimiento exponencial en vez de un
    `tail(N)` plano sin peso), aplicado a tarjetas/faltas/penaltis en lugar
    de goles. Sin distinción local/visitante: una sola pasada por partido.

    Espera un DataFrame ya normalizado (ver `_normalise_referee_frame` en
    `scripts/build_data.py`) con columnas `Date`, `_Y`, `_R`, `_F`, `_P`.

    Returns:
        Dict con `matches`, `effective_matches` (tamaño de muestra
        ponderado), `yellows_per_match`, `reds_per_match`, `fouls_per_match`,
        `penalties_per_match`, `last_match`; o None si no hay partidos
        suficientes.
    """
    if df is None or df.empty or "Date" not in df.columns:
        return None
    matches = df.dropna(subset=["Date"]).sort_values("Date", ascending=True).tail(max_matches)
    if len(matches) < min_matches:
        return None

    reference_date = pd.Timestamp(as_of) if as_of is not None else matches["Date"].max()

    rows: list[dict] = []
    for _, r in matches.iterrows():
        match_date = r["Date"]
        days_since = max(0, (reference_date - match_date).days)
        weight = 0.5 ** (days_since / half_life_days) if half_life_days > 0 else 1.0
        rows.append({
            "weight": weight,
            "yellows": float(r.get("_Y", 0) or 0),
            "reds": float(r.get("_R", 0) or 0),
            "fouls": float(r.get("_F", 0) or 0),
            "penalties": float(r.get("_P", 0) or 0),
        })

    total_weight = sum(r["weight"] for r in rows)
    if total_weight <= 0:
        return None

    def _wavg(key: str) -> float:
        return round(sum(r["weight"] * r[key] for r in rows) / total_weight, 2)

    return {
        "matches": len(rows),
        "effective_matches": round(total_weight, 1),
        "yellows_per_match": _wavg("yellows"),
        "reds_per_match": _wavg("reds"),
        "fouls_per_match": _wavg("fouls"),
        "penalties_per_match": _wavg("penalties"),
        "last_match": matches["Date"].max().strftime("%Y-%m-%d"),
    }


def calculate_player_percentiles(df_players: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el Z-Score y percentil de cada jugador en métricas clave.
    Compara al jugador contra todos los demás de la liga para dar contexto 'Pro'.
    """
    if df_players.empty:
        return df_players
        
    cols_to_score = ["sh", "sot", "gls", "ast"]
    df = df_players.copy()
    
    # Agrupar por jugador para tener sus medias de temporada
    player_stats = df.groupby("player")[cols_to_score].mean()
    
    for col in cols_to_score:
        mean = player_stats[col].mean()
        std = player_stats[col].std()
        if std > 0:
            # Z-Score: (x - mean) / std
            z_col = f"{col}_z"
            player_stats[z_col] = (player_stats[col] - mean) / std
            # Convertir a Percentil (0-100) simplificado
            from scipy.stats import norm
            player_stats[f"{col}_pct"] = player_stats[z_col].apply(lambda x: norm.cdf(x) * 100)
            
    return player_stats.reset_index()


# ─── H2H ────────────────────────────────────────────────────────────────────

def get_h2h(df: pd.DataFrame, team1: str, team2: str) -> pd.DataFrame | None:
    """
    Devuelve todos los enfrentamientos entre team1 y team2, ordenados por fecha desc.
    Incluye resultado y liga si están disponibles.
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

    # Incluir campos separados de equipo y marcador para que el pipeline
    # pueda emitirlos en h2h.json en vez de la cadena combinada "Resultado".
    cols = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "Resultado"]
    for c in ["Liga", "Div"]:
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


def get_weighted_h2h_summary(
    df: pd.DataFrame,
    team1: str,
    team2: str,
    as_of: pd.Timestamp | str | None = None,
    half_life_days: float = HALF_LIFE_DAYS,
) -> dict:
    """
    Igual que `get_h2h_summary`, pero da más peso a los enfrentamientos
    recientes que a los antiguos (mismo decaimiento que `get_weighted_form`).

    Los conteos enteros (`total`, `wins_team1`, `draws`, `wins_team2`) se
    devuelven SIN ponderar — son los mismos que `get_h2h_summary` produciría
    (así `wins_team1 + draws + wins_team2 == total` sigue siendo cierto).
    Se añaden `weighted_win_rate1`, `weighted_draw_rate`, `weighted_win_rate2`
    y se recalculan `avg_goals`/`over25_rate`/`btts_rate` con el peso por
    antigüedad, para usar en el blend de probabilidades.
    """
    full = df[
        ((df["HomeTeam"] == team1) & (df["AwayTeam"] == team2)) |
        ((df["HomeTeam"] == team2) & (df["AwayTeam"] == team1))
    ].copy()
    full = full[pd.notna(full["Date"])]
    if full.empty:
        return {}

    reference_date = pd.Timestamp(as_of) if as_of is not None else full["Date"].max()

    wins1 = draws = wins2 = 0
    rows: list[dict] = []

    for _, r in full.iterrows():
        hg = float(r["FTHG"]) if pd.notna(r["FTHG"]) else 0.0
        ag = float(r["FTAG"]) if pd.notna(r["FTAG"]) else 0.0
        total_goals = hg + ag

        if r["HomeTeam"] == team1:
            team1_won, team2_won = hg > ag, hg < ag
        else:
            team1_won, team2_won = ag > hg, ag < hg

        if team1_won:
            wins1 += 1
        elif team2_won:
            wins2 += 1
        else:
            draws += 1

        days_since = max(0, (reference_date - r["Date"]).days)
        weight = 0.5 ** (days_since / half_life_days) if half_life_days > 0 else 1.0

        rows.append({
            "weight": weight,
            "goals": total_goals,
            "over25": 1.0 if total_goals > 2.5 else 0.0,
            "btts": 1.0 if (hg > 0 and ag > 0) else 0.0,
            "win1": 1.0 if team1_won else 0.0,
            "draw": 0.0 if (team1_won or team2_won) else 1.0,
            "win2": 1.0 if team2_won else 0.0,
        })

    n = len(full)
    total_weight = sum(r["weight"] for r in rows)

    def _wavg(key: str) -> float:
        return round(sum(r["weight"] * r[key] for r in rows) / total_weight, 3) if total_weight else 0.0

    return {
        "total": n,
        "wins_team1": wins1,
        "draws": draws,
        "wins_team2": wins2,
        "avg_goals": round(_wavg("goals"), 2),
        "over25_rate": _wavg("over25"),
        "btts_rate": _wavg("btts"),
        "effective_total": round(total_weight, 1),
        "weighted_win_rate1": _wavg("win1"),
        "weighted_draw_rate": _wavg("draw"),
        "weighted_win_rate2": _wavg("win2"),
    }

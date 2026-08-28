"""Trend detection for KICKDEX match intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass(frozen=True)
class TrendRule:
    key: str
    label: str
    metric: Callable[[dict], bool]
    category: str


WINDOWS = (5, 8, 10)


def _num(value, default: float = 0.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if pd.isna(value):
        return default
    return value


RULES = (
    TrendRule("scored_1", "marca +0.5 goles", lambda m: m["gf"] >= 1, "goles"),
    TrendRule("scored_2", "marca +1.5 goles", lambda m: m["gf"] >= 2, "goles"),
    TrendRule("conceded_1", "recibe +0.5 goles", lambda m: m["ga"] >= 1, "goles_contra"),
    TrendRule("conceded_2", "recibe +1.5 goles", lambda m: m["ga"] >= 2, "goles_contra"),
    TrendRule("over_15", "+1.5 goles partido", lambda m: m["gf"] + m["ga"] >= 2, "totales"),
    TrendRule("over_25", "+2.5 goles partido", lambda m: m["gf"] + m["ga"] >= 3, "totales"),
    TrendRule("under_35", "-3.5 goles partido", lambda m: m["gf"] + m["ga"] <= 3, "totales"),
    TrendRule("btts", "BTTS", lambda m: m["gf"] > 0 and m["ga"] > 0, "totales"),
    TrendRule("unbeaten", "no pierde", lambda m: m["result"] in {"W", "D"}, "resultado"),
    TrendRule("wins", "gana", lambda m: m["result"] == "W", "resultado"),
    TrendRule("cards_3", "3+ tarjetas partido", lambda m: m["cards_total"] >= 3, "disciplina"),
    TrendRule("cards_4", "4+ tarjetas partido", lambda m: m["cards_total"] >= 4, "disciplina"),
    TrendRule("corners_8", "8+ corners partido", lambda m: m["corners_total"] >= 8, "corners"),
    TrendRule("corners_9", "9+ corners partido", lambda m: m["corners_total"] >= 9, "corners"),
)


def _team_match_log(df: pd.DataFrame, team: str, venue: str = "all", limit: int = 20) -> list[dict]:
    if df is None or df.empty:
        return []
    source = df.copy()
    if "Date" in source.columns:
        source["Date"] = pd.to_datetime(source["Date"], errors="coerce")
    source = source.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    if venue == "home":
        source = source[source["HomeTeam"] == team]
    elif venue == "away":
        source = source[source["AwayTeam"] == team]
    else:
        source = source[(source["HomeTeam"] == team) | (source["AwayTeam"] == team)]
    source = source.sort_values("Date", ascending=False).head(limit)

    matches = []
    for _, row in source.iterrows():
        is_home = row["HomeTeam"] == team
        gf = _num(row["FTHG"] if is_home else row["FTAG"])
        ga = _num(row["FTAG"] if is_home else row["FTHG"])
        result = "W" if gf > ga else "D" if gf == ga else "L"
        matches.append({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "opponent": str(row["AwayTeam"] if is_home else row["HomeTeam"]),
            "venue": "home" if is_home else "away",
            "gf": gf,
            "ga": ga,
            "result": result,
            "corners_total": _num(row.get("HC")) + _num(row.get("AC")),
            "cards_total": _num(row.get("HY")) + _num(row.get("AY")) + _num(row.get("HR")) + _num(row.get("AR")),
        })
    return matches


def _trends_from_matches(matches: list[dict], team: str, venue: str) -> list[dict]:
    """Core trend detection given an already-built, date-desc match log."""
    if len(matches) < 5:
        return []

    trends = []
    for rule in RULES:
        best = None
        for window in WINDOWS:
            sample = matches[:window]
            if len(sample) < window:
                continue
            hits = sum(1 for item in sample if rule.metric(item))
            if hits < max(4, window - 1):
                continue
            candidate = {
                "team": team,
                "venue": venue,
                "key": rule.key,
                "category": rule.category,
                "text": f"{rule.label} L{hits}/{window} {venue_label(venue)}",
                "hits": hits,
                "window": window,
                "rate": round(hits / window, 3),
                "sequence": [1 if rule.metric(item) else 0 for item in sample],
            }
            if best is None or (candidate["rate"], candidate["window"]) > (best["rate"], best["window"]):
                best = candidate
        if best:
            trends.append(best)

    trends.sort(key=lambda item: (item["rate"], item["window"], item["hits"]), reverse=True)
    return trends[:10]


def detect_team_trends(df: pd.DataFrame, team: str, venue: str = "all", limit: int = 20) -> list[dict]:
    """Return strongest readable trends for a team and venue context.

    Kept for callers that work with a single team; the batch builder uses a
    one-pass index instead (see build_trends_payload).
    """
    return _trends_from_matches(_team_match_log(df, team, venue=venue, limit=limit), team, venue)


def venue_label(venue: str) -> str:
    if venue == "home":
        return "local"
    if venue == "away":
        return "visitante"
    return "global"


def _build_team_match_index(df: pd.DataFrame, limit: int = 20) -> dict[str, dict[str, list[dict]]]:
    """One pass over the sorted frame → per-team date-desc match logs by venue."""
    index: dict[str, dict[str, list[dict]]] = {}
    if df is None or df.empty:
        return index

    source = df
    if not pd.api.types.is_datetime64_any_dtype(source["Date"]):
        source = source.assign(Date=pd.to_datetime(source["Date"], errors="coerce"))
    source = source.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    source = source.sort_values("Date", ascending=False)

    cols = ("Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "HC", "AC", "HY", "AY", "HR", "AR")
    present = [c for c in cols if c in source.columns]
    for row in source[present].itertuples(index=False):
        r = dict(zip(present, row))
        date_str = r["Date"].strftime("%Y-%m-%d")
        hc, ac = _num(r.get("HC")), _num(r.get("AC"))
        cards = _num(r.get("HY")) + _num(r.get("AY")) + _num(r.get("HR")) + _num(r.get("AR"))
        for team, is_home in ((r["HomeTeam"], True), (r["AwayTeam"], False)):
            team = str(team)
            gf = _num(r["FTHG"] if is_home else r["FTAG"])
            ga = _num(r["FTAG"] if is_home else r["FTHG"])
            match = {
                "date": date_str,
                "opponent": str(r["AwayTeam"] if is_home else r["HomeTeam"]),
                "venue": "home" if is_home else "away",
                "gf": gf,
                "ga": ga,
                "result": "W" if gf > ga else "D" if gf == ga else "L",
                "corners_total": hc + ac,
                "cards_total": cards,
            }
            bucket = index.setdefault(team, {"all": [], "home": [], "away": []})
            if len(bucket["all"]) < limit:
                bucket["all"].append(match)
            venue_key = "home" if is_home else "away"
            if len(bucket[venue_key]) < limit:
                bucket[venue_key].append(match)
    return index


def build_trends_payload(df: pd.DataFrame, teams: list[str], season_start=None) -> dict:
    """Build static trends JSON for all teams (single-pass over the frame)."""
    source = df
    if season_start is not None and "Date" in getattr(source, "columns", []):
        source = source.assign(Date=pd.to_datetime(source["Date"], errors="coerce"))
        source = source[source["Date"] >= pd.Timestamp(season_start)]

    index = _build_team_match_index(source)
    empty = {"all": [], "home": [], "away": []}

    result = {}
    for team in teams:
        buckets = index.get(str(team), empty)
        result[str(team)] = {
            venue: _trends_from_matches(buckets[venue], str(team), venue)
            for venue in ("all", "home", "away")
        }
    return {"teams": result}

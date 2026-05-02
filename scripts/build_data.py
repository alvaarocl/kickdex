"""
build_data.py — Genera los JSON estáticos para el frontend de GitHub Pages.
Ejecutar localmente o via GitHub Actions (diariamente).

Salida: docs/data/*.json
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.data.updater import update_data
from app.data.loader import load_matches, load_players, get_team_list, invalidate_cache
from app.data.fixture_download import fetch_fixture_download_calendar
from app.engine.metrics import (
    get_recent_form, get_h2h, get_h2h_summary, calculate_rolling_metrics
)
from app.engine.probability import calculate_probabilities
from app.engine.edge import calculate_edge, edge_confidence, implied_probability
from app.engine.trends import build_trends_payload
from app.engine.smart_alerts import generate_alerts, AlertStrength
from app.config import CURRENT_SEASON_LABEL, CURRENT_SEASON_START, ROLLING_WINDOW_DEFAULT

OUTPUT_DIR = ROOT / "docs" / "data"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe(val, decimals=2):
    """Convierte a float redondeado o None si NaN."""
    try:
        import math
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, decimals)
    except Exception:
        return None


def _serialize_form(form: dict | None) -> dict | None:
    if not form:
        return None
    result = {}
    for k, v in form.items():
        if k == "team":
            continue
        if k == "match_log":
            result[k] = v
        elif isinstance(v, float):
            result[k] = _safe(v)
        else:
            result[k] = v
    return result


def write_json(data, filename: str):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"), default=str)
    print(f"  OK {filename}  ({path.stat().st_size / 1024:.1f} KB)")


def _read_existing_json(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_player_json(data, filename: str):
    """Preserve existing player JSON if the fresh scrape has lower coverage."""
    existing = _read_existing_json(filename)
    existing_teams = len(existing) if isinstance(existing, dict) else 0
    new_teams = len(data) if isinstance(data, dict) else 0
    if existing_teams > 0 and new_teams < existing_teams:
        print(f"  KEEP {filename}  (nuevo: {new_teams} equipos, existente: {existing_teams})")
        return
    write_json(data, filename)


def write_fixtures_json(data, filename: str = "fixtures.json"):
    """Preserve the current calendar if external fixture sources fail empty."""
    existing = _read_existing_json(filename)
    existing_upcoming = len(existing.get("upcoming", [])) if isinstance(existing, dict) else 0
    new_upcoming = len(data.get("upcoming", [])) if isinstance(data, dict) else 0
    fd_status = (data.get("meta") or {}).get("fixture_download") if isinstance(data, dict) else {}
    fd_leagues = (fd_status or {}).get("leagues") or {}
    source_failed = bool(fd_leagues) and not any(info.get("ok") for info in fd_leagues.values() if isinstance(info, dict))
    if existing_upcoming > 0 and new_upcoming == 0 and source_failed:
        print(f"  KEEP {filename}  (FixtureDownload falló; preservados {existing_upcoming} próximos)")
        return
    write_json(data, filename)


def build_player_coverage(df_players, leagues: dict) -> dict:
    coverage = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_teams_with_players": 0,
        "total_player_rows": 0,
        "by_league": {},
    }
    if df_players is None or df_players.empty:
        return coverage
    coverage["total_teams_with_players"] = int(df_players["team"].nunique())
    coverage["total_player_rows"] = int(len(df_players))
    if "league" in df_players.columns:
        for code, grp in df_players.groupby("league"):
            league_code = str(code)
            league_info = leagues.get(league_code) or {}
            expected = set(league_info.get("teams", []))
            covered = set(grp["team"].dropna().astype(str))
            coverage["by_league"][league_code] = {
                "name": league_info.get("name", league_code),
                "teams_with_players": len(covered),
                "expected_teams": len(expected),
                "coverage_rate": round(len(covered & expected) / len(expected), 3) if expected else None,
                "missing_teams": sorted(expected - covered),
                "player_rows": int(len(grp)),
            }
    return coverage


def build_player_coverage_from_json(leagues: dict) -> dict:
    players = _read_existing_json("players.json")
    coverage = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_teams_with_players": 0,
        "total_player_rows": 0,
        "by_league": {},
    }
    if not isinstance(players, dict):
        return coverage
    covered_teams = set(players.keys())
    coverage["total_teams_with_players"] = len(covered_teams)
    coverage["total_player_rows"] = sum(len(v) for v in players.values() if isinstance(v, list))
    for code, info in leagues.items():
        expected = set(info.get("teams", []))
        matched = expected & covered_teams
        coverage["by_league"][code] = {
            "name": info.get("name", code),
            "teams_with_players": len(matched),
            "expected_teams": len(expected),
            "coverage_rate": round(len(matched) / len(expected), 3) if expected else None,
            "missing_teams": sorted(expected - covered_teams),
            "player_rows": sum(len(players.get(team, [])) for team in matched),
        }
    return coverage


def build_data_status(coverage: dict, source: str = "build_data") -> dict:
    by_league = coverage.get("by_league") or {}
    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "players": {
            "total_teams_with_players": coverage.get("total_teams_with_players", 0),
            "total_player_rows": coverage.get("total_player_rows", 0),
            "covered_leagues": sorted(by_league.keys()),
            "league_count": len(by_league),
            "all_covered": all((info.get("coverage_rate") or 0) >= 1 for info in by_league.values()) if by_league else False,
        },
    }


# ── Builders ──────────────────────────────────────────────────────────────────

def build_meta(df, df_current) -> dict:
    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "season": CURRENT_SEASON_LABEL,
        "total_matches": len(df),
        "current_season_matches": len(df_current),
    }


def build_team_stats(df, teams: list) -> dict:
    result = {}
    for i, team in enumerate(teams):
        if i % 10 == 0:
            print(f"    {i}/{len(teams)} equipos...")
        home = get_recent_form(df, team, venue="Home", n=ROLLING_WINDOW_DEFAULT)
        away = get_recent_form(df, team, venue="Away", n=ROLLING_WINDOW_DEFAULT)
        if not home and not away:
            continue
        result[team] = {
            "home": _serialize_form(home),
            "away": _serialize_form(away),
        }
    return result


def build_h2h(df, teams: list) -> dict:
    result = {}
    
    # Find unique pairs that actually played against each other
    actual_pairs = set()
    for _, row in df[['HomeTeam', 'AwayTeam']].dropna().drop_duplicates().iterrows():
        t1, t2 = sorted([row['HomeTeam'], row['AwayTeam']])
        if t1 in teams and t2 in teams:
            actual_pairs.add((t1, t2))
            
    pairs = list(actual_pairs)
    print(f"    Calculando {len(pairs)} pares reales (filtrado de {len(teams) * (len(teams)-1) // 2} posibles)...")

    for t1, t2 in pairs:
        summary = get_h2h_summary(df, t1, t2)
        if not summary or summary.get("total", 0) < 2:
            continue

        h2h_df = get_h2h(df, t1, t2)
        if h2h_df is None or h2h_df.empty:
            continue

        matches = []
        for _, row in h2h_df.head(25).iterrows():
            m = {
                "date": row["Date"].strftime("%Y-%m-%d") if hasattr(row["Date"], "strftime") else str(row["Date"]),
                "result": row["Resultado"],
            }
            for col, key in [("Liga", "league")]:
                if col in row.index:
                    v = row[col]
                    try:
                        import pandas as pd
                        if pd.notna(v):
                            m[key] = round(float(v), 2) if key != "league" else str(v)
                    except Exception:
                        pass
            matches.append(m)

        key = f"{t1}|{t2}"
        result[key] = {
            "team1": t1,
            "team2": t2,
            "summary": {
                "total": summary["total"],
                "wins1": summary["wins_team1"],
                "draws": summary["draws"],
                "wins2": summary["wins_team2"],
                "avg_goals": _safe(summary["avg_goals"]),
                "over25_rate": _safe(summary["over25_rate"]),
                "btts_rate": _safe(summary["btts_rate"]),
            },
            "matches": matches,
        }
    return result


def build_players(df_players) -> dict:
    if df_players is None or df_players.empty:
        return {}
    result = {}
    for team, grp in df_players.groupby("team"):
        players = []
        for player, pg in grp.groupby("player"):
            last = pg.sort_values("date", ascending=False).head(10)
            players.append({
                "player": player,
                "sh":   _safe(last["sh"].mean()),
                "sot":  _safe(last["sot"].mean()),
                "gls":  _safe(last["gls"].mean()),
                "ast":  _safe(last["ast"].mean()),
                "min":  _safe(last["min"].mean()),
                "fls":  _safe(last["fls"].mean()),
                "crdy": _safe(last["crdy"].mean()),
            })
        players.sort(key=lambda x: (x["sh"] or 0), reverse=True)
        result[str(team)] = players
    return result


def build_players_detail(df_players) -> dict:
    """Datos partido a partido para Player Props (últimos 20 por jugador)."""
    if df_players is None or df_players.empty:
        return {}
    result = {}
    for team, grp in df_players.groupby("team"):
        team_data = {}
        for player, pg in grp.groupby("player"):
            rows = []
            for _, r in pg.sort_values("date", ascending=False).head(20).iterrows():
                date_val = r.get("date")
                try:
                    import pandas as pd
                    date_str = date_val.strftime("%Y-%m-%d") if pd.notna(date_val) and hasattr(date_val, "strftime") else str(date_val or "")
                except Exception:
                    date_str = str(date_val or "")
                rows.append({
                    "date": date_str,
                    "sh":   _safe(r.get("sh", 0)),
                    "sot":  _safe(r.get("sot", 0)),
                    "gls":  _safe(r.get("gls", 0)),
                    "ast":  _safe(r.get("ast", 0)),
                    "min":  _safe(r.get("min", 0)),
                    "fls":  _safe(r.get("fls", 0)),
                    "crdy": _safe(r.get("crdy", 0)),
                })
            team_data[player] = rows
        result[str(team)] = team_data
    return result


def build_leagues(df, teams: list) -> dict:
    """Mapeo liga → equipos para el filtro de división en el frontend."""
    import pandas as pd
    from app.config import CURRENT_SEASON_START, LEAGUES
    if df is None or df.empty or "Date" not in df.columns:
        return {}
    current = df[df["Date"] >= CURRENT_SEASON_START]
    result = {}
    for code, name in LEAGUES.items():
        league_df = current[current["Div"] == code] if "Div" in current.columns else pd.DataFrame()
        if league_df.empty:
            continue
        league_teams = sorted(
            set(league_df["HomeTeam"].dropna()) | set(league_df["AwayTeam"].dropna())
        )
        result[code] = {"name": name, "teams": league_teams}
    return result


def _fixture_key(item: dict) -> tuple:
    return (
        item.get("league", ""),
        item.get("date", ""),
        item.get("home", ""),
        item.get("away", ""),
    )


def _merge_fixture_lists(primary: list[dict], secondary: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for item in secondary:
        merged[_fixture_key(item)] = item
    for item in primary:
        key = _fixture_key(item)
        merged[key] = {**merged.get(key, {}), **item}
    return list(merged.values())


def build_fixtures(df, leagues_json: dict | None = None) -> dict:
    """
    Genera partidos recientes (últimos 7 días) y próximos (NaN FTHG).
    Fuente: CSVs de la temporada actual descargados frescos.
    """
    import pandas as pd
    from datetime import datetime, timedelta
    from pathlib import Path
    from app.config import CURRENT_SEASON_CODE, DATA_DIR, LEAGUES

    recent = []
    upcoming = []
    leagues = LEAGUES
    cutoff = pd.Timestamp(datetime.utcnow() - timedelta(days=7))
    now = pd.Timestamp(datetime.utcnow())

    for code, name in leagues.items():
        path = Path(DATA_DIR) / f"{code}_{CURRENT_SEASON_CODE}.csv"
        if not path.exists():
            continue
        for enc in ("utf-8-sig", "latin1"):
            try:
                raw = pd.read_csv(path, encoding=enc, low_memory=False)
                raw.columns = [c.lstrip("\ufeff").strip() for c in raw.columns]
                break
            except Exception:
                continue
        else:
            continue

        if "Date" not in raw.columns:
            continue
        raw["Date"] = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce")
        raw = raw.dropna(subset=["Date"])

        for _, row in raw.iterrows():
            date = row["Date"]
            has_score = pd.notna(row.get("FTHG")) and pd.notna(row.get("FTAG"))
            item = {
                "league": code,
                "league_name": name,
                "date": date.strftime("%Y-%m-%d"),
                "time": str(row.get("Time", "") or "").strip(),
                "home": str(row.get("HomeTeam", "")),
                "away": str(row.get("AwayTeam", "")),
            }
            if has_score:
                item["home_score"] = int(row["FTHG"])
                item["away_score"] = int(row["FTAG"])
                if date >= cutoff:
                    recent.append(item)
            else:
                if date >= now - pd.Timedelta(days=1):
                    upcoming.append(item)

    fd_recent = []
    fd_upcoming = []
    fd_status = {}
    if leagues_json:
        try:
            league_teams = {code: info.get("teams", []) for code, info in leagues_json.items()}
            fd_recent, fd_upcoming, fd_status = fetch_fixture_download_calendar(leagues, league_teams)
            print(f"  OK FixtureDownload calendar ({len(fd_upcoming)} futuros, {len(fd_recent)} recientes)")
        except Exception as exc:
            fd_status = {"source": "fixturedownload", "ok": False, "error": str(exc)}
            print(f"  Warning FixtureDownload calendar: {exc}")

    recent = _merge_fixture_lists(primary=recent, secondary=fd_recent)
    upcoming = _merge_fixture_lists(primary=fd_upcoming, secondary=upcoming)

    recent.sort(key=lambda x: (x["date"], x.get("time", "")), reverse=True)
    upcoming.sort(key=lambda x: (x["date"], x.get("time", ""), x.get("league", "")))
    return {
        "recent": recent[:80],
        "upcoming": upcoming[:160],
        "meta": {
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sources": ["football-data.co.uk", "FixtureDownload"],
            "fixture_download": fd_status,
        },
    }


def _first_decimal(row, columns: tuple[str, ...]) -> float | None:
    for col in columns:
        if col not in row.index:
            continue
        value = _safe(row.get(col), decimals=3)
        if value is not None and value > 1:
            return value
    return None


def _match_status(row, date) -> str:
    import pandas as pd
    has_score = pd.notna(row.get("FTHG")) and pd.notna(row.get("FTAG"))
    if has_score:
        return "settled"
    return "upcoming" if date >= pd.Timestamp(datetime.utcnow().date()) else "unknown"


def _settled_outcome(row) -> str | None:
    home_goals = _safe(row.get("FTHG"), decimals=0)
    away_goals = _safe(row.get("FTAG"), decimals=0)
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return "home"
    if away_goals > home_goals:
        return "away"
    return "draw"


def build_edges(df) -> dict:
    """Generate real value edges from the Poisson model and Bet365 odds."""
    import pandas as pd
    from app.config import LEAGUES

    empty = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "season": CURRENT_SEASON_LABEL,
        "source": "football-data.co.uk Bet365 closing odds",
        "status": "empty",
        "top": None,
        "items": [],
        "stats": {"evaluated_matches": 0, "positive_edges": 0, "upcoming_edges": 0, "settled_edges": 0},
    }
    required = {"Date", "HomeTeam", "AwayTeam"}
    if df is None or df.empty or not required.issubset(df.columns):
        return empty

    data = df.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date", "HomeTeam", "AwayTeam"]).sort_values("Date").reset_index(drop=True)
    if data.empty:
        return empty

    candidates = data[data["Date"] >= pd.Timestamp(CURRENT_SEASON_START)].copy()
    markets = (
        ("home", ("B365CH", "B365H"), "Home"),
        ("draw", ("B365CD", "B365D"), "Draw"),
        ("away", ("B365CA", "B365A"), "Away"),
    )

    items = []
    evaluated = 0
    for idx, row in candidates.iterrows():
        date = row["Date"]
        league = str(row.get("Div", "") or "")
        home = str(row.get("HomeTeam", "") or "")
        away = str(row.get("AwayTeam", "") or "")
        if not home or not away:
            continue

        odds = {market: _first_decimal(row, columns) for market, columns, _ in markets}
        if not any(odds.values()):
            continue

        league_mask = data["Div"].eq(league) if "Div" in data.columns else True
        history = data[league_mask & (data["Date"] < date)].copy()
        home_form = get_recent_form(history, home, venue="Home", n=ROLLING_WINDOW_DEFAULT, season_only=False)
        away_form = get_recent_form(history, away, venue="Away", n=ROLLING_WINDOW_DEFAULT, season_only=False)
        if not home_form or not away_form:
            continue
        if home_form.get("matches_analyzed", 0) < 3 or away_form.get("matches_analyzed", 0) < 3:
            continue

        h2h_summary = get_h2h_summary(history, home, away)
        probabilities = calculate_probabilities(home_form, away_form, h2h_summary).as_dict()
        status = _match_status(row, date)
        outcome = _settled_outcome(row)
        evaluated += 1

        for market, _, label in markets:
            market_odds = odds.get(market)
            model_probability = probabilities.get(market)
            edge_pct = calculate_edge(model_probability, market_odds)
            if edge_pct is None or edge_pct < 1:
                continue
            if edge_pct > 25 or not 0.08 <= float(model_probability) <= 0.80:
                continue
            implied = implied_probability(market_odds)
            selection = home if market == "home" else away if market == "away" else "Empate"
            items.append({
                "id": f"{league}-{date.strftime('%Y%m%d')}-{home}-{away}-{market}".replace(" ", "_"),
                "date": date.strftime("%Y-%m-%d"),
                "time": str(row.get("Time", "") or "").strip(),
                "league": league,
                "league_name": LEAGUES.get(league, league),
                "home": home,
                "away": away,
                "market": market,
                "market_label": label,
                "selection": selection,
                "odds": round(float(market_odds), 2),
                "probability": _safe(model_probability, decimals=4),
                "implied_probability": _safe(implied, decimals=4),
                "edge_pct": round(edge_pct, 2),
                "status": status,
                "confidence": edge_confidence(edge_pct, home_form.get("matches_analyzed", 0), away_form.get("matches_analyzed", 0)),
                "result": {
                    "home_score": int(row["FTHG"]) if _safe(row.get("FTHG"), decimals=0) is not None else None,
                    "away_score": int(row["FTAG"]) if _safe(row.get("FTAG"), decimals=0) is not None else None,
                    "outcome": outcome,
                    "hit": (outcome == market) if outcome else None,
                },
                "model": {
                    "home_matches": int(home_form.get("matches_analyzed", 0)),
                    "away_matches": int(away_form.get("matches_analyzed", 0)),
                },
            })

    items.sort(key=lambda x: (1 if x["status"] == "upcoming" else 0, x["date"], x["edge_pct"]), reverse=True)
    upcoming = [item for item in items if item["status"] == "upcoming"]
    settled = [item for item in items if item["status"] == "settled"]
    latest_date = max((pd.Timestamp(item["date"]) for item in settled), default=None)
    recent_settled = [
        item for item in settled
        if latest_date is not None and pd.Timestamp(item["date"]) >= latest_date - pd.Timedelta(days=30)
    ]
    top_pool = upcoming or recent_settled or settled or items
    top = max(top_pool, key=lambda x: x["edge_pct"]) if top_pool else None
    status = "live_edges" if upcoming else "settled_only" if settled else "empty"
    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "season": CURRENT_SEASON_LABEL,
        "source": "football-data.co.uk Bet365 closing odds",
        "status": status,
        "top": top,
        "items": items[:300],
        "stats": {
            "evaluated_matches": evaluated,
            "positive_edges": len(items),
            "upcoming_edges": len(upcoming),
            "settled_edges": len(settled),
        },
    }


def _normalise_referee_frame(df, source: str = "csv"):
    import pandas as pd
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if "referee" in out.columns and "Referee" not in out.columns:
        out["Referee"] = out["referee"]
    if "league" in out.columns and "Div" not in out.columns:
        out["Div"] = out["league"]
    if "date" in out.columns and "Date" not in out.columns:
        out["Date"] = out["date"]
    if "Date" in out.columns:
        out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    out = out.dropna(subset=[c for c in ["Referee", "Div"] if c in out.columns])
    if out.empty or "Referee" not in out.columns or "Div" not in out.columns:
        return pd.DataFrame()
    out["Referee"] = out["Referee"].astype(str).str.strip()
    out["Div"] = out["Div"].astype(str).str.strip()
    def _num_col(name: str):
        if name in out.columns:
            return pd.to_numeric(out[name], errors="coerce").fillna(0)
        return pd.Series(0.0, index=out.index)

    has_incremental_cols = any(c in out.columns for c in ["yellow_cards", "red_cards", "fouls", "penalties"])
    if has_incremental_cols:
        out["_Y"] = _num_col("yellow_cards")
        out["_R"] = _num_col("red_cards")
        out["_F"] = _num_col("fouls")
        out["_P"] = _num_col("penalties")
    else:
        for col in ["HY", "AY", "HR", "AR", "HF", "AF"]:
            if col not in out.columns:
                out[col] = 0
        out["_Y"] = _num_col("HY") + _num_col("AY")
        out["_R"] = _num_col("HR") + _num_col("AR")
        out["_F"] = _num_col("HF") + _num_col("AF")
        out["_P"] = pd.Series(0.0, index=out.index)
    if "_source" not in out.columns:
        out["_source"] = source
    else:
        out["_source"] = out["_source"].fillna(source)
    return out


def _load_incremental_referees():
    import pandas as pd
    from app.config import DATA_DIR
    path = Path(DATA_DIR) / "referees_matches.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return _normalise_referee_frame(pd.read_csv(path, low_memory=False), "api-football")
    except Exception as e:
        print(f"  Warning: could not read {path}: {e}")
        return pd.DataFrame()


def _load_referee_season_aggregates():
    import pandas as pd
    from app.config import DATA_DIR
    path = Path(DATA_DIR) / "referees_season.csv"
    if not path.exists():
        return {}
    try:
        raw = pd.read_csv(path, low_memory=False)
    except Exception as e:
        print(f"  Warning: could not read {path}: {e}")
        return {}
    required = {"league", "referee", "matches", "yellow_cards", "red_cards"}
    if raw.empty or not required.issubset(raw.columns):
        return {}

    result = {}
    for _, row in raw.iterrows():
        try:
            matches = int(float(row.get("matches") or 0))
        except (TypeError, ValueError):
            matches = 0
        referee = str(row.get("referee") or "").strip()
        league = str(row.get("league") or "").strip()
        if not referee or not league or matches <= 0:
            continue

        yellow_cards = pd.to_numeric(pd.Series([row.get("yellow_cards")]), errors="coerce").fillna(0).iloc[0]
        second_yellow_cards = pd.to_numeric(pd.Series([row.get("second_yellow_cards")]), errors="coerce").fillna(0).iloc[0]
        red_cards = pd.to_numeric(pd.Series([row.get("red_cards")]), errors="coerce").fillna(0).iloc[0]
        result[(league, referee)] = {
            "matches": matches,
            "yellows_per_match": _safe(float(yellow_cards) / matches),
            "reds_per_match": _safe((float(second_yellow_cards) + float(red_cards)) / matches),
            "fouls_per_match": None,
            "penalties_per_match": None,
            "last_match": None,
            "source": str(row.get("source") or "worldsoccerdata"),
        }
    return result


def build_discipline_watch(players: dict, leagues: dict) -> dict:
    """Build a player card-risk watchlist from current player yellow-card rates.

    This is not an official suspension feed. It ranks players by yellow-card
    tendency using the player stats we already refresh.
    """
    by_team = {}
    by_league = {}
    top = []
    league_by_team = {}
    for code, info in (leagues or {}).items():
        for team in info.get("teams", []):
            league_by_team[team] = code

    for team, rows in (players or {}).items():
        league = league_by_team.get(team)
        team_items = []
        for row in rows or []:
            minutes = row.get("min")
            crdy = row.get("crdy")
            if minutes is None or crdy is None:
                continue
            try:
                minutes_f = float(minutes)
                crdy_f = float(crdy)
            except (TypeError, ValueError):
                continue
            if minutes_f < 25 or crdy_f < 0.12:
                continue
            crdy_p90 = crdy_f * 90 / minutes_f if minutes_f > 0 else None
            score = (crdy_f * 0.65) + ((crdy_p90 or 0) * 0.35)
            risk = "alto" if crdy_f >= 0.28 or (crdy_p90 or 0) >= 0.38 else "medio"
            item = {
                "player": row.get("player"),
                "team": team,
                "league": league,
                "league_name": (leagues.get(league) or {}).get("name", league),
                "minutes_per_match": _safe(minutes_f, 0),
                "yellow_cards_per_match": _safe(crdy_f, 2),
                "yellow_cards_p90": _safe(crdy_p90, 2),
                "risk_score": _safe(score, 3),
                "risk": risk,
                "label": "posible riesgo disciplinario",
                "official_suspension_status": False,
            }
            team_items.append(item)
            top.append(item)
            if league:
                by_league.setdefault(league, {
                    "name": (leagues.get(league) or {}).get("name", league),
                    "players": [],
                })["players"].append(item)

        if team_items:
            team_items.sort(key=lambda x: (x["risk_score"] or 0), reverse=True)
            by_team[team] = team_items[:8]

    top.sort(key=lambda x: (x["risk_score"] or 0), reverse=True)
    for block in by_league.values():
        block["players"].sort(key=lambda x: (x["risk_score"] or 0), reverse=True)
        block["players"] = block["players"][:30]

    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "players.json yellow-card rates",
        "status": "risk_model_not_official_suspension_feed",
        "disclaimer": "Lista orientativa por tendencia de tarjetas. No confirma apercibidos ni sanciones oficiales.",
        "thresholds": {
            "min_minutes_per_match": 25,
            "min_yellow_cards_per_match": 0.12,
            "high_risk_yellow_cards_per_match": 0.28,
            "high_risk_yellow_cards_p90": 0.38,
        },
        "top": top[:50],
        "by_team": by_team,
        "by_league": by_league,
    }


def _ref_stats(grp):
    import pandas as pd
    if grp is None or grp.empty:
        return None
    g = _normalise_referee_frame(grp, "csv")
    if g.empty:
        return None
    matches = int(len(g))
    if matches < 3:
        return None
    return {
        "matches": matches,
        "yellows_per_match": _safe(pd.to_numeric(g["_Y"], errors="coerce").fillna(0).sum() / matches),
        "reds_per_match": _safe(pd.to_numeric(g["_R"], errors="coerce").fillna(0).sum() / matches),
        "fouls_per_match": _safe(pd.to_numeric(g["_F"], errors="coerce").fillna(0).sum() / matches),
        "penalties_per_match": _safe(pd.to_numeric(g["_P"], errors="coerce").fillna(0).sum() / matches),
        "last_match": g["Date"].max().strftime("%Y-%m-%d") if "Date" in g.columns and pd.notna(g["Date"].max()) else None,
        "source": "api-football" if (g.get("_source") == "api-football").any() else "football-data",
    }


def build_referees(df, df_current=None) -> list:
    import pandas as pd
    if "Referee" not in df.columns or "Div" not in df.columns:
        return []
    rdf = _normalise_referee_frame(df, "football-data")
    incremental = _load_incremental_referees()
    season_aggregates = _load_referee_season_aggregates()
    if not incremental.empty:
        rdf = pd.concat([rdf, incremental], ignore_index=True)
    if rdf.empty:
        return []

    if df_current is not None and not df_current.empty and "Referee" in df_current.columns:
        rdf_curr = _normalise_referee_frame(df_current, "football-data")
    else:
        rdf_curr = pd.DataFrame(columns=rdf.columns)
    if not incremental.empty and "Date" in incremental.columns:
        from app.config import CURRENT_SEASON_START
        inc_curr = incremental[incremental["Date"] >= pd.Timestamp(CURRENT_SEASON_START)].copy()
        rdf_curr = pd.concat([rdf_curr, inc_curr], ignore_index=True)

    # Sort by date so head(N) = most recent N
    date_col = "Date" if "Date" in rdf.columns else None
    if date_col:
        rdf = rdf.sort_values(date_col, ascending=False)
        if not rdf_curr.empty:
            rdf_curr = rdf_curr.sort_values(date_col, ascending=False)

    results = []
    for (div, referee), grp in rdf.groupby(["Div", "Referee"], sort=False):
        overall = _ref_stats(grp)
        if overall is None:
            continue  # skip refs with < 3 matches total

        grp_curr = rdf_curr[(rdf_curr["Div"] == div) & (rdf_curr["Referee"] == referee)] if not rdf_curr.empty else pd.DataFrame()
        season_stats = season_aggregates.get((div, referee))
        if season_stats is None and not grp_curr.empty:
            season_stats = _ref_stats(grp_curr)

        record = {
            "name":    referee,
            "league":  div,
            # top-level legacy fields (used by old frontend code)
            "matches":           overall["matches"],
            "yellows_per_match": overall["yellows_per_match"],
            "reds_per_match":    overall["reds_per_match"],
            "fouls_per_match":   overall["fouls_per_match"],
            "penalties_per_match": overall.get("penalties_per_match"),
            "last_match":        overall.get("last_match"),
            "source":            overall.get("source"),
            # windowed blocks
            "overall":        overall,
            "last10":         _ref_stats(grp.head(10)),
            "last5":          _ref_stats(grp.head(5)),
            "season":         season_stats,
            "season_last10":  _ref_stats(grp_curr.head(10)) if not grp_curr.empty else None,
            "season_last5":   _ref_stats(grp_curr.head(5))  if not grp_curr.empty else None,
        }
        results.append(record)

    existing_keys = {(r["league"], r["name"]) for r in results}
    for (div, referee), season_stats in season_aggregates.items():
        if (div, referee) in existing_keys:
            continue
        results.append({
            "name": referee,
            "league": div,
            "matches": season_stats["matches"],
            "yellows_per_match": season_stats["yellows_per_match"],
            "reds_per_match": season_stats["reds_per_match"],
            "fouls_per_match": season_stats.get("fouls_per_match"),
            "penalties_per_match": season_stats.get("penalties_per_match"),
            "last_match": season_stats.get("last_match"),
            "source": season_stats.get("source"),
            "overall": season_stats,
            "last10": None,
            "last5": None,
            "season": season_stats,
            "season_last10": None,
            "season_last5": None,
        })

    # Merge manual overrides (e.g. SP1/SP2 refs not provided by football-data.co.uk)
    manual_path = Path("DATOS") / "referees_manual.json"
    if manual_path.exists():
        try:
            import json as _json
            manual = _json.loads(manual_path.read_text(encoding="utf-8"))
            existing = {(r["name"], r["league"]) for r in results}
            added = 0
            for r in manual:
                key = (r.get("name"), r.get("league"))
                if key not in existing:
                    results.append(r)
                    added += 1
            print(f"     Merged {added} manual referees from {manual_path}")
        except Exception as e:
            print(f"  Warning: could not merge manual referees: {e}")

    results.sort(key=lambda r: (r["league"], -r.get("yellows_per_match", 0)))
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("BUILD DATA - KICKDEX  -> docs/data/")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Descargar/actualizar CSVs
    print("\n[1/6] Actualizando CSVs...")
    if os.getenv("KICKDEX_SKIP_DOWNLOADS") == "1":
        print("     Saltado por KICKDEX_SKIP_DOWNLOADS=1")
    else:
        try:
            result = update_data(force_current=True)
            print(
                f"     {len(result['downloaded'])} descargados, "
                f"{len(result['skipped'])} saltados, {len(result['failed'])} fallidos"
            )
        except Exception as e:
            print(f"  Warning: {e}")

    # 2. Cargar datos
    print("\n[2/6] Cargando datos...")
    invalidate_cache()
    df = load_matches()
    df_players = load_players()
    if df.empty or "Date" not in df.columns:
        print("\nERROR: no hay CSVs historicos validos en datos/.")
        print("       Se conservan los JSON existentes en docs/data/ para no romper GitHub Pages.")
        print("       Descarga o copia los CSVs football-data en datos/ y vuelve a ejecutar este script.")
        return 1
    teams = get_team_list(df, recent_only=True)
    df_current = df[df["Date"] >= CURRENT_SEASON_START]
    print(f"     {len(df):,} partidos · {len(teams)} equipos · {len(df_players):,} registros jugadores")

    # 3. Meta
    print("\n[3/6] meta.json + teams.json...")
    write_json(build_meta(df, df_current), "meta.json")
    write_json(teams, "teams.json")

    # 4. Team stats
    print("\n[4/6] team_stats.json...")
    write_json(build_team_stats(df, teams), "team_stats.json")

    # 5. H2H
    print("\n[5/6] h2h.json...")
    write_json(build_h2h(df, teams), "h2h.json")

    # 6. Players + Leagues + Fixtures + Referees
    print("\n[6/7] players.json, players_detail.json, referees.json...")
    leagues = build_leagues(df, teams)
    players_payload = build_players(df_players)
    write_player_json(players_payload, "players.json")
    write_player_json(build_players_detail(df_players), "players_detail.json")
    coverage = build_player_coverage_from_json(leagues) if df_players.empty else build_player_coverage(df_players, leagues)
    write_json(coverage, "player_coverage.json")
    players_for_watch = _read_existing_json("players.json") or players_payload
    write_json(build_discipline_watch(players_for_watch, leagues), "discipline_watch.json")
    write_json(build_data_status(coverage), "data_status.json")
    write_json(build_referees(df, df_current), "referees.json")

    print("\n[7/7] leagues.json, fixtures.json, edges.json, trends.json...")
    write_json(leagues, "leagues.json")
    write_fixtures_json(build_fixtures(df, leagues))
    write_json(build_edges(df), "edges.json")
    write_json(build_trends_payload(df, teams, season_start=CURRENT_SEASON_START), "trends.json")

    print("\n" + "=" * 60)
    print("BUILD COMPLETADO")
    print("=" * 60)
    print(f"Archivos en: {OUTPUT_DIR.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

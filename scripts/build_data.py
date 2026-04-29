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
from app.engine.metrics import (
    get_recent_form, get_h2h, get_h2h_summary, calculate_rolling_metrics
)
from app.engine.smart_alerts import generate_alerts, AlertStrength
from app.engine.value_detector import scan_value_patterns
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
            for col, key in [("B365H", "b365h"), ("B365D", "b365d"), ("B365A", "b365a"), ("Liga", "league")]:
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


def build_fixtures(df) -> dict:
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
            for odds_col, key in [("B365H","odds_home"),("B365D","odds_draw"),("B365A","odds_away"),
                                   ("B365>2.5","odds_over25"),("B365<2.5","odds_under25")]:
                v = row.get(odds_col)
                try:
                    item[key] = round(float(v), 2) if pd.notna(v) else None
                except Exception:
                    item[key] = None

            if has_score:
                item["home_score"] = int(row["FTHG"])
                item["away_score"] = int(row["FTAG"])
                if date >= cutoff:
                    recent.append(item)
            else:
                if date >= now - pd.Timedelta(days=1):
                    upcoming.append(item)

    recent.sort(key=lambda x: x["date"], reverse=True)
    upcoming.sort(key=lambda x: x["date"])
    return {"recent": recent[:20], "upcoming": upcoming[:20]}


def build_value_patterns(df) -> list:
    try:
        df_proc = calculate_rolling_metrics(df)
        patterns = scan_value_patterns(df_proc)
        if patterns.empty:
            return []
        return patterns.head(25).to_dict("records")
    except Exception as e:
        print(f"  Warning value patterns: {e}")
        return []


def _ref_stats(sub_df, min_matches=3):
    """Compute per-match referee stats from a subset of matches. Returns None if too few rows."""
    import pandas as pd
    n = len(sub_df)
    if n < min_matches:
        return None
    def _col_sum(col):
        return pd.to_numeric(sub_df.get(col, pd.Series(0, index=sub_df.index)), errors="coerce").fillna(0).sum()
    yellows = _col_sum("HY") + _col_sum("AY")
    reds    = _col_sum("HR") + _col_sum("AR")
    fouls   = _col_sum("HF") + _col_sum("AF")
    return {
        "matches":           n,
        "yellows_per_match": round(float(yellows) / n, 2),
        "reds_per_match":    round(float(reds)    / n, 2),
        "fouls_per_match":   round(float(fouls)   / n, 2),
    }


def build_referees(df, df_current=None) -> list:
    import pandas as pd
    if "Referee" not in df.columns or "Div" not in df.columns:
        return []
    rdf = df.dropna(subset=["Referee", "Div"]).copy()
    rdf["Referee"] = rdf["Referee"].str.strip()
    if rdf.empty:
        return []

    if df_current is not None and not df_current.empty and "Referee" in df_current.columns:
        rdf_curr = df_current.dropna(subset=["Referee", "Div"]).copy()
        rdf_curr["Referee"] = rdf_curr["Referee"].str.strip()
    else:
        rdf_curr = pd.DataFrame(columns=rdf.columns)

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

        record = {
            "name":    referee,
            "league":  div,
            # top-level legacy fields (used by old frontend code)
            "matches":           overall["matches"],
            "yellows_per_match": overall["yellows_per_match"],
            "reds_per_match":    overall["reds_per_match"],
            "fouls_per_match":   overall["fouls_per_match"],
            # windowed blocks
            "overall":        overall,
            "last10":         _ref_stats(grp.head(10)),
            "last5":          _ref_stats(grp.head(5)),
            "season":         _ref_stats(grp_curr) if not grp_curr.empty else None,
            "season_last10":  _ref_stats(grp_curr.head(10)) if not grp_curr.empty else None,
            "season_last5":   _ref_stats(grp_curr.head(5))  if not grp_curr.empty else None,
        }
        results.append(record)

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

    # 6. Players + Value + Leagues + Fixtures + Referees
    print("\n[6/7] players.json, players_detail.json, value_patterns.json, referees.json...")
    leagues = build_leagues(df, teams)
    write_player_json(build_players(df_players), "players.json")
    write_player_json(build_players_detail(df_players), "players_detail.json")
    coverage = build_player_coverage_from_json(leagues) if df_players.empty else build_player_coverage(df_players, leagues)
    write_json(coverage, "player_coverage.json")
    write_json(build_data_status(coverage), "data_status.json")
    write_json(build_value_patterns(df), "value_patterns.json")
    write_json(build_referees(df, df_current), "referees.json")

    print("\n[7/7] leagues.json, fixtures.json...")
    write_json(leagues, "leagues.json")
    write_json(build_fixtures(df), "fixtures.json")

    print("\n" + "=" * 60)
    print("✓ BUILD COMPLETADO")
    print("=" * 60)
    print(f"Archivos en: {OUTPUT_DIR.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

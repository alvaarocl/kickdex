"""
build_data.py — Genera los JSON estáticos para el frontend de GitHub Pages.
Ejecutar localmente o via GitHub Actions (diariamente).

Salida: docs/data/*.json
"""

import json
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
from app.config import CURRENT_SEASON_LABEL, ROLLING_WINDOW_DEFAULT

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
    pairs = [(t1, t2) for i, t1 in enumerate(teams) for t2 in teams[i+1:]]
    print(f"    Calculando {len(pairs)} pares...")

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
                date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)
                rows.append({
                    "date": date_str,
                    "sh":   _safe(r.get("sh", 0)),
                    "sot":  _safe(r.get("sot", 0)),
                    "gls":  _safe(r.get("gls", 0)),
                    "ast":  _safe(r.get("ast", 0)),
                    "fls":  _safe(r.get("fls", 0)),
                    "crdy": _safe(r.get("crdy", 0)),
                })
            team_data[player] = rows
        result[str(team)] = team_data
    return result


def build_leagues(df, teams: list) -> dict:
    """Mapeo liga → equipos para el filtro de división en el frontend."""
    import pandas as pd
    from app.config import CURRENT_SEASON_START
    current = df[df["Date"] >= CURRENT_SEASON_START]
    result = {}
    for code, name in {"SP1": "La Liga", "SP2": "Segunda División"}.items():
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
    from app.config import CURRENT_SEASON_CODE, DATA_DIR

    recent = []
    upcoming = []
    leagues = {"SP1": "La Liga", "SP2": "Segunda División"}
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("BUILD DATA - Analista Pro  -> docs/data/")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Descargar/actualizar CSVs
    print("\n[1/6] Actualizando CSVs...")
    try:
        result = update_data(force_current=True)
        print(f"     {len(result['downloaded'])} descargados, {len(result['skipped'])} saltados")
    except Exception as e:
        print(f"  Warning: {e}")

    # 2. Cargar datos
    print("\n[2/6] Cargando datos...")
    invalidate_cache()
    df = load_matches()
    df_players = load_players()
    teams = get_team_list(df, recent_only=True)
    df_current = df[df["Date"] >= "2025-08-01"]
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

    # 6. Players + Value + Leagues + Fixtures
    print("\n[6/7] players.json, players_detail.json, value_patterns.json...")
    write_json(build_players(df_players), "players.json")
    write_json(build_players_detail(df_players), "players_detail.json")
    write_json(build_value_patterns(df), "value_patterns.json")

    print("\n[7/7] leagues.json, fixtures.json...")
    write_json(build_leagues(df, teams), "leagues.json")
    write_json(build_fixtures(df), "fixtures.json")

    print("\n" + "=" * 60)
    print("✓ BUILD COMPLETADO")
    print("=" * 60)
    print(f"Archivos en: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()

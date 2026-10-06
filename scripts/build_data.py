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
from app.data.assets import build_player_assets, build_team_assets
from app.data.health import build_data_health
from app.data.season_rosters import all_roster_teams, roster_for
from app.engine.metrics import (
    get_recent_form, get_h2h, get_h2h_summary, calculate_rolling_metrics,
    get_weighted_form, get_weighted_h2h_summary, get_weighted_referee_form,
)
from app.engine.probability import (
    calculate_probabilities,
    _HOME_ADVANTAGE, _LEAGUE_AVG_GOALS, _DIXON_COLES_RHO,
    _H2H_WEIGHT, _H2H_MIN_TOTAL, _OVER25_WEIGHTS, _BTTS_WEIGHTS,
)
from app.engine.edge import calculate_edge, edge_confidence, implied_probability
from app.engine.trends import build_trends_payload
from app.engine.smart_alerts import generate_alerts, AlertStrength
from app.engine.suspensions import build_suspensions_payload
from app.config import (
    CURRENT_SEASON_LABEL,
    CURRENT_SEASON_START,
    MIN_MATCHES_FOR_STATS,
    ROLLING_WINDOW_DEFAULT,
)

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


def _compute_hit_rates(df, team: str, venue: str) -> dict:
    """
    Calcula hit-rates de métricas de apuestas para un equipo y localía dados.

    Args:
        df: DataFrame completo de partidos (todas las temporadas).
        team: Nombre canónico del equipo.
        venue: 'home' o 'away'.

    Returns:
        Dict con claves l5/l10/l20/all; cada una contiene un sub-dict de
        métrica -> {hits: int, total: int, rate: float}.
        Si una ventana tiene menos partidos que su tamaño, `total` refleja
        los reales disponibles.
    """
    import pandas as pd
    import math as _math

    if venue == 'home':
        mask = df['HomeTeam'] == team
    else:
        mask = df['AwayTeam'] == team

    scored_mask = df['FTHG'].notna() & df['FTAG'].notna()
    matches = df[mask & scored_mask].sort_values('Date', ascending=False).copy()

    def _sf(val) -> float:
        try:
            f = float(val)
            return 0.0 if _math.isnan(f) or _math.isinf(f) else f
        except Exception:
            return 0.0

    metric_keys = [
        'goals_over_05', 'goals_over_15', 'goals_over_25', 'goals_over_35',
        'btts', 'clean_sheet', 'team_no_score', 'team_over_05', 'team_over_15',
        'corners_over_85', 'corners_over_95',
        'cards_over_35', 'cards_over_45',
        'fouls_over_205', 'fouls_over_245',
    ]

    def _window(subset) -> dict:
        total = len(subset)
        if total == 0:
            return {}
        counters = {k: 0 for k in metric_keys}
        for _, row in subset.iterrows():
            hg = _sf(row.get('FTHG', 0))
            ag = _sf(row.get('FTAG', 0))
            gf = hg if venue == 'home' else ag
            gc = ag if venue == 'home' else hg
            tg = hg + ag
            hc = _sf(row.get('HC', 0))
            ac = _sf(row.get('AC', 0))
            tc = hc + ac
            hy = _sf(row.get('HY', 0))
            ay = _sf(row.get('AY', 0))
            hr = _sf(row.get('HR', 0))
            ar = _sf(row.get('AR', 0))
            tk = hy + ay + hr + ar
            hf = _sf(row.get('HF', 0))
            af = _sf(row.get('AF', 0))
            tf = hf + af
            if tg > 0.5: counters['goals_over_05'] += 1
            if tg > 1.5: counters['goals_over_15'] += 1
            if tg > 2.5: counters['goals_over_25'] += 1
            if tg > 3.5: counters['goals_over_35'] += 1
            if gf > 0 and gc > 0: counters['btts'] += 1
            if gc == 0: counters['clean_sheet'] += 1
            if gf == 0: counters['team_no_score'] += 1
            if gf > 0.5: counters['team_over_05'] += 1
            if gf > 1.5: counters['team_over_15'] += 1
            if tc > 8.5: counters['corners_over_85'] += 1
            if tc > 9.5: counters['corners_over_95'] += 1
            if tk > 3.5: counters['cards_over_35'] += 1
            if tk > 4.5: counters['cards_over_45'] += 1
            if tf > 20.5: counters['fouls_over_205'] += 1
            if tf > 24.5: counters['fouls_over_245'] += 1
        return {
            m: {'hits': h, 'total': total, 'rate': round(h / total, 3)}
            for m, h in counters.items()
        }

    result = {}
    for key, n in [('l5', 5), ('l10', 10), ('l20', 20), ('all', None)]:
        subset = matches.head(n) if n is not None else matches
        result[key] = _window(subset)
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


def write_player_json(data, filename: str, current_teams: set | None = None):
    """Fusiona por equipo: los datos frescos mandan; de lo existente solo se
    conservan equipos que no vinieron en el scrape y siguen en la temporada.

    Antes, "menos equipos que el fichero anterior" descartaba TODO el scrape:
    el fichero viejo tenía 109 equipos (con 13 descendidos) y uno completo de
    las 5 ligas tiene 96, así que players.json se quedó congelado semanas.
    """
    existing = _read_existing_json(filename)
    existing = existing if isinstance(existing, dict) else {}
    if not isinstance(data, dict) or not data:
        if existing:
            print(f"  KEEP {filename}  (scrape vacío, existente: {len(existing)} equipos)")
            return
        write_json(data or {}, filename)
        return
    merged = dict(data)
    kept = [t for t in existing if t not in data and (current_teams is None or t in current_teams)]
    for team in kept:
        merged[team] = existing[team]
    dropped = len(existing) - len(kept) - len(set(existing) & set(data))
    print(f"  MERGE {filename}  (frescos: {len(data)}, conservados: {len(kept)}, retirados: {dropped})")
    write_json(merged, filename)


def current_season_teams(leagues: dict | None) -> set | None:
    teams = {str(t) for info in (leagues or {}).values() for t in (info.get("teams") or [])}
    return teams or None


def write_fixtures_json(data, filename: str = "fixtures.json"):
    """Persist fixtures and return the payload that is actually on disk."""
    existing = _read_existing_json(filename)
    existing_upcoming = len(existing.get("upcoming", [])) if isinstance(existing, dict) else 0
    existing_season = (existing.get("meta") or {}).get("season") if isinstance(existing, dict) else None
    new_upcoming = len(data.get("upcoming", [])) if isinstance(data, dict) else 0
    fd_status = (data.get("meta") or {}).get("fixture_download") if isinstance(data, dict) else {}
    fd_leagues = (fd_status or {}).get("leagues") or {}
    source_failed = bool((fd_status or {}).get("skipped")) or (
        bool(fd_leagues)
        and not any(info.get("ok") for info in fd_leagues.values() if isinstance(info, dict))
    )
    if (
        existing_upcoming > 0
        and existing_season == CURRENT_SEASON_LABEL
        and new_upcoming == 0
        and source_failed
    ):
        print(f"  KEEP {filename}  (FixtureDownload falló; preservados {existing_upcoming} próximos)")
        return existing
    write_json(data, filename)
    return data


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
    for league_code, league_info in leagues.items():
        expected = set(league_info.get("teams", []))
        expected_count = int(league_info.get("expected_teams") or len(expected))
        coverage["by_league"][league_code] = {
            "name": league_info.get("name", league_code),
            "teams_with_players": 0,
            "expected_teams": expected_count,
            "coverage_rate": 0.0 if expected_count else None,
            "missing_teams": sorted(expected),
            "unresolved_team_slots": max(0, expected_count - len(expected)),
            "player_rows": 0,
        }
    if "league" in df_players.columns:
        for code, grp in df_players.groupby("league"):
            league_code = str(code)
            league_info = leagues.get(league_code) or {}
            expected = set(league_info.get("teams", []))
            expected_count = int(league_info.get("expected_teams") or len(expected))
            covered = set(grp["team"].dropna().astype(str))
            matched = covered & expected
            coverage["by_league"][league_code] = {
                "name": league_info.get("name", league_code),
                "teams_with_players": len(matched),
                "expected_teams": expected_count,
                "coverage_rate": round(len(matched) / expected_count, 3) if expected_count else None,
                "missing_teams": sorted(expected - covered),
                "unresolved_team_slots": max(0, expected_count - len(expected)),
                "player_rows": int(grp["team"].isin(matched).sum()),
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
        expected_count = int(info.get("expected_teams") or len(expected))
        matched = expected & covered_teams
        coverage["by_league"][code] = {
            "name": info.get("name", code),
            "teams_with_players": len(matched),
            "expected_teams": expected_count,
            "coverage_rate": round(len(matched) / expected_count, 3) if expected_count else None,
            "missing_teams": sorted(expected - covered_teams),
            "unresolved_team_slots": max(0, expected_count - len(expected)),
            "player_rows": sum(len(players.get(team, [])) for team in matched),
        }
    return coverage


def _write_alerts_json(fixtures_payload: dict):
    """
    Genera docs/data/alerts.json a partir de smart_alerts.py.
    Itera sobre los próximos partidos de fixtures_payload y llama a
    generate_alerts() con los stats de team_stats.json y h2h.json
    (ya escritos en disco en los pasos anteriores del build).
    """
    team_stats_data = _read_existing_json("team_stats.json") or {}
    h2h_data = _read_existing_json("h2h.json") or {}

    upcoming = fixtures_payload.get("upcoming", [])
    matches_alerts: dict = {}

    for fixture in upcoming:
        home = fixture.get("home", "")
        away = fixture.get("away", "")
        league = fixture.get("league", "")
        date = fixture.get("date", "")
        if not home or not away:
            continue

        key = f"{league}|{date}|{home}|{away}"

        home_team_data = team_stats_data.get(home, {})
        away_team_data = team_stats_data.get(away, {})
        # Usar stats del venue correspondiente; fallback al otro venue si no existe.
        home_stats = home_team_data.get("home") or home_team_data.get("away")
        away_stats = away_team_data.get("away") or away_team_data.get("home")

        if not home_stats or not away_stats:
            continue

        # Inyectar el nombre para que smart_alerts escriba "Racing promedia..."
        # en vez de "Local promedia..." (las sub-claves home/away no lo llevan).
        home_stats = {**home_stats, "team": home}
        away_stats = {**away_stats, "team": away}

        # La clave en h2h.json es "{alphabetically_first}|{alphabetically_second}"
        h2h_key = "|".join(sorted([home, away]))
        h2h_entry = h2h_data.get(h2h_key)
        h2h_summary = h2h_entry.get("summary") if isinstance(h2h_entry, dict) else None

        n = max(int(home_stats.get("matches_analyzed") or 5), 1)
        try:
            alerts = generate_alerts(home_stats, away_stats, h2h_summary, n=n)
        except Exception as exc:
            print(f"  Warning alerts {key}: {exc}")
            continue

        if alerts:
            matches_alerts[key] = [
                {
                    "type": a.type.value,
                    "strength": a.strength.value,
                    "text": a.text,
                    "emoji": a.emoji,
                    "color": a.color,
                    "confidence": round(a.confidence, 3),
                    "source": a.source,
                }
                for a in alerts
            ]

    write_json(
        {
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "matches": matches_alerts,
        },
        "alerts.json",
    )


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


def build_model_config() -> dict:
    """
    Vuelca las constantes del modelo de probabilidad (app/engine/probability.py)
    a JSON para que docs/js/app.js las lea en vez de mantener su propia copia
    hardcodeada — evita que el Comparador (JS) y edges.json (Python) usen
    matemáticas distintas para el mismo partido.
    """
    return {
        "home_advantage": _HOME_ADVANTAGE,
        "league_avg_goals": _LEAGUE_AVG_GOALS,
        "dixon_coles_rho": _DIXON_COLES_RHO,
        "h2h_weight": _H2H_WEIGHT,
        "h2h_min_total": _H2H_MIN_TOTAL,
        "over25_weights": {
            "base_poisson": _OVER25_WEIGHTS[0],
            "home_rate": _OVER25_WEIGHTS[1],
            "away_rate": _OVER25_WEIGHTS[2],
            "h2h_rate": _OVER25_WEIGHTS[3],
        },
        "btts_weights": {
            "home_rate": _BTTS_WEIGHTS[0],
            "away_rate": _BTTS_WEIGHTS[1],
            "h2h_rate": _BTTS_WEIGHTS[2],
        },
    }


def build_team_stats(df, teams: list) -> dict:
    """Build stats for every roster team, weighting all-time history by recency."""
    result = {}
    for i, team in enumerate(teams):
        if i % 10 == 0:
            print(f'    {i}/{len(teams)} equipos...')
        home = get_weighted_form(df, team, venue='Home')
        away = get_weighted_form(df, team, venue='Away')
        if not home and not away:
            continue
        # Fracción de peso que viene de la temporada en curso, combinada de
        # ambos lados. Sustituye a la antigua distinción binaria
        # season/historical (que en la práctica siempre eran los mismos 5
        # partidos, con o sin filtrar por fecha de inicio de temporada).
        weight_current = (home or {}).get('current_season_weight_share', 0) * (home or {}).get('effective_matches', 0) \
            + (away or {}).get('current_season_weight_share', 0) * (away or {}).get('effective_matches', 0)
        weight_total = (home or {}).get('effective_matches', 0) + (away or {}).get('effective_matches', 0)
        current_share = (weight_current / weight_total) if weight_total else 0.0
        scope = 'season' if current_share >= 0.6 else 'mixed' if current_share > 0 else 'historical'
        result[team] = {
            'home': _serialize_form(home),
            'away': _serialize_form(away),
            'sample_scope': scope,
            'season_matches': (home or {}).get('current_season_matches', 0) + (away or {}).get('current_season_matches', 0),
            'historical_matches': (home or {}).get('matches_analyzed', 0) + (away or {}).get('matches_analyzed', 0),
            'hit_rates': {
                'home': _compute_hit_rates(df, team, 'home'),
                'away': _compute_hit_rates(df, team, 'away'),
            },
        }
    return result


def build_h2h(df, teams: list) -> dict:
    result = {}

    # Agrupar UNA vez por pareja (orden alfabético). Antes cada pareja filtraba
    # el frame completo (~92k partidos) dos veces → ~70% del tiempo del build.
    team_set = set(teams)
    base = df.dropna(subset=["HomeTeam", "AwayTeam"])
    base = base[base["HomeTeam"].isin(team_set) & base["AwayTeam"].isin(team_set)]
    lo = base["HomeTeam"].where(base["HomeTeam"] <= base["AwayTeam"], base["AwayTeam"])
    hi = base["AwayTeam"].where(base["HomeTeam"] <= base["AwayTeam"], base["HomeTeam"])
    groups = base.groupby([lo, hi], sort=False)
    print(f"    Calculando {groups.ngroups} pares reales (filtrado de {len(teams) * (len(teams)-1) // 2} posibles)...")

    for (t1, t2), pair_df in groups:
        if t1 == t2:
            continue
        summary = get_weighted_h2h_summary(pair_df, t1, t2)
        if not summary or summary.get("total", 0) < 1:
            continue

        h2h_df = get_h2h(pair_df, t1, t2)
        if h2h_df is None or h2h_df.empty:
            continue

        matches = []
        import pandas as pd
        for _, row in h2h_df.head(25).iterrows():
            hg = row.get("FTHG")
            ag = row.get("FTAG")
            m = {
                "date": row["Date"].strftime("%Y-%m-%d") if hasattr(row["Date"], "strftime") else str(row["Date"]),
                "result": row.get("Resultado", "?-?"),  # retrocompat — una versión más
                "home": str(row.get("HomeTeam", "")),
                "away": str(row.get("AwayTeam", "")),
                "home_score": int(float(hg)) if pd.notna(hg) else None,
                "away_score": int(float(ag)) if pd.notna(ag) else None,
            }
            # Liga/Div como campo league
            for col, key in [("Liga", "league"), ("Div", "league")]:
                if col in row.index and "league" not in m:
                    v = row[col]
                    try:
                        if pd.notna(v):
                            m[key] = str(v)
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
                # Ponderados por antigüedad (0.5 ** dias/HALF_LIFE_DAYS); "total"
                # y "wins1/draws/wins2" arriba siguen siendo conteos reales.
                "effective_total": _safe(summary.get("effective_total", summary["total"]), 1),
                "weighted_win_rate1": _safe(summary.get("weighted_win_rate1")),
                "weighted_draw_rate": _safe(summary.get("weighted_draw_rate")),
                "weighted_win_rate2": _safe(summary.get("weighted_win_rate2")),
            },
            "matches": matches,
        }
    return result


def build_players(df_players) -> dict:
    import pandas as pd
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
            # Partidos jugados (solo en scrapes que lo traen; las caches
            # antiguas no tienen la columna).
            if "mp" in pg.columns:
                mp = pd.to_numeric(last["mp"], errors="coerce").max()
                if pd.notna(mp):
                    players[-1]["mp"] = int(mp)
        players.sort(key=lambda x: (x["sh"] or 0), reverse=True)
        result[str(team)] = players
    return result


# ── Jugadores desde ESPN (partido a partido, 11 ligas) ─────────────────────

PLAYER_DETAIL_COLUMNS = ["date", "opp", "venue", "min", "gls", "ast", "sh", "sot", "fls", "fld", "crdy", "crdr", "starter"]
PLAYER_DETAIL_MATCHES = 15
# Secuencias (más reciente primero) que viajan en players.json para calcular
# en la web las ventanas 5/10/15 y frecuencias tipo "comete ≥2 faltas en n/N".
PLAYER_SEQ_FIELDS = {"fls": "fls", "fld": "fld", "crdy": "crdy", "min": "minutes"}
PLAYER_SEQ_MATCHES = 15


def _espn_sync_time() -> str | None:
    from app.config import DATA_DIR
    try:
        return json.loads((Path(DATA_DIR) / "espn_sync.json").read_text(encoding="utf-8")).get("updated_at")
    except (OSError, ValueError):
        return None


def load_espn_player_matches():
    """DATOS/espn_player_matches.csv (scripts/update_espn_data.py), solo temporada actual."""
    import pandas as pd
    from app.config import CURRENT_SEASON_START, DATA_DIR
    path = Path(DATA_DIR) / "espn_player_matches.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False, dtype={"event_id": str, "player_id": str})
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[df["date"] >= pd.Timestamp(CURRENT_SEASON_START)]
    df = df.drop_duplicates(subset=["event_id", "player_id"], keep="last")
    for col in ["minutes", "gls", "ast", "sh", "sot", "fls", "fld", "crdy", "crdr", "og", "starter"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def build_players_from_matches(df) -> dict:
    """players.json: por equipo, una fila por jugador con medias por partido
    jugado (contrato previo: gls, ast, sh, sot, min, fls, crdy) + partidos,
    titularidades, minutos y totales. Un jugador traspasado aparece en cada
    equipo con lo que hizo en él."""
    if df is None or df.empty:
        return {}
    result = {}
    for team, grp in df.groupby("team"):
        players = []
        for pid, pg in grp.groupby("player_id"):
            mp = int(len(pg))
            recent = pg.sort_values("date", ascending=False).head(PLAYER_SEQ_MATCHES)
            tot = {c: int(pg[c].sum()) for c in ["gls", "ast", "sh", "sot", "fls", "fld", "crdy", "crdr"]}
            minutes = int(pg["minutes"].sum())
            pos = pg["position"].dropna().astype(str)
            players.append({
                "player": str(pg.sort_values("date")["player"].iloc[-1]),
                "player_id": str(pid),
                "pos": pos.mode().iloc[0] if not pos.empty else "",
                "mp": mp,
                "starts": int(pg["starter"].sum()),
                "min_total": minutes,
                "last_match": pg["date"].max().strftime("%Y-%m-%d"),
                # medias por partido jugado (mismo contrato que antes)
                "min": _safe(minutes / mp),
                "gls": _safe(tot["gls"] / mp), "ast": _safe(tot["ast"] / mp),
                "sh": _safe(tot["sh"] / mp), "sot": _safe(tot["sot"] / mp),
                "fls": _safe(tot["fls"] / mp), "fld": _safe(tot["fld"] / mp), "crdy": _safe(tot["crdy"] / mp),
                "crdr": _safe(tot["crdr"] / mp),
                # totales de temporada
                "gls_tot": tot["gls"], "ast_tot": tot["ast"], "sh_tot": tot["sh"], "sot_tot": tot["sot"],
                "fls_tot": tot["fls"], "fld_tot": tot["fld"], "crdy_tot": tot["crdy"], "crdr_tot": tot["crdr"],
                "seq": {k: [int(v) for v in recent[col]] for k, col in PLAYER_SEQ_FIELDS.items()},
            })
        players.sort(key=lambda x: (-(x["min_total"] or 0), x["player"]))
        result[str(team)] = players
    return result


def build_players_detail_from_matches(df) -> dict:
    """players_detail.json compacto: {columns, teams: {equipo: {jugador: [[...], ...]}}}
    con los últimos PLAYER_DETAIL_MATCHES partidos (más reciente primero). La
    web lo expande a objetos (expandPlayersDetail en app.js / player.js)."""
    if df is None or df.empty:
        return {"columns": PLAYER_DETAIL_COLUMNS, "teams": {}}
    teams: dict = {}
    for (team, pid), pg in df.sort_values("date", ascending=False).groupby(["team", "player_id"], sort=False):
        name = str(pg["player"].iloc[0])
        rows = []
        for _, r in pg.head(PLAYER_DETAIL_MATCHES).iterrows():
            rows.append([
                r["date"].strftime("%Y-%m-%d"), str(r.get("opponent") or ""), str(r.get("venue") or ""),
                int(r["minutes"]), int(r["gls"]), int(r["ast"]), int(r["sh"]), int(r["sot"]),
                int(r["fls"]), int(r.get("fld", 0) or 0), int(r["crdy"]), int(r["crdr"]), int(r["starter"]),
            ])
        teams.setdefault(str(team), {})[name] = rows
    return {"columns": PLAYER_DETAIL_COLUMNS, "teams": teams}


def add_player_percentiles(players_payload: dict, leagues: dict) -> dict:
    """Añade *_pct (percentil 0-100 vs la liga del jugador) a players.json.

    Da contexto comparativo: "gls_pct: 92" = mete más goles/p que el 92% de los
    jugadores de su liga. Se calcula por liga, no global, para que comparar un
    delantero de 2ª con uno de 1ª no distorsione. Conecta la lógica de
    calculate_player_percentiles() de app/engine/metrics.py, que estaba muerta.
    """
    metrics = ("gls", "ast", "sh", "sot", "fls", "fld", "crdy")
    team_to_league = {}
    for code, info in (leagues or {}).items():
        for team in info.get("teams", []):
            team_to_league[str(team)] = code

    # Agrupar jugadores por liga
    by_league: dict[str, list[dict]] = {}
    for team, players in players_payload.items():
        code = team_to_league.get(str(team), "_unknown")
        by_league.setdefault(code, []).extend(players)

    for code, players in by_league.items():
        # Pool de comparación: solo jugadores con minutos reales, para que los
        # suplentes que juegan 5' no aplasten a todos al percentil 100.
        pool = [p for p in players if isinstance(p.get("min"), (int, float)) and p["min"] >= 30
                and (p.get("mp") is None or p["mp"] >= 3)]
        if len(pool) < 8:
            pool = players
        for m in metrics:
            vals = sorted(p[m] for p in pool if isinstance(p.get(m), (int, float)))
            n = len(vals)
            if n < 5:
                continue
            for p in players:
                v = p.get(m)
                if not isinstance(v, (int, float)):
                    continue
                # percentil = fracción del pool con valor <= v
                lo = sum(1 for x in vals if x <= v)
                p[f"{m}_pct"] = max(0, min(100, round(lo / n * 100)))
    return players_payload


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
                is_aggregate = not date_str or date_str == "NaT"
                rows.append({
                    "date": None if is_aggregate else date_str,
                    "scope": "season_aggregate" if is_aggregate else "match",
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
    """Build league rosters independently from the matches already played."""
    import pandas as pd
    from app.config import CURRENT_SEASON_LABEL, CURRENT_SEASON_START, LEAGUES, LEAGUE_TEAM_COUNTS
    current = (
        df[df["Date"] >= CURRENT_SEASON_START]
        if df is not None and not df.empty and "Date" in df.columns
        else pd.DataFrame()
    )
    result = {}
    for code, name in LEAGUES.items():
        league_df = current[current["Div"] == code] if "Div" in current.columns else pd.DataFrame()
        observed_teams = sorted(
            set(league_df["HomeTeam"].dropna()) | set(league_df["AwayTeam"].dropna())
        ) if not league_df.empty else []
        roster = roster_for(code)
        league_teams = sorted(roster["teams"]) if roster else observed_teams
        expected = LEAGUE_TEAM_COUNTS.get(code)
        result[code] = {
            "name": name,
            "teams": league_teams,
            "season": CURRENT_SEASON_LABEL,
            "expected_teams": expected,
            "roster_status": "complete" if expected and len(league_teams) == expected else "partial",
            "observed_team_count": len(set(observed_teams) & set(league_teams)),
            "unmatched_observed_teams": sorted(set(observed_teams) - set(league_teams)),
            "roster_source": roster.get("source") if roster else "football-data.co.uk",
            "roster_verified_at": roster.get("verified_at") if roster else None,
        }
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


def _merge_espn_upcoming(upcoming: list[dict], calendar: list[dict], fd_status: dict, now) -> tuple[list, list]:
    """Próximos partidos de ESPN (DATOS/espn_upcoming.json):
    - ligas sin FixtureDownload (segundas divisiones): se añaden; antes
      "Próximos" salía vacío para Segunda, Serie B, 2. Bundesliga y Ligue 2.
    - resto: solo rellenan la hora cuando FixtureDownload la deja vacía."""
    import pandas as pd
    from app.config import DATA_DIR
    try:
        items = json.loads((Path(DATA_DIR) / "espn_upcoming.json").read_text(encoding="utf-8")).get("items", [])
    except (OSError, ValueError):
        return upcoming, calendar
    covered = {code for code, info in ((fd_status or {}).get("leagues") or {}).items() if (info or {}).get("ok")}
    today = pd.Timestamp(now).strftime("%Y-%m-%d")
    items = [i for i in items if str(i.get("date", "")) >= today]
    # FixtureDownload pone los partidos "hora por confirmar" en el viernes de la
    # jornada; ESPN trae el día y la hora reales → se cruza por equipos (±4 días).
    espn_by_teams: dict = {}
    for i in items:
        espn_by_teams.setdefault((i.get("league"), i.get("home"), i.get("away")), []).append(i)

    def _espn_for(f):
        cands = espn_by_teams.get((f.get("league"), f.get("home"), f.get("away")), [])
        try:
            fd = pd.Timestamp(f.get("date"))
        except (TypeError, ValueError):
            return None
        near = [c for c in cands if abs((pd.Timestamp(c["date"]) - fd).days) <= 4]
        return near[0] if near else None

    for bucket in (upcoming, calendar):
        for f in bucket:
            if f.get("time") or f.get("status") == "finished":
                continue
            match = _espn_for(f)
            if match and match.get("time"):
                f["date"], f["time"] = match["date"], match["time"]

    extra = [i for i in items if i.get("league") not in covered]
    upcoming = _merge_fixture_lists(primary=upcoming, secondary=extra)
    calendar = _merge_fixture_lists(primary=calendar, secondary=extra)
    return upcoming, calendar


CUP_COMPETITIONS = {"CL": {"name": "Champions League", "short": "UCL", "type": "uefa"}}


def build_competitions() -> dict:
    """competitions.json: competiciones europeas (fuera de leagues.json para que
    cada club siga perteneciendo a su liga doméstica)."""
    from app.config import DATA_DIR
    try:
        standings = json.loads((Path(DATA_DIR) / "espn_standings.json").read_text(encoding="utf-8")).get("leagues", {})
    except (OSError, ValueError):
        standings = {}
    try:
        team_map = json.loads((OUTPUT_DIR / "espn_teams.json").read_text(encoding="utf-8")).get("leagues", {})
    except (OSError, ValueError):
        team_map = {}
    out = {}
    for code, meta in CUP_COMPETITIONS.items():
        table = (standings.get(code) or {}).get("table") or []
        teams = [r["team"] for r in table] or sorted(set((team_map.get(code) or {}).values()))
        if not teams:
            continue
        out[code] = {**meta, "teams": teams, "logos": {r["team"]: r.get("logo") for r in table if r.get("logo")}}
    return out


def _load_espn_results() -> list[dict]:
    from app.config import DATA_DIR
    try:
        return list(json.loads((Path(DATA_DIR) / "espn_results.json").read_text(encoding="utf-8")).get("items", {}).values())
    except (OSError, ValueError):
        return []


def build_fixtures(df, leagues_json: dict | None = None) -> dict:
    """
    Genera partidos recientes (últimos 7 días) y próximos (NaN FTHG).
    Fuente: CSVs de la temporada actual descargados frescos.
    """
    import pandas as pd
    from datetime import datetime, timedelta
    from pathlib import Path
    from app.config import CURRENT_SEASON_CODE, DATA_DIR, LEAGUES
    from app.data.loader import normalize_team_name

    recent = []
    upcoming = []
    calendar = []
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
                "home": normalize_team_name(str(row.get("HomeTeam", ""))),
                "away": normalize_team_name(str(row.get("AwayTeam", ""))),
                # Árbitro: football-data.co.uk no asigna árbitro a partidos futuros,
                # solo a partidos ya disputados. La asignación previa es imposible
                # a partir de estas fuentes. Fase 0.5: campo estructural en null.
                "referee": None,
                "referee_yellows_per_match": None,
            }
            if has_score:
                item["home_score"] = int(row["FTHG"])
                item["away_score"] = int(row["FTAG"])
                item["status"] = "finished"
                if date >= cutoff:
                    recent.append(item)
            else:
                item["status"] = "scheduled" if date >= now else "postponed"
                if date >= now - pd.Timedelta(days=1):
                    upcoming.append(item)
            calendar.append(item)

    fd_recent = []
    fd_upcoming = []
    fd_calendar = []
    fd_status = {}
    skip_fixture_downloads = os.getenv("KICKDEX_SKIP_FIXTURE_DOWNLOADS") == "1"
    if leagues_json and skip_fixture_downloads:
        fd_status = {
            "source": "fixturedownload",
            "ok": False,
            "skipped": True,
            "reason": "KICKDEX_SKIP_FIXTURE_DOWNLOADS=1",
            "leagues": {},
        }
        print("  SKIP FixtureDownload calendar (KICKDEX_SKIP_FIXTURE_DOWNLOADS=1)")
    elif leagues_json:
        try:
            league_teams = {code: info.get("teams", []) for code, info in leagues_json.items()}
            fd_recent, fd_upcoming, fd_calendar, fd_status = fetch_fixture_download_calendar(
                leagues, league_teams
            )
            print(f"  OK FixtureDownload calendar ({len(fd_upcoming)} futuros, {len(fd_recent)} recientes)")
        except Exception as exc:
            fd_status = {"source": "fixturedownload", "ok": False, "error": str(exc)}
            print(f"  Warning FixtureDownload calendar: {exc}")

    recent = _merge_fixture_lists(primary=recent, secondary=fd_recent)
    upcoming = _merge_fixture_lists(primary=fd_upcoming, secondary=upcoming)
    calendar = _merge_fixture_lists(primary=calendar, secondary=fd_calendar)
    upcoming, calendar = _merge_espn_upcoming(upcoming, calendar, fd_status, now)
    # Resultados de competiciones europeas (no hay CSV de football-data).
    cup_results = [r for r in _load_espn_results() if r.get("league") in CUP_COMPETITIONS]
    if cup_results:
        calendar = _merge_fixture_lists(primary=cup_results, secondary=calendar)
        recent = _merge_fixture_lists(primary=[r for r in cup_results if pd.Timestamp(r["date"]) >= cutoff],
                                      secondary=recent)

    # Forma uniforme: FixtureDownload no trae árbitro; football-data.co.uk solo
    # lo asigna a partidos ya disputados. Fase 0.5: campos estructurales en null
    # en todo lo que no lo tenga (asignación previa imposible con estas fuentes).
    # Árbitro asignado cuando ESPN ya lo publica (scripts/update_espn_data.py).
    assigned = {}
    try:
        payload = json.loads((Path(DATA_DIR) / "referee_assignments.json").read_text(encoding="utf-8"))
        assigned = {(a["league"], a["date"], a["home"], a["away"]): a["referee"] for a in payload.get("items", [])}
    except (OSError, ValueError, KeyError):
        pass
    for _bucket in (recent, upcoming, calendar):
        for _item in _bucket:
            ref = assigned.get((_item.get("league"), _item.get("date"), _item.get("home"), _item.get("away")))
            if ref:
                _item["referee"] = ref
            _item.setdefault("referee", None)
            _item.setdefault("referee_yellows_per_match", None)

    recent.sort(key=lambda x: (x["date"], x.get("time", "")), reverse=True)
    upcoming.sort(key=lambda x: (x["date"], x.get("time", ""), x.get("league", "")))
    calendar.sort(key=lambda x: (x["date"], x.get("time", ""), x.get("league", "")))
    return {
        "recent": recent[:80],
        "upcoming": upcoming[:300],  # 11 ligas con calendario ≈ 10-14 días
        "calendar": calendar,
        "meta": {
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "season": CURRENT_SEASON_LABEL,
            "sources": ["football-data.co.uk", "FixtureDownload"],
            "calendar_records": len(calendar),
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
        # as_of=date: el decaimiento se calcula respecto a la fecha del propio
        # fixture (no "hoy"), y el filtro Date < date de arriba ya evita fugas.
        home_form = get_weighted_form(history, home, venue="Home", as_of=date)
        away_form = get_weighted_form(history, away, venue="Away", as_of=date)
        if not home_form or not away_form:
            continue
        if home_form.get("effective_matches", 0) < 3 or away_form.get("effective_matches", 0) < 3:
            continue

        h2h_summary = get_weighted_h2h_summary(history, home, away, as_of=date)
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


def add_odds_based_edges(edges_payload: dict, df, fixtures_payload: dict) -> dict:
    """Fusiona en edges.json el edge de partidos FUTUROS usando odds.json.

    build_edges() solo produce edge retrospectivo (cuotas de cierre Bet365 que
    llegan tras el partido). Aquí, si hay odds.json con enabled=true, se calcula
    para cada fixture próximo: prob del modelo (forma ponderada sobre todo el
    historial, as_of = fecha del fixture) − prob implícita de la mejor cuota.

    Sin odds.json / enabled=false: no-op, edges.json queda igual (solo settled).
    """
    import pandas as pd
    from app.config import LEAGUES

    odds_data = _read_existing_json("odds.json") or {}
    if not odds_data.get("enabled") or not odds_data.get("matches"):
        return edges_payload

    upcoming_fixtures = (fixtures_payload or {}).get("upcoming", [])
    if df is None or df.empty or not upcoming_fixtures:
        return edges_payload

    data = df.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date", "HomeTeam", "AwayTeam"])

    market_labels = {"home": "Home", "draw": "Draw", "away": "Away"}
    new_items = []
    seen = 0
    for fx in upcoming_fixtures:
        league = fx.get("league", "")
        date = fx.get("date", "")
        home = fx.get("home", "")
        away = fx.get("away", "")
        if not (league and date and home and away):
            continue
        entry = odds_data["matches"].get(f"{league}|{date}|{home}|{away}")
        if not entry:
            continue
        h2h = (entry.get("markets") or {}).get("h2h") or {}
        if not h2h:
            continue

        as_of = pd.Timestamp(date)
        league_mask = data["Div"].eq(league) if "Div" in data.columns else True
        history = data[league_mask & (data["Date"] < as_of)]
        home_form = get_weighted_form(history, home, venue="Home", as_of=as_of)
        away_form = get_weighted_form(history, away, venue="Away", as_of=as_of)
        if not home_form or not away_form:
            continue
        if home_form.get("effective_matches", 0) < 3 or away_form.get("effective_matches", 0) < 3:
            continue
        h2h_summary = get_weighted_h2h_summary(history, home, away, as_of=as_of)
        probs = calculate_probabilities(home_form, away_form, h2h_summary).as_dict()
        seen += 1

        for market, odd in h2h.items():
            model_p = probs.get(market)
            edge_pct = calculate_edge(model_p, odd)
            if edge_pct is None or edge_pct < 1 or edge_pct > 25:
                continue
            if not 0.08 <= float(model_p) <= 0.80:
                continue
            selection = home if market == "home" else away if market == "away" else "Empate"
            new_items.append({
                "id": f"{league}-{date.replace('-', '')}-{home}-{away}-{market}".replace(" ", "_"),
                "date": date,
                "time": fx.get("time", ""),
                "league": league,
                "league_name": LEAGUES.get(league, league),
                "home": home,
                "away": away,
                "market": market,
                "market_label": market_labels.get(market, market),
                "selection": selection,
                "odds": round(float(odd), 2),
                "probability": _safe(model_p, decimals=4),
                "implied_probability": _safe(implied_probability(odd), decimals=4),
                "edge_pct": round(edge_pct, 2),
                "status": "upcoming",
                "confidence": edge_confidence(edge_pct, home_form.get("matches_analyzed", 0), away_form.get("matches_analyzed", 0)),
                "result": {"home_score": None, "away_score": None, "outcome": None, "hit": None},
                "model": {
                    "home_matches": int(home_form.get("matches_analyzed", 0)),
                    "away_matches": int(away_form.get("matches_analyzed", 0)),
                },
                "odds_source": "the-odds-api.com",
                "bookmaker_count": entry.get("bookmaker_count"),
            })

    if not new_items:
        return edges_payload

    merged = new_items + list(edges_payload.get("items", []))
    merged.sort(key=lambda x: (1 if x["status"] == "upcoming" else 0, x["date"], x["edge_pct"]), reverse=True)
    stats = dict(edges_payload.get("stats", {}))
    stats["upcoming_edges"] = len(new_items)
    stats["positive_edges"] = stats.get("positive_edges", 0) + len(new_items)
    stats["upcoming_evaluated"] = seen
    edges_payload["items"] = merged[:300]
    edges_payload["stats"] = stats
    edges_payload["status"] = "live_edges"
    edges_payload["source"] = "the-odds-api.com (futuros) + football-data.co.uk Bet365 (histórico)"
    edges_payload["top"] = max(new_items, key=lambda x: x["edge_pct"])
    edges_payload["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return edges_payload


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
        # Fuentes sin faltas/penaltis (World Soccer Data): NaN, no 0 — así las
        # medias salen None ("sin dato") en vez de un falso 0.00.
        # Celda vacía = sin dato (ESPN no da penaltis) → NaN, no 0.
        out["_F"] = pd.to_numeric(out["fouls"], errors="coerce") if "fouls" in out.columns else float("nan")
        out["_P"] = pd.to_numeric(out["penalties"], errors="coerce") if "penalties" in out.columns else float("nan")
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


def _load_wsd_referee_matches():
    """Partidos por árbitro de World Soccer Data (todas las ligas, varias
    temporadas) — ver scripts/update_worldsoccerdata_referee_data.py."""
    import pandas as pd
    from app.config import DATA_DIR
    path = Path(DATA_DIR) / "referees_wsd_matches.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        raw = pd.read_csv(path, low_memory=False)
    except Exception as e:
        print(f"  Warning: could not read {path}: {e}")
        return pd.DataFrame()
    # World Soccer Data escribe "0 0" cuando no tiene las tarjetas de un partido
    # (11% de sus filas frente al ~3% real; donde coincide con ESPN, ESPN da
    # 2-4 amarillas). Se descartan: mejor sin dato que una media hundida.
    if {"yellow_cards", "red_cards"} <= set(raw.columns):
        y = pd.to_numeric(raw["yellow_cards"], errors="coerce").fillna(0)
        r = pd.to_numeric(raw["red_cards"], errors="coerce").fillna(0)
        raw = raw[(y + r) > 0]
    return _normalise_referee_frame(raw, "worldsoccerdata")


def _load_referee_season_aggregates(max_rounds: dict | None = None):
    """Agregados de temporada (World Soccer Data). Se descartan los que no
    pueden ser de esta temporada: scrapeados antes de su inicio o con más
    partidos que jornadas disputadas en la liga (bug 2026-10: salían 19-22 PJ
    "esta temporada" que eran de la temporada anterior)."""
    import pandas as pd
    from app.config import CURRENT_SEASON_START, DATA_DIR
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
        updated = str(row.get("updated_at") or "")[:10]
        if updated and updated < CURRENT_SEASON_START:
            continue
        if max_rounds and league in max_rounds and matches > max_rounds[league]:
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


def load_manual_suspension_rows(path: Path | None = None) -> list[dict]:
    import csv

    manual_path = path or (ROOT / "DATOS" / "suspensions_manual.csv")
    if not manual_path.exists():
        return []
    with manual_path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh) if any((value or "").strip() for value in row.values())]


def load_suspension_source_catalog(path: Path | None = None) -> list[dict]:
    source_path = path or (ROOT / "DATOS" / "suspensions_sources.json")
    if not source_path.exists():
        return []
    try:
        return json.loads(source_path.read_text(encoding="utf-8")).get("sources", [])
    except Exception:
        return []


def _referee_key(name: str) -> str:
    """
    Normaliza un nombre de árbitro para cruzar fuentes con formato distinto:
    football-data.co.uk usa iniciales ("A Taylor"), worldsoccerdata usa
    nombre completo ("Anthony Taylor") — sin esto nunca coinciden y el mismo
    árbitro humano aparece como dos registros separados (uno con historial,
    otro con la temporada actual, nunca los dos a la vez).

    Clave = apellido + inicial del nombre ("A Taylor" y "Anthony Taylor" ->
    "taylor_a"). Colisiones reales de apellido+inicial son raras pero
    posibles; para esos casos añadir una entrada a REFEREE_ALIASES en
    app/config.py.
    """
    import re
    import unicodedata
    from app.config import REFEREE_ALIASES

    text = unicodedata.normalize("NFKD", str(name or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).strip().lower()
    text = re.sub(r"[^a-z\s]", "", text)
    if text in REFEREE_ALIASES:
        return REFEREE_ALIASES[text]
    parts = [p for p in text.split() if p]
    if not parts:
        return ""
    last = parts[-1]
    first_initial = parts[0][0] if len(parts) > 1 else ""
    return f"{last}_{first_initial}" if first_initial else last


def _ref_stats(grp):
    """Media plana sin ponderar — se mantiene solo para el CSV incremental de
    API-Football sin fecha fiable por partido; el camino normal usa
    get_weighted_referee_form()."""
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


REFEREE_RECENT_MATCHES = 10
# Un árbitro sin partidos en este plazo se marca como inactivo (retirado,
# ascendido/descendido de categoría...). La UI lo oculta por defecto.
REFEREE_ACTIVE_DAYS = 450


def _referee_match_log(grp, limit: int = REFEREE_RECENT_MATCHES) -> list:
    """Últimos partidos pitados (más reciente primero) para la ficha del árbitro.
    Solo existe en fuentes partido a partido (football-data.co.uk, API-Football)."""
    import pandas as pd
    if grp is None or grp.empty or "Date" not in grp.columns:
        return []
    rows = grp.dropna(subset=["Date"]).sort_values("Date", ascending=False).head(limit)
    from app.data.loader import normalize_team_name

    def _team(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip()
        return normalize_team_name(text) if text else None

    def _int(value):
        n = pd.to_numeric(value, errors="coerce")
        return None if pd.isna(n) else int(n)

    def _first(r, *cols):
        # football-data.co.uk (HomeTeam/FTHG) e incremental API-Football
        # (home/home_score) pueden convivir en el mismo grupo tras el concat.
        for col in cols:
            value = r.get(col)
            if value is not None and not (isinstance(value, float) and pd.isna(value)):
                return value
        return None

    has_fouls = "HF" in grp.columns or "fouls" in grp.columns
    log = []
    for _, r in rows.iterrows():
        log.append({
            "date": r["Date"].strftime("%Y-%m-%d"),
            "home": _team(_first(r, "HomeTeam", "home")),
            "away": _team(_first(r, "AwayTeam", "away")),
            "home_score": _int(_first(r, "FTHG", "home_score")),
            "away_score": _int(_first(r, "FTAG", "away_score")),
            "yellows": _int(r.get("_Y")),
            "reds": _int(r.get("_R")),
            "fouls": _int(r.get("_F")) if has_fouls else None,
        })
    return log


def _referee_is_active(last_match, today=None) -> bool:
    import pandas as pd
    if not last_match:
        return False
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.now("UTC").tz_localize(None)
    return (today - pd.Timestamp(last_match)).days <= REFEREE_ACTIVE_DAYS


def _unified_referee_keys(names_frame) -> dict:
    """(liga, nombre) -> clave común. Además de "M Oliver" ~ "Michael Oliver"
    (apellido + inicial), une nombres españoles con apellidos compuestos:
    "Ortiz Arias" ⊂ "Miguel Angel Ortiz Arias" en la misma liga."""
    import re
    import unicodedata

    def tokens(name):
        text = unicodedata.normalize("NFKD", str(name or ""))
        text = "".join(c for c in text if not unicodedata.combining(c)).lower()
        return [t for t in re.sub(r"[^a-z\s]", " ", text).split() if t]

    out = {}
    if names_frame is None or names_frame.empty:
        return out
    for div, grp in names_frame.dropna().drop_duplicates().groupby("Div"):
        names = sorted(set(grp["Referee"].astype(str)), key=lambda n: -len(tokens(n)))
        for name in names:
            toks = tokens(name)
            target = name
            if len(toks) >= 2 and all(len(t) > 1 for t in toks):
                for longer in names:
                    lt = tokens(longer)
                    if len(lt) > len(toks) and lt[-len(toks):] == toks:
                        target = longer
                        break
            out[(div, name)] = _referee_key(target)
    return out


def _dedupe_referee_matches(frame):
    import pandas as pd
    if frame is None or frame.empty or "Date" not in frame.columns:
        return frame
    keyed = frame.assign(_day=pd.to_datetime(frame["Date"], errors="coerce").dt.normalize())
    return keyed.drop_duplicates(subset=["Div", "_key", "_day"], keep="first").drop(columns="_day")


def _league_rounds_played(df_current) -> dict:
    """Máximo de partidos jugados por un equipo esta temporada, por liga
    (tope de partidos que puede haber pitado un árbitro en esa liga)."""
    if df_current is None or df_current.empty or not {"Div", "HomeTeam", "AwayTeam"} <= set(df_current.columns):
        return {}
    played = df_current.dropna(subset=["FTHG"]) if "FTHG" in df_current.columns else df_current
    out = {}
    for div, grp in played.groupby("Div"):
        counts = grp["HomeTeam"].value_counts().add(grp["AwayTeam"].value_counts(), fill_value=0)
        if len(counts):
            # margen: la fuente del calendario puede ir 1-2 jornadas por detrás
            out[str(div)] = int(counts.max()) + 2
    return out


def build_referees(df, df_current=None) -> list:
    import pandas as pd
    if "Referee" not in df.columns or "Div" not in df.columns:
        return []
    rdf = _normalise_referee_frame(df, "football-data")
    wsd = _load_wsd_referee_matches()
    sources = [f for f in (_load_incremental_referees(), wsd) if not f.empty]
    incremental = pd.concat(sources, ignore_index=True) if sources else pd.DataFrame()
    season_aggregates = _load_referee_season_aggregates(_league_rounds_played(df_current))
    if not incremental.empty:
        rdf = pd.concat([rdf, incremental], ignore_index=True)
    if rdf.empty:
        # Sin partido a partido: aún pueden existir agregados de temporada.
        rdf = pd.DataFrame(columns=["Date", "Div", "Referee", "_Y", "_R", "_F", "_P", "_source"])

    if df_current is not None and not df_current.empty and "Referee" in df_current.columns:
        rdf_curr = _normalise_referee_frame(df_current, "football-data")
    else:
        rdf_curr = pd.DataFrame(columns=rdf.columns)
    if not incremental.empty and "Date" in incremental.columns:
        from app.config import CURRENT_SEASON_START
        inc_curr = incremental[incremental["Date"] >= pd.Timestamp(CURRENT_SEASON_START)].copy()
        rdf_curr = pd.concat([rdf_curr, inc_curr], ignore_index=True)

    key_map = _unified_referee_keys(pd.concat(
        [f[["Div", "Referee"]] for f in (rdf, rdf_curr) if not f.empty and "Referee" in f.columns]
        + [pd.DataFrame([{"Div": d, "Referee": n} for d, n in season_aggregates])],
        ignore_index=True,
    ))
    rdf["_key"] = [key_map.get((d, n), _referee_key(n)) for d, n in zip(rdf["Div"], rdf["Referee"])]
    if not rdf_curr.empty:
        rdf_curr["_key"] = [key_map.get((d, n), _referee_key(n)) for d, n in zip(rdf_curr["Div"], rdf_curr["Referee"])]
    # Un mismo partido puede venir de varias fuentes (football-data + World
    # Soccer Data en Premier/Championship): se queda la primera (football-data,
    # que trae faltas).
    rdf = _dedupe_referee_matches(rdf)
    rdf_curr = _dedupe_referee_matches(rdf_curr)

    # Las claves de los agregados de temporada (worldsoccerdata) se
    # normalizan igual, para que "Anthony Taylor" cruce con "A Taylor".
    season_aggregates_by_key = {
        (div, key_map.get((div, name), _referee_key(name))): stats for (div, name), stats in season_aggregates.items()
    }

    results = []
    for (div, key), grp in rdf.groupby(["Div", "_key"], sort=False):
        if not key:
            continue
        overall = get_weighted_referee_form(grp, min_matches=1)  # la UI marca las muestras cortas
        if overall is None:
            continue
        overall["source"] = "api-football" if (grp.get("_source") == "api-football").any() else "football-data"
        # Nombre a mostrar: el más largo/completo de los que aparecen para
        # esta clave (normalmente el de football-data, con iniciales, pierde
        # frente al nombre completo si ambas fuentes cruzan).
        display_name = max(grp["Referee"].unique(), key=len)

        grp_curr = rdf_curr[(rdf_curr["Div"] == div) & (rdf_curr["_key"] == key)] if not rdf_curr.empty else pd.DataFrame()
        # El agregado de temporada de worldsoccerdata puede estar desfasado
        # (se ha visto con fecha de scrape anterior al inicio de temporada,
        # es decir con datos de la temporada previa mal etiquetados como
        # "actual"). En cuanto exista partido a partido real de la temporada
        # actual (aunque sean pocos partidos) confiamos solo en esa fuente,
        # incluso si es "sin datos aun" (None) — mejor honesto que hinchado
        # con un numero que no corresponde a este arbitro esta temporada.
        if grp_curr.empty:
            season_stats = season_aggregates_by_key.get((div, key))
        else:
            season_stats = get_weighted_referee_form(grp_curr, min_matches=1)  # la UI marca <5 como muestra corta

        record = {
            "name":    display_name,
            "league":  div,
            # top-level legacy fields (used by old frontend code)
            "matches":           overall["matches"],
            "yellows_per_match": overall["yellows_per_match"],
            "reds_per_match":    overall["reds_per_match"],
            "fouls_per_match":   overall["fouls_per_match"],
            "penalties_per_match": overall.get("penalties_per_match"),
            "last_match":        overall.get("last_match"),
            "source":            overall.get("source"),
            # windowed blocks — todos ponderados por antigüedad (más peso a
            # lo reciente), no una media plana sobre los últimos N.
            "overall":        overall,
            "last10":         get_weighted_referee_form(grp, max_matches=10, min_matches=3),
            "last5":          get_weighted_referee_form(grp, max_matches=5, min_matches=3),
            "season":         season_stats,
            "season_last10":  get_weighted_referee_form(grp_curr, max_matches=10, min_matches=3) if not grp_curr.empty else None,
            "season_last5":   get_weighted_referee_form(grp_curr, max_matches=5, min_matches=3) if not grp_curr.empty else None,
            # `overall.matches` está topado por la ventana ponderada (60); este
            # es el total real de partidos pitados en la fuente.
            "career_matches": int(grp["Date"].notna().sum()) if "Date" in grp.columns else int(len(grp)),
            "first_match":    grp["Date"].min().strftime("%Y-%m-%d") if "Date" in grp.columns and pd.notna(grp["Date"].min()) else None,
            "recent_matches": _referee_match_log(grp),
        }
        last_seen = max(filter(None, [overall.get("last_match"), (season_stats or {}).get("last_match")]), default=None)
        record["active"] = bool(season_stats) or _referee_is_active(last_seen)
        results.append(record)

    existing_keys = {(r["league"], key_map.get((r["league"], r["name"]), _referee_key(r["name"]))) for r in results}
    for (div, referee), season_stats in season_aggregates.items():
        if (div, key_map.get((div, referee), _referee_key(referee))) in existing_keys:
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
            "career_matches": season_stats["matches"],
            "first_match": None,
            "recent_matches": [],
            # Solo existe en el agregado de la temporada actual → activo.
            "active": True,
        })

    # Merge manual overrides (e.g. SP1/SP2 refs not provided by football-data.co.uk)
    manual_path = Path("DATOS") / "referees_manual.json"
    if manual_path.exists():
        try:
            import json as _json
            manual = _json.loads(manual_path.read_text(encoding="utf-8"))
            existing = {(r["name"], r["league"]) for r in results}
            added = 0
            names_by_league: dict = {}
            for r in results:
                names_by_league.setdefault(r["league"], []).append(r["name"])
            for r in manual:
                key = (r.get("name"), r.get("league"))
                league_names = names_by_league.get(r.get("league"), [])
                probe = _unified_referee_keys(pd.DataFrame(
                    [{"Div": r.get("league"), "Referee": n} for n in league_names + [r.get("name")]]))
                manual_key = probe.get((r.get("league"), r.get("name")))
                if key in existing or any(probe.get((r.get("league"), n)) == manual_key for n in league_names):
                    continue
                # Ficha manual estática: si no aparece en ninguna fuente viva
                # no ha pitado esta temporada → inactivo.
                results.append({**r, "active": False, "career_matches": r.get("matches"), "recent_matches": []})
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
    skip_heavy_rebuild = os.getenv("KICKDEX_SKIP_HEAVY_REBUILD") == "1"

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
    observed_teams = get_team_list(df, recent_only=True)
    leagues = build_leagues(df, observed_teams)
    teams = sorted(set(observed_teams) | set(all_roster_teams()))
    df_current = df[df["Date"] >= CURRENT_SEASON_START]
    print(
        f"     {len(df):,} partidos · {len(teams)} equipos "
        f"({len(observed_teams)} observados) · {len(df_players):,} registros jugadores"
    )

    # 3. Meta
    print("\n[3/6] meta.json + teams.json...")
    meta_payload = build_meta(df, df_current)
    write_json(meta_payload, "meta.json")
    write_json(teams, "teams.json")
    write_json(build_model_config(), "model_config.json")

    # 4. Team stats
    print("\n[4/6] team_stats.json...")
    if skip_heavy_rebuild:
        print("     Conservado por KICKDEX_SKIP_HEAVY_REBUILD=1")
    else:
        write_json(build_team_stats(df, teams), "team_stats.json")

    # 5. H2H
    print("\n[5/6] h2h.json...")
    if skip_heavy_rebuild:
        print("     Conservado por KICKDEX_SKIP_HEAVY_REBUILD=1")
    else:
        write_json(build_h2h(df, teams), "h2h.json")

    # 6. Players + Leagues + Fixtures + Referees
    print("\n[6/7] players.json, players_detail.json, referees.json...")
    espn_players = load_espn_player_matches()
    if not espn_players.empty:
        # Fuente principal: ESPN partido a partido (11 ligas, tiros a puerta y
        # faltas reales). Sustituye a Understat/FBref (sin SoT ni faltas, 5 ligas,
        # nombres de equipo sin normalizar).
        cup_rows = espn_players[espn_players["league"].isin(list(CUP_COMPETITIONS))]
        espn_players = espn_players[~espn_players["league"].isin(list(CUP_COMPETITIONS))]
        players_payload = add_player_percentiles(build_players_from_matches(espn_players), leagues)
        write_json(players_payload, "players.json")
        write_json(build_players_detail_from_matches(espn_players), "players_detail.json")
        # Champions: estadísticas solo de esa competición, aparte (mismo contrato).
        competitions = build_competitions()
        write_json(competitions, "competitions.json")
        if not cup_rows.empty:
            write_json(add_player_percentiles(build_players_from_matches(cup_rows), competitions), "players_cl.json")
        coverage = build_player_coverage(espn_players, leagues)
        coverage["source"] = "espn"
        coverage["scraped_at"] = _espn_sync_time() or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        coverage["matches"] = int(espn_players["event_id"].nunique())
    else:
        players_payload = build_players(df_players)
        players_payload = add_player_percentiles(players_payload, leagues)
        write_player_json(players_payload, "players.json", current_season_teams(leagues))
        write_player_json(build_players_detail(df_players), "players_detail.json", current_season_teams(leagues))
        coverage = build_player_coverage_from_json(leagues) if df_players.empty else build_player_coverage(df_players, leagues)
    write_json(coverage, "player_coverage.json")
    players_for_watch = _read_existing_json("players.json") or players_payload
    write_json(build_discipline_watch(players_for_watch, leagues), "discipline_watch.json")
    suspensions_payload = build_suspensions_payload(
        load_manual_suspension_rows(), leagues, load_suspension_source_catalog()
    )
    write_json(suspensions_payload, "suspensions.json")
    write_json(build_data_status(coverage), "data_status.json")
    referees_payload = build_referees(df, df_current)
    write_json(referees_payload, "referees.json")

    print("\n[7/7] leagues.json, fixtures.json, edges.json, trends.json...")
    write_json(leagues, "leagues.json")
    fixtures_payload = build_fixtures(df, leagues)
    fixtures_payload = write_fixtures_json(fixtures_payload)
    _write_alerts_json(fixtures_payload)
    if skip_heavy_rebuild:
        print("     Conservados edges.json y trends.json por KICKDEX_SKIP_HEAVY_REBUILD=1")
    else:
        edges_payload = build_edges(df)
        edges_payload = add_odds_based_edges(edges_payload, df, fixtures_payload)
        write_json(edges_payload, "edges.json")
        # Rachas sobre todo el historial (los últimos 20 partidos por equipo),
        # no solo la temporada actual: con ~1,6 partidos/equipo en 2026/27 ninguna
        # TrendRule llegaba a disparar. Ver plan fixture-first, Fase 0.1.
        write_json(build_trends_payload(df, teams), "trends.json")
    write_json(
        build_team_assets(leagues, _read_existing_json("team_assets.json"), _read_existing_json("competitions.json")),
        "team_assets.json",
    )
    write_json(
        build_player_assets(players_for_watch, _read_existing_json("player_assets.json")),
        "player_assets.json",
    )
    write_json(
        build_data_health(
            meta_payload,
            fixtures_payload,
            coverage,
            referees_payload,
            suspensions_payload,
            leagues,
            live_scores=_read_existing_json("live_scores.json"),
            standings=_read_existing_json("standings.json"),
            scorers=_read_existing_json("scorers.json"),
        ),
        "data_health.json",
    )

    print("\n" + "=" * 60)
    print("BUILD COMPLETADO")
    print("=" * 60)
    print(f"Archivos en: {OUTPUT_DIR.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

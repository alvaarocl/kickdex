import pandas as pd

from app.engine.metrics import get_weighted_referee_form
from scripts.build_data import _normalise_referee_frame, _referee_key, build_referees


def test_weighted_referee_form_from_incremental_rows():
    df = pd.DataFrame(
        [
            {"date": "2026-04-01", "league": "SP1", "referee": "Test Ref", "yellow_cards": 5, "red_cards": 1, "fouls": 28, "penalties": 1},
            {"date": "2026-04-08", "league": "SP1", "referee": "Test Ref", "yellow_cards": 3, "red_cards": 0, "fouls": 22, "penalties": 0},
            {"date": "2026-04-15", "league": "SP1", "referee": "Test Ref", "yellow_cards": 4, "red_cards": 0, "fouls": 20, "penalties": 0},
        ]
    )

    stats = get_weighted_referee_form(_normalise_referee_frame(df, "csv"))

    # Ponderado por antigüedad (HALF_LIFE_DAYS=270): el partido más reciente
    # (04-15) pesa más que el más antiguo (04-01), así que la media ya no es
    # la media plana simple (4.0, 0.33, 23.33, 0.33).
    assert stats["matches"] == 3
    assert stats["yellows_per_match"] == 3.99
    assert stats["reds_per_match"] == 0.33
    assert stats["fouls_per_match"] == 23.29
    assert stats["penalties_per_match"] == 0.33
    assert stats["last_match"] == "2026-04-15"


def test_referee_key_merges_initials_and_full_name():
    # football-data.co.uk usa iniciales; worldsoccerdata usa nombre completo.
    # Sin esta normalización nunca se cruzan y el árbitro queda partido en
    # dos registros (uno con historial, otro con la temporada actual).
    assert _referee_key("A Taylor") == _referee_key("Anthony Taylor") == "taylor_a"


def test_build_referees_uses_incremental_file(tmp_path, monkeypatch):
    data_dir = tmp_path / "datos"
    data_dir.mkdir()
    (data_dir / "referees_matches.csv").write_text(
        "\n".join(
            [
                "fixture_id,date,league,league_name,referee,home,away,home_score,away_score,yellow_cards,red_cards,fouls,penalties,source,updated_at",
                "1,2026-04-01,SP1,La Liga,Test Ref,A,B,1,0,5,0,24,0,api-football,2026-04-01T00:00:00Z",
                "2,2026-04-08,SP1,La Liga,Test Ref,C,D,1,1,3,1,22,1,api-football,2026-04-08T00:00:00Z",
                "3,2026-04-15,SP1,La Liga,Test Ref,E,F,0,0,4,0,20,0,api-football,2026-04-15T00:00:00Z",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.config.DATA_DIR", str(data_dir))

    base = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-04-01", "2026-04-08", "2026-04-15"]),
            "Div": ["SP1", "SP1", "SP1"],
            "Referee": ["Base Ref", "Base Ref", "Base Ref"],
            "HY": [2, 2, 2],
            "AY": [1, 1, 1],
            "HR": [0, 0, 0],
            "AR": [0, 0, 0],
            "HF": [10, 10, 10],
            "AF": [12, 12, 12],
        }
    )

    refs = build_referees(base, base)
    by_name = {r["name"]: r for r in refs}

    assert by_name["Test Ref"]["source"] == "api-football"
    assert by_name["Test Ref"]["last5"]["matches"] == 3
    assert by_name["Test Ref"]["yellows_per_match"] == 3.99


def test_build_referees_uses_season_aggregate_file(tmp_path, monkeypatch):
    data_dir = tmp_path / "datos"
    data_dir.mkdir()
    (data_dir / "referees_season.csv").write_text(
        "\n".join(
            [
                "league,league_name,referee,matches,yellow_cards,second_yellow_cards,red_cards,source,updated_at",
                "SP1,La Liga,Season Ref,10,52,2,1,worldsoccerdata,2026-04-30T00:00:00Z",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.config.DATA_DIR", str(data_dir))

    base = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-04-01", "2024-04-08", "2024-04-15"]),
            "Div": ["E0", "E0", "E0"],
            "Referee": ["Base Ref", "Base Ref", "Base Ref"],
            "HY": [2, 2, 2],
            "AY": [1, 1, 1],
            "HR": [0, 0, 0],
            "AR": [0, 0, 0],
            "HF": [10, 10, 10],
            "AF": [12, 12, 12],
        }
    )

    refs = build_referees(base, base)
    by_name = {r["name"]: r for r in refs}

    assert by_name["Season Ref"]["source"] == "worldsoccerdata"
    assert by_name["Season Ref"]["season"]["matches"] == 10
    assert by_name["Season Ref"]["season"]["yellows_per_match"] == 5.2
    assert by_name["Season Ref"]["season"]["reds_per_match"] == 0.3
    assert by_name["Season Ref"]["season_last5"] is None


def test_build_referees_merges_initials_and_full_name_sources(tmp_path, monkeypatch):
    # football-data.co.uk trae "A Taylor" (per-match, historial real);
    # worldsoccerdata trae "Anthony Taylor" (agregado de temporada actual)
    # para la misma persona. Antes del fix esto generaba DOS registros
    # separados y season_last5/season_last10 quedaban siempre vacíos porque
    # nunca se cruzaban con el historial per-match.
    data_dir = tmp_path / "datos"
    data_dir.mkdir()
    (data_dir / "referees_season.csv").write_text(
        "\n".join(
            [
                "league,league_name,referee,matches,yellow_cards,second_yellow_cards,red_cards,source,updated_at",
                "E0,Premier League,Anthony Taylor,20,80,4,2,worldsoccerdata,2026-08-20T00:00:00Z",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.config.DATA_DIR", str(data_dir))

    base = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-08-10", "2026-08-15", "2026-08-20"]),
            "Div": ["E0", "E0", "E0"],
            "Referee": ["A Taylor", "A Taylor", "A Taylor"],
            "HY": [2, 2, 2],
            "AY": [1, 1, 1],
            "HR": [0, 0, 0],
            "AR": [0, 0, 0],
            "HF": [10, 10, 10],
            "AF": [12, 12, 12],
        }
    )

    refs = build_referees(base, base)
    e0_refs = [r for r in refs if r["league"] == "E0"]

    assert len(e0_refs) == 1
    record = e0_refs[0]
    assert record["overall"] is not None
    # El agregado de temporada de worldsoccerdata (20 partidos) se descarta
    # en favor del partido a partido real de la temporada actual (3
    # partidos) en cuanto este existe — es una fuente mas fiable aunque
    # tenga menos muestra, y evita mostrar un numero desfasado.
    assert record["season"] is not None
    assert record["season"]["matches"] == 3
    assert record["season_last5"] is not None


def test_stale_worldsoccerdata_season_aggregate_never_overrides_real_current_season_data(tmp_path, monkeypatch):
    # Bug real encontrado en datos de produccion: el scrape de
    # worldsoccerdata puede quedar desfasado (fecha de actualizacion previa
    # al inicio de la temporada actual) y entonces su "matches" de temporada
    # no tiene nada que ver con la realidad. En cuanto hay UN SOLO partido
    # real de la temporada actual (aunque sea insuficiente para promediar,
    # min_matches=3), season debe quedar en None en vez de mostrar el
    # agregado desfasado como si fuera fiable.
    data_dir = tmp_path / "datos"
    data_dir.mkdir()
    (data_dir / "referees_season.csv").write_text(
        "\n".join(
            [
                "league,league_name,referee,matches,yellow_cards,second_yellow_cards,red_cards,source,updated_at",
                "E0,Premier League,Michael Oliver,29,85,0,2,worldsoccerdata,2026-08-06T15:26:12Z",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.config.DATA_DIR", str(data_dir))

    # Historico (>=3 partidos, para que "overall" exista) con solo UN
    # partido dentro de la temporada actual (por debajo de min_matches=3) —
    # el resto son de la temporada anterior.
    history = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2025-11-01", "2025-11-08", "2026-08-22"]),
            "Div": ["E0", "E0", "E0"],
            "Referee": ["M Oliver", "M Oliver", "M Oliver"],
            "HY": [2, 2, 3],
            "AY": [1, 1, 2],
            "HR": [0, 0, 0],
            "AR": [0, 0, 0],
            "HF": [10, 10, 10],
            "AF": [12, 12, 12],
        }
    )
    current_season_only = history.iloc[[2]]  # solo el partido de 2026-08-22

    refs = build_referees(history, current_season_only)
    record = next(r for r in refs if r["league"] == "E0")

    assert record["overall"] is not None
    assert record["season"] is None

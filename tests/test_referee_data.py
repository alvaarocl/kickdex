import pandas as pd

from scripts.build_data import _ref_stats, build_referees


def test_ref_stats_from_incremental_rows():
    df = pd.DataFrame(
        [
            {"date": "2026-04-01", "league": "SP1", "referee": "Test Ref", "yellow_cards": 5, "red_cards": 1, "fouls": 28, "penalties": 1},
            {"date": "2026-04-08", "league": "SP1", "referee": "Test Ref", "yellow_cards": 3, "red_cards": 0, "fouls": 22, "penalties": 0},
            {"date": "2026-04-15", "league": "SP1", "referee": "Test Ref", "yellow_cards": 4, "red_cards": 0, "fouls": 20, "penalties": 0},
        ]
    )

    stats = _ref_stats(df)

    assert stats["matches"] == 3
    assert stats["yellows_per_match"] == 4.0
    assert stats["reds_per_match"] == 0.33
    assert stats["fouls_per_match"] == 23.33
    assert stats["penalties_per_match"] == 0.33
    assert stats["last_match"] == "2026-04-15"


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
    assert by_name["Test Ref"]["yellows_per_match"] == 4.0

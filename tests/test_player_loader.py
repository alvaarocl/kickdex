from pathlib import Path

import pandas as pd

from app.data import loader


def test_get_team_list_empty_dataframe():
    assert loader.get_team_list(pd.DataFrame()) == []


def test_load_players_from_per_league_csv(tmp_path, monkeypatch):
    data_dir = tmp_path / "datos"
    players_dir = data_dir / "players"
    players_dir.mkdir(parents=True)
    csv_path = players_dir / "laliga.csv"
    csv_path.write_text(
        "date,team,player,sh,sot,gls,ast,fls,crdy,min,league\n"
        "2025-09-01,Real Madrid,Jugador Uno,3,2,1,0,1,0,90,SP1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(loader, "DATA_DIR", str(data_dir))

    df = loader.load_players()

    assert len(df) == 1
    row = df.iloc[0]
    assert row["team"] == "Real Madrid"
    assert row["player"] == "Jugador Uno"
    assert row["sh"] == 3
    assert row["sot"] == 2
    assert row["league"] == "SP1"

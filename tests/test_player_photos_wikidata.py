import json

from scripts import update_player_photos_wikidata as wd


def _binding(name, qid, person_label, image=None, team_label=None):
    row = {
        "name": {"value": name},
        "person": {"value": f"http://www.wikidata.org/entity/{qid}"},
        "personLabel": {"value": person_label},
    }
    if image:
        row["image"] = {"value": f"http://commons.wikimedia.org/wiki/Special:FilePath/{image}"}
    if team_label:
        row["teamLabel"] = {"value": team_label}
    return row


def test_match_players_accepts_unique_named_candidate_with_photo():
    bindings = [_binding("Bukayo Saka", "Q1", "Bukayo Saka", image="Bukayo_Saka.jpg", team_label="Arsenal F.C.")]
    result = wd.match_players(["Bukayo Saka"], "Arsenal", bindings)
    assert result["Bukayo Saka"]["qid"] == "Q1"
    assert result["Bukayo Saka"]["photo"].endswith("Bukayo_Saka.jpg?width=300")


def test_match_players_returns_none_without_photo():
    bindings = [_binding("Bukayo Saka", "Q1", "Bukayo Saka", team_label="Arsenal F.C.")]
    result = wd.match_players(["Bukayo Saka"], "Arsenal", bindings)
    assert result["Bukayo Saka"] is None


def test_match_players_disambiguates_using_team_score():
    # Dos personas distintas llamadas "Rodri" (alias corto) — una juega en el
    # Real Madrid, otra en el Manchester City. Sólo el Manchester City debe
    # ganar cuando consultamos la plantilla del Manchester City.
    bindings = [
        _binding("Rodri", "Q1", "Rodrigo Hernandez", image="Rodri_ManCity.jpg", team_label="Manchester City F.C."),
        _binding("Rodri", "Q2", "Rodrigo Some Other Player", image="Rodri_Other.jpg", team_label="Real Madrid CF"),
    ]
    result = wd.match_players(["Rodri"], "Manchester City", bindings)
    assert result["Rodri"]["qid"] == "Q1"


def test_match_players_flags_ambiguous_when_team_scores_tie():
    bindings = [
        _binding("John Smith", "Q1", "John Smith", image="a.jpg", team_label="Some FC"),
        _binding("John Smith", "Q2", "John Smith", image="b.jpg", team_label="Some FC"),
    ]
    result = wd.match_players(["John Smith"], "Different Team", bindings)
    assert result["John Smith"] == "AMBIGUOUS"


def test_match_players_missing_when_no_binding():
    result = wd.match_players(["Nobody"], "Arsenal", [])
    assert result["Nobody"] is None


def test_photo_url_from_image_uri_encodes_width():
    url = wd._photo_url_from_image_uri("http://commons.wikimedia.org/wiki/Special:FilePath/Foo%20Bar.jpg")
    assert url == "https://commons.wikimedia.org/wiki/Special:FilePath/Foo%20Bar.jpg?width=300"


def test_update_player_photos_dry_run_does_not_write(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DATA_DIR", tmp_path)
    (tmp_path / "players.json").write_text(
        json.dumps({"Arsenal": [{"player": "Bukayo Saka"}]}), encoding="utf-8"
    )

    monkeypatch.setattr(
        wd, "query_wikidata",
        lambda names, timeout=30: [_binding("Bukayo Saka", "Q1", "Bukayo Saka", image="s.jpg", team_label="Arsenal F.C.")],
    )

    stats = wd.update_player_photos(dry_run=True, sleep_seconds=0)

    assert stats["matched"] == 1
    assert not (tmp_path / "player_assets.json").exists()


def test_update_player_photos_writes_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DATA_DIR", tmp_path)
    (tmp_path / "players.json").write_text(
        json.dumps({"Arsenal": [{"player": "Bukayo Saka"}]}), encoding="utf-8"
    )

    monkeypatch.setattr(
        wd, "query_wikidata",
        lambda names, timeout=30: [_binding("Bukayo Saka", "Q1", "Bukayo Saka", image="s.jpg", team_label="Arsenal F.C.")],
    )

    stats = wd.update_player_photos(sleep_seconds=0)
    assert stats["matched"] == 1

    manifest = json.loads((tmp_path / "player_assets.json").read_text(encoding="utf-8"))
    asset = manifest["players"]["Arsenal::Bukayo Saka"]
    assert asset["photo"].endswith("s.jpg?width=300")
    assert asset["source"] == "wikidata"


def test_update_player_photos_skips_players_with_existing_photo(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "DATA_DIR", tmp_path)
    (tmp_path / "players.json").write_text(
        json.dumps({"Arsenal": [{"player": "Bukayo Saka"}]}), encoding="utf-8"
    )
    (tmp_path / "player_assets.json").write_text(
        json.dumps({"players": {"Arsenal::Bukayo Saka": {"photo": "https://existing.example/photo.jpg"}}}),
        encoding="utf-8",
    )

    called = []

    def fake_query(names, timeout=30):
        called.append(names)
        return []

    monkeypatch.setattr(wd, "query_wikidata", fake_query)

    stats = wd.update_player_photos(sleep_seconds=0)

    assert stats["skipped_existing"] == 1
    assert called == []  # no debería ni consultar Wikidata para un jugador ya cubierto

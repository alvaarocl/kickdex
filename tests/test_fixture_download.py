from app.data.fixture_download import _canonical_team


def test_canonical_team_matches_suffix_names():
    teams = ["Blackburn", "Leicester", "QPR", "Sheffield Weds"]

    assert _canonical_team("Blackburn Rovers", teams) == "Blackburn"
    assert _canonical_team("Leicester City", teams) == "Leicester"
    assert _canonical_team("Queens Park Rangers", teams) == "QPR"
    assert _canonical_team("Sheffield Wednesday", teams) == "Sheffield Weds"

from app.data.fixture_download import _canonical_team, fixture_download_slugs


def test_canonical_team_matches_suffix_names():
    teams = ["Blackburn", "Leicester", "QPR", "Sheffield Weds"]

    assert _canonical_team("Blackburn Rovers", teams) == "Blackburn"
    assert _canonical_team("Leicester City", teams) == "Leicester"
    assert _canonical_team("Queens Park Rangers", teams) == "QPR"
    assert _canonical_team("Sheffield Wednesday", teams) == "Sheffield Weds"


def test_fixture_download_slugs_follow_current_season():
    assert fixture_download_slugs(2026)["SP1"] == "la-liga-2026"
    assert fixture_download_slugs(2026)["E0"] == "epl-2026"


def test_canonical_team_handles_current_season_feed_names():
    assert _canonical_team("R. Racing Club", ["Santander", "Elche"]) == "Santander"
    assert _canonical_team("Atl. Madrid", ["Ath Madrid", "Malaga"]) == "Ath Madrid"
    assert _canonical_team(
        "RCD Espanyol de Barcelona", ["Barcelona", "Espanol"]
    ) == "Espanol"
    assert _canonical_team("Internazionale", ["Inter", "Milan"]) == "Inter"
    assert _canonical_team("Fortuna Sittard", ["For Sittard", "Ajax"]) == "For Sittard"


def test_midnight_utc_is_treated_as_unconfirmed_kickoff():
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    from app.data.fixture_download import _local_date_time

    madrid = ZoneInfo("Europe/Madrid")
    # Marcador de FixtureDownload: no es "viernes 02:00" en Madrid.
    assert _local_date_time(datetime(2026, 10, 9, 0, 0, tzinfo=timezone.utc), madrid) == ("2026-10-09", "")
    assert _local_date_time(datetime(2026, 10, 10, 13, 30, tzinfo=timezone.utc), madrid) == ("2026-10-10", "15:30")

from scripts import update_referee_data


def test_update_referees_skips_unavailable_api_plan(monkeypatch):
    monkeypatch.setenv("APIFOOTBALL_KEY", "test-key")

    def blocked_request(path, params, key, timeout=25):
        raise RuntimeError("API-Football error on /fixtures: {'plan': 'Free plans do not have access to this season'}")

    monkeypatch.setattr(update_referee_data, "_request", blocked_request)
    monkeypatch.setattr(update_referee_data, "_load_existing_ids", lambda path: set())

    appended = update_referee_data.update_referees(
        days_back=7,
        leagues=["SP1"],
        sleep_seconds=0,
        max_fixtures=1,
    )

    assert appended == 0

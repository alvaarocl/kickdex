from app import config


def test_current_season_contract_is_consistent():
    assert config.CURRENT_SEASON_CODE == "2627"
    assert config.CURRENT_SEASON_START == "2026-08-01"
    assert config.CURRENT_SEASON_LABEL == "2026/27"
    assert config.CURRENT_SEASON_YEAR == 2026
    assert config.CURRENT_SEASON_CODE == f"{str(config.CURRENT_SEASON_YEAR)[-2:]}{str(config.CURRENT_SEASON_YEAR + 1)[-2:]}"

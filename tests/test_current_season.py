from app import config


def test_current_season_contract_is_consistent():
    from datetime import date
    year = config.season_year_for(date.today())
    assert config.CURRENT_SEASON_YEAR == year
    assert config.CURRENT_SEASON_START == f"{year}-08-01"
    assert config.CURRENT_SEASON_LABEL == f"{year}/{str(year + 1)[-2:]}"
    assert config.CURRENT_SEASON_CODE == f"{str(config.CURRENT_SEASON_YEAR)[-2:]}{str(config.CURRENT_SEASON_YEAR + 1)[-2:]}"


def test_season_rolls_over_automatically_on_july_first():
    from datetime import date
    from app.config import season_year_for

    assert season_year_for(date(2026, 6, 30)) == 2025
    assert season_year_for(date(2026, 7, 1)) == 2026
    assert season_year_for(date(2027, 3, 15)) == 2026
    assert season_year_for(date(2027, 8, 20)) == 2027

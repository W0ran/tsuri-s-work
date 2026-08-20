import pytest


@pytest.mark.skip(
    reason=(
        "UI переключателя темы ещё не разведан — не было скриншота открытого "
        "меню. Сверить локатор в pages/common/shell_page.py (theme_toggle) "
        "через playwright codegen и включить тест."
    )
)
def test_theme_switch_persists_after_reload():
    pass

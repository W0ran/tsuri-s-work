import pytest


@pytest.mark.skip(
    reason=(
        "UI переключателя языка ещё не разведан — не было скриншота "
        "открытого меню. Сверить локатор в pages/common/shell_page.py "
        "(language_toggle) через playwright codegen и включить тест."
    )
)
def test_language_switch_changes_ui_language():
    pass

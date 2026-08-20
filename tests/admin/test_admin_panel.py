import pytest


@pytest.mark.admin
@pytest.mark.skip(
    reason=(
        "UI панели администратора (/admin) ещё не изучен — нужна сессия "
        "playwright codegen под учёткой admin, чтобы наполнить "
        "pages/admin/admin_page.py реальными локаторами."
    )
)
def test_admin_placeholder():
    pass

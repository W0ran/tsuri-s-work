from playwright.sync_api import expect
from pages.common.shell_page import ShellPage
from tests.conftest import login_as
import config


def test_logout_returns_to_login(login_page, role):
    """Предполагаем, что кнопка "Выйти" одинакова для всех ролей (общий
    ShellPage). Если у какой-то роли разметка отличается — поправить в
    pages/common/shell_page.py, тест менять не нужно."""
    page = login_as(login_page, role)

    shell = ShellPage(page)
    shell.logout()

    expect(page).to_have_url(f"{config.BASE_URL}/login")

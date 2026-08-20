from playwright.sync_api import expect
from tests.conftest import login_as
import config


def test_login_page_loads(login_page):
    expect(login_page.heading).to_be_visible()
    expect(login_page.login_input).to_be_visible()
    expect(login_page.password_input).to_be_visible()
    expect(login_page.submit_button).to_be_visible()


def test_successful_login_for_role(login_page, role):
    """Общий тест для всех 5 ролей: после успешного логина пользователь
    уходит со страницы /login. Уходит целенаправленно от проверки
    конкретного URL/дашборда — это специфика роли и живёт в её собственных
    тестах (tests/applicant/test_wizard.py и т.д.)."""
    page = login_as(login_page, role)
    expect(page).not_to_have_url(f"{config.BASE_URL}/login")


def test_login_with_invalid_credentials(login_page):
    login_page.login("admin", "wrong")

    expect(login_page.error_message).to_be_visible()
    expect(login_page.page).to_have_url(f"{config.BASE_URL}/login")


def test_login_with_empty_fields(login_page):
    login_page.submit_button.click()

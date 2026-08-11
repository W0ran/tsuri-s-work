from playwright.sync_api import expect
from pages.home_page import HomePage
import config


def test_login_page_loads(login_page):
    expect(login_page.heading).to_be_visible()
    expect(login_page.login_input).to_be_visible()
    expect(login_page.password_input).to_be_visible()
    expect(login_page.submit_button).to_be_visible()


def test_successful_login(login_page, page):
    login_page.login(config.APPLICANT_LOGIN, config.APPLICANT_PASSWORD)

    home = HomePage(page)
    expect(page).to_have_url(f"{config.BASE_URL}/applicant")
    expect(home.page_heading).to_be_visible()
    expect(home.user_badge).to_be_visible()


def test_login_with_invalid_credentials(login_page):
    login_page.login("admin", "wrong")

    expect(login_page.error_message).to_be_visible()
    expect(login_page.page).to_have_url(f"{config.BASE_URL}/login")


def test_login_with_empty_fields(login_page):
    login_page.submit_button.click()
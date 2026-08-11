import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage
import config


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    lp = LoginPage(page)
    lp.open(config.BASE_URL)
    return lp
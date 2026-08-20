import pytest
from playwright.sync_api import Page
from tests.conftest import login_as


@pytest.fixture
def admin_page(login_page) -> Page:
    return login_as(login_page, "admin")

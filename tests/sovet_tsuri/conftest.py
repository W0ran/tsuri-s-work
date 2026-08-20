import pytest
from playwright.sync_api import Page

from pages.sovet_tsuri.sovet_tsuri_page import SovetTsuriPage
from tests.conftest import login_as
import config


@pytest.fixture
def sovet_tsuri_page(login_page) -> Page:
    page = login_as(login_page, "sovet_tsuri")
    # см. аналогичный комментарий в tests/predsedatel/conftest.py
    page.wait_for_url(f"{config.BASE_URL}/", timeout=15_000)
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture
def council_page(sovet_tsuri_page) -> SovetTsuriPage:
    cp = SovetTsuriPage(sovet_tsuri_page)
    cp.open(config.BASE_URL)
    return cp

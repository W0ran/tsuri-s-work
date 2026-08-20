import pytest
from playwright.sync_api import Page

from pages.predsedatel.predsedatel_page import PredsedatelPage
from tests.conftest import login_as
import config


@pytest.fixture
def predsedatel_page(login_page) -> Page:
    page = login_as(login_page, "predsedatel")
    # login_as не ждёт завершения пост-логинового редиректа на "/" — без
    # этого ожидания council_page, который сразу после логина делает goto()
    # на /council, гонится с этим редиректом (тот же баг, что чинили в
    # tests/expert/conftest.py для /expert)
    page.wait_for_url(f"{config.BASE_URL}/", timeout=15_000)
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture
def council_page(predsedatel_page) -> PredsedatelPage:
    cp = PredsedatelPage(predsedatel_page)
    cp.open(config.BASE_URL)
    return cp

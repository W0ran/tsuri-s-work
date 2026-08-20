import pytest
from playwright.sync_api import Page

from pages.expert.expert_page import ExpertPage
from pages.expert.workflow_page import WorkflowPage
from pages.expert.reference_page import ReferencePage
from tests.conftest import login_as
import config


@pytest.fixture
def expert_page(login_page) -> Page:
    page = login_as(login_page, "expert")
    # login_as не ждёт завершения пост-логинового редиректа на /expert — без
    # этого ожидания фикстуры workflow_page/reference_page, которые сразу
    # после логина делают goto() на другой урл, гонятся с этим редиректом и
    # проигрывают: обе навигации в SPA конфликтуют, страница остаётся на /expert
    page.wait_for_url("**/expert", timeout=15_000)
    # и без этого ожидания KPI/таблица заявок читаются раньше, чем клиент
    # успевает подгрузить данные асинхронным запросом после редиректа
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture
def expert_list_page(expert_page) -> ExpertPage:
    # логин под ролью expert уже приземляет на /expert — просто оборачиваем
    return ExpertPage(expert_page)


@pytest.fixture
def workflow_page(expert_page) -> WorkflowPage:
    wp = WorkflowPage(expert_page)
    wp.open(config.BASE_URL)
    return wp


@pytest.fixture
def reference_page(expert_page) -> ReferencePage:
    rp = ReferencePage(expert_page)
    rp.open(config.BASE_URL)
    return rp

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from playwright.sync_api import Page
from pages.common.login_page import LoginPage
import config

from generate_fixtures import ensure_fixture_files


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_files():
    ensure_fixture_files()


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    lp = LoginPage(page)
    lp.open(config.BASE_URL)
    return lp


ALL_ROLES = ["applicant", "expert", "admin", "predsedatel", "sovet_tsuri"]


@pytest.fixture(params=ALL_ROLES)
def role(request) -> str:
    """Параметризация по всем ролям — используется в common/ и workflows/
    тестах, где поведение должно быть одинаковым независимо от роли."""
    return request.param


def login_as(login_page: LoginPage, role: str) -> Page:
    """Логинит под указанной ролью; пропускает тест (pytest.skip), если в
    .env нет логина/пароля для этой роли. Переиспользуется ролевыми
    conftest.py (tests/applicant/conftest.py и т.д.) для получения
    залогиненной страницы под конкретную, не параметризованную роль."""
    creds = config.USERS[role]
    if not creds["login"] or not creds["password"]:
        pytest.skip(f"В .env нет логина/пароля для роли '{role}' — тест пропущен")
    login_page.login(creds["login"], creds["password"])
    return login_page.page

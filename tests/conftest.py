import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage
from pages.upload_page import UploadPage
from pages.wizard_page import WizardPage
import config


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    lp = LoginPage(page)
    lp.open(config.BASE_URL)
    return lp


ALL_ROLES = ["applicant", "expert", "admin", "chairman", "board_member"]
# Временно ограничено ролью "applicant": для остальных ролей ещё не изучен
# реальный UI-флоу (есть ли у них "Создать заявку", куда логин их приводит и
# т.д. — предварительная проверка показала разное и нестабильное поведение).
# Верните ALL_ROLES, когда флоу для каждой роли будет проверен и учтён в
# WizardPage/UploadPage.
ACTIVE_ROLES = ["applicant"]


@pytest.fixture(params=ACTIVE_ROLES)
def role(request) -> str:
    return request.param


@pytest.fixture
def logged_in_page(login_page: LoginPage, role: str) -> Page:
    creds = config.USERS[role]
    if not creds["login"] or not creds["password"]:
        pytest.skip(f"В .env нет логина/пароля для роли '{role}' — тест пропущен")
    login_page.login(creds["login"], creds["password"])
    return login_page.page


@pytest.fixture
def upload_page(logged_in_page) -> UploadPage:
    wizard = WizardPage(logged_in_page)
    wizard.start_new_application_and_reach_documents()
    return UploadPage(logged_in_page)

from generate_fixtures import ensure_fixture_files

@pytest.fixture(scope="session", autouse=True)
def _prepare_test_files():
    ensure_fixture_files()
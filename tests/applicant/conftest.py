import pytest
from playwright.sync_api import Page

from pages.applicant.wizard_page import WizardPage
from pages.applicant.upload_page import UploadPage
from pages.applicant.applications_list_page import ApplicationsListPage
from tests.conftest import login_as


@pytest.fixture
def applicant_page(login_page) -> Page:
    return login_as(login_page, "applicant")


@pytest.fixture
def applications_list_page(applicant_page) -> ApplicationsListPage:
    return ApplicationsListPage(applicant_page)


@pytest.fixture
def upload_page(applicant_page) -> UploadPage:
    wizard = WizardPage(applicant_page)
    wizard.start_new_application_and_reach_documents()
    return UploadPage(applicant_page)


@pytest.fixture
def application_params_page(applicant_page) -> WizardPage:
    """Доводит до раздела "Параметры" (подраздел "1. Основное"), не уходя
    во вкладку "Документы" — нужно для тестов, которые работают с полями
    заявки (Заявитель, Производитель, Торговое наименование и т.д.)."""
    wizard = WizardPage(applicant_page)
    wizard.open_new_application()
    wizard.select_default_criteria()
    applicant_page.wait_for_timeout(1000)
    return wizard

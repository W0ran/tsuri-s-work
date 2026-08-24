# Переиспользуем фикстуры заявителя (applicant_page, upload_page,
# application_params_page) — импорт делает их видимыми для pytest в этой
# директории, не дублируя код.
import pytest

from tests.applicant.conftest import applicant_page, upload_page, application_params_page  # noqa: F401


@pytest.fixture
def wizard_page(application_params_page):
	return application_params_page

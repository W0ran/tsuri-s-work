# Переиспользуем фикстуры заявителя (applicant_page, upload_page) —
# импорт делает их видимыми для pytest в этой директории, не дублируя код.
from tests.applicant.conftest import applicant_page, upload_page  # noqa: F401

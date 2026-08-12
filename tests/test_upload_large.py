# tests/test_document_upload_large.py
import os
import time
import pytest
from pages.upload_page import UploadPage

LARGE_FILE_PATH = "fixtures/sample_documents/_generated_large.pdf"
LARGE_FILE_SIZE_MB = 20


@pytest.fixture(scope="module", autouse=True)
def generate_large_file():
    # генерируем файл заметно крупнее типичных лимитов (5-10 МБ) один раз перед модулем, удаляем после
    if not os.path.exists(LARGE_FILE_PATH):
        with open(LARGE_FILE_PATH, "wb") as f:
            f.write(b"%PDF-1.4\n" + os.urandom(LARGE_FILE_SIZE_MB * 1024 * 1024))
    yield
    # браузер может ещё какое-то время держать файл открытым на Windows
    # после закрытия страницы (антивирус/индексатор тоже могут держать хендл) — даём пару попыток
    for attempt in range(5):
        try:
            os.remove(LARGE_FILE_PATH)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(1)


def test_upload_large_file_no_size_limit(upload_page: UploadPage):
    upload_page.upload_file(LARGE_FILE_PATH)
    # 20 МБ обычно грузится за ~20с, но сайт под нагрузкой заметно замедляется —
    # даём щедрый запас, чтобы тест не был флакующим на медленной сети/сервере
    upload_page.wait_for_upload_complete("_generated_large.pdf", timeout=240_000)
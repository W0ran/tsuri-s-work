# tests/test_document_upload_large.py
import os
import time
import pytest
from pages.upload_page import UploadPage

LARGE_FILE_PATH = "fixtures/sample_documents/_generated_large.pdf"
LARGE_FILE_SIZE_MB = 20


def _build_large_but_valid_pdf(padding_mb: int) -> bytes:
    """Структурно валидный PDF (с корректными xref/trailer/%%EOF), где нужный
    объём "веса" — просто байты внутри потока-содержимого страницы (парсер
    пропускает ровно /Length байт, не разбирая их как PDF-синтаксис).
    Новая глубокая PDF-валидация проверяет корректное завершение документа —
    файл из одного заголовка + случайного мусора после него (как было раньше)
    теперь считается повреждённым и отклоняется."""
    padding = os.urandom(padding_mb * 1024 * 1024)
    stream_content = b"BT /F1 12 Tf 20 100 Td (QA large sample PDF) Tj ET\n" + padding
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]"
        b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length " + str(len(stream_content)).encode() + b">>\n"
        b"stream\n" + stream_content + b"\nendstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n0\n%%EOF\n"
    )


@pytest.fixture(scope="module", autouse=True)
def generate_large_file():
    # генерируем файл заметно крупнее типичных лимитов (5-10 МБ) один раз перед модулем, удаляем после
    if not os.path.exists(LARGE_FILE_PATH):
        with open(LARGE_FILE_PATH, "wb") as f:
            f.write(_build_large_but_valid_pdf(LARGE_FILE_SIZE_MB))
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
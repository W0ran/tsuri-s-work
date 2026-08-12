import pytest
from pages.upload_page import UploadPage

VALID_FILES = {
    "pdf": "fixtures/sample_documents/sample.pdf",
    "png": "fixtures/sample_documents/sample.png",
    "jpeg": "fixtures/sample_documents/sample.jpg",
    "doc": "fixtures/sample_documents/sample.doc",
    "docx": "fixtures/sample_documents/sample.docx",
}

IMAGE_EXTENSIONS = {"png", "jpeg"}

INVALID_FILES = {
    "exe": "fixtures/invalid_documents/sample.exe",
    "zip": "fixtures/invalid_documents/sample.zip",
    "txt": "fixtures/invalid_documents/sample.txt",
}


def _card_for(file_type: str) -> str:
    return UploadPage.IMAGE_CARD_TITLE if file_type in IMAGE_EXTENSIONS else UploadPage.DOC_CARD_TITLE


@pytest.mark.parametrize("file_type,path", VALID_FILES.items())
def test_upload_valid_formats(upload_page: UploadPage, file_type, path):
    card = _card_for(file_type)
    upload_page.upload_file(path)
    upload_page.wait_for_upload_complete(path.split("/")[-1], card_title=card)
    filenames = upload_page.get_uploaded_filenames(card_title=card)
    assert any(path.split("/")[-1] in f for f in filenames)


@pytest.mark.parametrize("file_type,path", INVALID_FILES.items())
def test_upload_invalid_formats_rejected(upload_page: UploadPage, file_type, path):
    upload_page.upload_file(path)
    assert upload_page.is_error_visible()


def test_upload_spoofed_extension_rejected(upload_page: UploadPage):
    spoofed_path = "fixtures/invalid_documents/fake_executable.pdf"  # содержимое — реальный exe
    upload_page.upload_file(spoofed_path)
    # если валидация только по расширению — этот тест провалится, и это находка, а не баг теста
    assert upload_page.is_error_visible()


def test_submit_without_files_blocked(upload_page: UploadPage):
    # реальная кнопка отправки — "Отправить в экспертизу" на шаге "Проверка".
    # Она задизейблена, пока не заполнены все обязательные типы документов
    # (в т.ч. если не загружен вообще ни один новый документ в этой сессии).
    upload_page.go_to_review()
    assert not upload_page.is_submit_enabled()


def test_upload_multiple_files(upload_page: UploadPage):
    # оба файла одного формата (pdf, doc) — идут в одну карточку "Общая документация"
    paths = [VALID_FILES["pdf"], VALID_FILES["doc"]]
    upload_page.upload_multiple(paths)
    for p in paths:
        upload_page.wait_for_upload_complete(p.split("/")[-1])
    assert len(upload_page.get_uploaded_filenames()) >= 2


def test_delete_uploaded_file(upload_page: UploadPage):
    upload_page.upload_file(VALID_FILES["pdf"])
    filename = VALID_FILES["pdf"].split("/")[-1]
    upload_page.wait_for_upload_complete(filename)
    upload_page.delete_uploaded_file(filename)
    assert filename not in upload_page.get_uploaded_filenames()


@pytest.mark.parametrize("filename", [
    "документ_с_кириллицей.pdf",
    "file with spaces.pdf",
    "файл-№1 (копия).pdf",
])
def test_upload_special_filenames(upload_page: UploadPage, filename):
    # предполагается наличие подготовленных копий с такими именами в fixtures
    path = f"fixtures/sample_documents/{filename}"
    upload_page.upload_file(path)
    upload_page.wait_for_upload_complete(filename, timeout=30_000)


def test_replace_uploaded_file(upload_page: UploadPage):
    """Замена одного файла другим: удаляем загруженный файл и загружаем на его
    место другой — старого не должно остаться, новый должен появиться."""
    first_path = VALID_FILES["pdf"]
    second_path = VALID_FILES["doc"]
    first_name = first_path.split("/")[-1]
    second_name = second_path.split("/")[-1]

    upload_page.upload_file(first_path)
    upload_page.wait_for_upload_complete(first_name)

    upload_page.delete_uploaded_file(first_name)
    assert first_name not in upload_page.get_uploaded_filenames()

    upload_page.upload_file(second_path)
    upload_page.wait_for_upload_complete(second_name)

    filenames = upload_page.get_uploaded_filenames()
    assert second_name in filenames
    assert first_name not in filenames


def test_upload_same_file_twice(upload_page: UploadPage):
    """Повторная загрузка одного и того же файла (после того как первая
    загрузка полностью завершилась): сайт распознаёт точный дубликат
    (то же имя и содержимое) и не создаёт вторую запись — остаётся 1 чип."""
    path = VALID_FILES["pdf"]
    filename = path.split("/")[-1]

    upload_page.upload_file(path)
    upload_page.wait_for_upload_complete(filename)
    upload_page.upload_file(path)
    upload_page.page.wait_for_timeout(1500)

    assert upload_page.count_uploaded_chips(filename) == 1


def test_save_draft_offline_shows_false_success(upload_page: UploadPage):
    """Обрыв интернета во время сохранения: сама загрузка файла в карточку
    не зависит от сети (обработка идёт в браузере), поэтому здесь проверяется
    сетевая операция — сохранение черновика. При полностью отключённой сети
    приложение всё равно показывает тост "Черновик сохранен" — оно не
    отличает успешное сохранение на сервере от офлайн-состояния.
    Это находка, а не баг теста."""
    page = upload_page.page
    upload_page.upload_file(VALID_FILES["pdf"])

    page.context.set_offline(True)
    try:
        upload_page.save_draft()
        assert not upload_page.is_draft_saved_toast_visible(timeout=5_000), (
            "Тост 'Черновик сохранен' показался даже при отключённой сети — "
            "приложение не проверяет, что черновик реально сохранён на сервере"
        )
    finally:
        page.context.set_offline(False)

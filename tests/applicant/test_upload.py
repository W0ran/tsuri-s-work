from pathlib import Path

import pytest
from pages.applicant.upload_page import UploadPage
from utils.test_data_marker import make_test_application_name

VALID_FILES = {
    "pdf": "fixtures/applicant/sample_documents/sample.pdf",
    "png": "fixtures/applicant/sample_documents/sample.png",
    "jpeg": "fixtures/applicant/sample_documents/sample.jpg",
    "doc": "fixtures/applicant/sample_documents/sample.doc",
    "docx": "fixtures/applicant/sample_documents/sample.docx",
}

IMAGE_EXTENSIONS = {"png", "jpeg"}

INVALID_FILES = {
    "exe": "fixtures/applicant/invalid_documents/sample.exe",
    "zip": "fixtures/applicant/invalid_documents/sample.zip",
    "txt": "fixtures/applicant/invalid_documents/sample.txt",
}


def _card_for(file_type: str) -> str:
    return UploadPage.IMAGE_CARD_TITLE if file_type in IMAGE_EXTENSIONS else UploadPage.DOC_CARD_TITLE


def _name(path: str) -> str:
    return Path(path).name


@pytest.mark.parametrize("file_type,path", VALID_FILES.items())
def test_upload_valid_formats(upload_page: UploadPage, file_type, path):
    card = _card_for(file_type)
    unique_path = upload_page.make_unique_copy(path)
    upload_page.upload_file(unique_path)
    upload_page.wait_for_upload_complete(_name(unique_path), card_title=card)
    filenames = upload_page.get_uploaded_filenames(card_title=card)
    assert any(_name(unique_path) in f for f in filenames)


@pytest.mark.parametrize("file_type,path", INVALID_FILES.items())
def test_upload_invalid_formats_rejected(upload_page: UploadPage, file_type, path):
    upload_page.upload_file(path)
    assert upload_page.is_error_visible()


def test_upload_spoofed_extension_rejected(upload_page: UploadPage):
    spoofed_path = "fixtures/applicant/invalid_documents/fake_executable.pdf"  # содержимое — реальный exe
    upload_page.upload_file(spoofed_path)
    assert upload_page.is_error_visible()


def test_submit_without_files_blocked(application_params_page):
    """Precondition: РЕАЛЬНО новая заявка через wizard, без единого документа
    — не общий переиспользуемый черновик стенда, где документы накоплены
    за все прошлые прогоны и кнопка отправки была бы активна законно."""
    wizard = application_params_page
    wizard.fill_required_top_level_fields()

    marker_name = make_test_application_name()
    wizard.go_to_section("2. Сведения о ЛС")
    wizard.trade_name_field().fill(marker_name)

    wizard.go_to_documents_tab()
    upload_page = UploadPage(wizard.page)

    upload_page.go_to_review()
    assert not upload_page.is_submit_enabled(), (
        "Кнопка 'Отправить в экспертизу' активна на заведомо новой заявке "
        "без единого загруженного документа"
    )


def test_upload_multiple_files(upload_page: UploadPage):
    # оба файла одного формата (pdf, doc) — идут в одну карточку "Общая документация"
    paths = [
        upload_page.make_unique_copy(VALID_FILES["pdf"]),
        upload_page.make_unique_copy(VALID_FILES["doc"]),
    ]
    upload_page.upload_multiple(paths)
    for p in paths:
        upload_page.wait_for_upload_complete(_name(p))
    assert len(upload_page.get_uploaded_filenames()) >= 2


def test_delete_uploaded_file(upload_page: UploadPage):
    path = upload_page.make_unique_copy(VALID_FILES["pdf"])
    filename = _name(path)
    upload_page.upload_file(path)
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
    original_path = f"fixtures/applicant/sample_documents/{filename}"
    path = upload_page.make_unique_copy(original_path)
    upload_page.upload_file(path)
    upload_page.wait_for_upload_complete(_name(path), timeout=30_000)


def test_replace_uploaded_file(upload_page: UploadPage):
    """Замена одного файла другим: удаляем загруженный файл и загружаем на его
    место другой — старого не должно остаться, новый должен появиться."""
    first_path = upload_page.make_unique_copy(VALID_FILES["pdf"])
    second_path = upload_page.make_unique_copy(VALID_FILES["doc"])
    first_name = _name(first_path)
    second_name = _name(second_path)

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
    загрузка полностью завершилась): сайт НЕ проверяет дубликаты — оба
    экземпляра появляются как отдельные записи с одинаковым именем.

    Имя файла уникализировано один раз для этого прогона и переиспользуется
    для обеих загрузок — иначе результат смешивался бы с чужими "sample.pdf",
    накопленными в общей заявке за прошлые прогоны (на статичном имени этот
    тест ранее ошибочно показывал "дедуп до 1 чипа" — это был артефакт
    старых накопленных дублей, а не реальное поведение сайта)."""
    path = upload_page.make_unique_copy(VALID_FILES["pdf"])
    filename = _name(path)

    upload_page.upload_file(path)
    upload_page.wait_for_upload_complete(filename)
    upload_page.upload_file(path)
    upload_page.page.wait_for_timeout(1500)

    assert upload_page.count_uploaded_chips(filename) == 2


@pytest.mark.xfail(
    strict=True,
    reason=(
        "НАХОДКА: обрыв интернета во время сохранения: сама загрузка файла в "
        "карточку не зависит от сети (обработка идёт в браузере), поэтому "
        "здесь проверяется сетевая операция — сохранение черновика. При "
        "полностью отключённой сети приложение всё равно показывает тост "
        "'Черновик сохранен' — оно не отличает успешное сохранение на "
        "сервере от офлайн-состояния. Если тест вдруг пройдёт (XPASS), "
        "значит починили — маркер нужно убрать."
    ),
)
def test_save_draft_offline_shows_false_success(upload_page: UploadPage):
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

"""Тесты на глубокую проверку содержимого файлов (обновление валидации загрузки):
- реальная сигнатура файла вместо доверия расширению/MIME;
- блокировка PE/ELF, битых контейнеров, полиглотов, макросов/ActiveX;
- SHA-256 и статус антивируса фиксируются при успешной загрузке.

Файлы лежат в test-files/ (специально подготовленный QA-набор), не в fixtures/,
и не генерируются автоматически — они статичны и коммитятся в репозиторий.

Тест на ClamAV (EICAR) намеренно не реализован: локальный антивирус на машине
разработчика удаляет EICAR-файл с диска раньше, чем тест успевает его загрузить,
так что такой тест ненадёжен на обычной dev-машине.
"""

import pytest
from pages.applicant.upload_page import UploadPage

# (путь, ожидаемый HTTP-статус, ожидаемый код валидации)
REJECTED_FILES = {
    "exe_content_as_pdf": ("test-files/fake_executable.pdf", 415, "DANGEROUS_FILE_SIGNATURE"),
    "elf_content_as_jpeg": ("test-files/fake_elf.jpeg", 415, "DANGEROUS_FILE_SIGNATURE"),
    "corrupted_docx_container": ("test-files/fake_container.docx", 422, "INVALID_OFFICE_CONTAINER"),
    "corrupted_image_as_pdf": ("test-files/fake_script.pdf", 422, "INVALID_IMAGE_STRUCTURE"),
    "pdf_zip_polyglot": ("test-files/testfiles/tc9_polyglot_pdf_zip.pdf", 422, "AMBIGUOUS_FILE_FORMAT"),
    "pdf_zip_polyglot_v2": ("test-files/testfiles/tc9_polyglot_v2_pdf_zip.pdf", 422, "AMBIGUOUS_FILE_FORMAT"),
    "empty_file": ("test-files/testfiles/tc10_empty_file.pdf", 400, "EMPTY_FILE"),
    "pdf_signature_only": ("test-files/testfiles/tc11_sig_only.pdf", 422, "INVALID_PDF_STRUCTURE"),
    "docx_signature_only": ("test-files/testfiles/tc11_sig_only.docx", 422, "INVALID_OFFICE_CONTAINER"),
    "docx_macro_marker": ("test-files/testfiles/tc12_macro_marker.docx", 422, "INVALID_OFFICE_STRUCTURE"),
    "docx_macro_marker_v2": ("test-files/testfiles/tc12_macro_marker_v2.docx", 422, "OFFICE_ACTIVE_CONTENT"),
    "docx_nested_zipbomb": ("test-files/testfiles/tc13_nested_zipbomb.docx", 422, "INVALID_OFFICE_STRUCTURE"),
    "docx_nested_container": ("test-files/testfiles/tc14_nested_container.docx", 422, "INVALID_OFFICE_STRUCTURE"),
}

# (путь, ожидаемый detectedFormat)
ACCEPTED_FILES = {
    "valid_docx_double_extension": ("test-files/sixseven.pdf.docx", "docx"),
    "pdf_without_text_layer": ("test-files/testfiles/tc23_pdf_no_text_layer.pdf", "pdf"),
}


@pytest.mark.security
@pytest.mark.applicant
@pytest.mark.parametrize("case_id,params", REJECTED_FILES.items())
def test_dangerous_or_malformed_file_rejected(upload_page: UploadPage, case_id, params):
    path, expected_status, expected_code = params
    result = upload_page.upload_file_and_capture_response(path)
    assert result["status"] == expected_status, result
    assert result["body"]["code"] == expected_code, result


@pytest.mark.security
@pytest.mark.applicant
@pytest.mark.parametrize("case_id,params", ACCEPTED_FILES.items())
def test_valid_file_with_unusual_content_accepted(upload_page: UploadPage, case_id, params):
    path, expected_format = params
    result = upload_page.upload_file_and_capture_response(path)
    assert result["status"] == 200, result
    metadata = result["body"]["metadata"]
    assert metadata["validationStatus"] == "validated", result
    assert metadata["detectedFormat"] == expected_format, result
    assert metadata["antivirusStatus"] == "clean", result
    assert "sha256" in metadata and metadata["sha256"]


@pytest.mark.security
@pytest.mark.applicant
@pytest.mark.xfail(
    strict=True,
    reason=(
        "НАХОДКА: в отличие от tc13_nested_zipbomb.docx (v1, отклонён — но "
        "по общей причине 'битый контейнер', а не как zip bomb), структурно "
        "валидный tc13_nested_zipbomb_v2.docx с настоящей вложенной "
        "zip-бомбой проходит валидацию и принимается (200, validated). "
        "Похоже, защита от zip bomb не срабатывает для структурно корректных "
        "DOCX-контейнеров на этапе загрузки. Если тест вдруг пройдёт "
        "(XPASS), значит починили — маркер нужно убрать."
    ),
)
def test_nested_zipbomb_v2_should_be_rejected(upload_page: UploadPage):
    result = upload_page.upload_file_and_capture_response(
        "test-files/testfiles/tc13_nested_zipbomb_v2.docx"
    )
    assert result["status"] != 200, (
        "Файл с вложенной zip-бомбой (валидный DOCX-контейнер) был принят "
        f"сервером вместо отклонения: {result}"
    )

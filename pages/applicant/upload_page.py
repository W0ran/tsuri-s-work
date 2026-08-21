import tempfile
import uuid
from pathlib import Path

from playwright.sync_api import Page, Locator, expect
from pages.common.base_page import BasePage


class UploadPage(BasePage):
    """Вкладка "Документы" мастера заявки: чек-лист из ~94 обязательных типов
    документов, каждый — отдельная карточка (data-slot="card") со своим
    input[type=file] и своим набором допустимых расширений (accept).

    Для тестов используются две фиксированные, всегда присутствующие на первом
    экране карточки:
      - "Общая документация" — Форматы: pdf, doc, docx
      - "Цветные макеты ..." (1.3.5) — Форматы: jpg, jpeg, png
    Любое расширение вне этих двух наборов (exe, zip, txt и т.п.) отправляется
    в карточку "Общая документация", чтобы проверить, что сайт его отклонит.
    """

    SUBMIT_BUTTON_TEXT = "Отправить в экспертизу"
    SAVE_DRAFT_BUTTON_TEXT = "Сохранить черновик"
    DRAFT_SAVED_TOAST_TEXT = "Черновик сохранен"

    DOC_CARD_TITLE = "Общая документация"
    IMAGE_CARD_TITLE = (
        "Цветные макеты потребительских упаковок, этикеток, стикеров в "
        "электронном виде в формате jpeg (джипег) в масштабе 1:1"
    )

    EXTENSION_TO_CARD = {
        "pdf": DOC_CARD_TITLE,
        "doc": DOC_CARD_TITLE,
        "docx": DOC_CARD_TITLE,
        "jpg": IMAGE_CARD_TITLE,
        "jpeg": IMAGE_CARD_TITLE,
        "png": IMAGE_CARD_TITLE,
    }

    def make_unique_copy(self, file_path: str) -> str:
        """Копия файла с уникальным именем (короткий uuid-префикс).

        Карточка документа копит файлы за все прошлые прогоны тестов (общая,
        переиспользуемая заявка на стенде), поэтому проверки по точному имени
        файла ("есть ли sample.pdf в списке") без уникализации ловят чужие
        записи из прошлых запусков, а не только результат текущего теста."""
        src = Path(file_path)
        unique_name = f"{uuid.uuid4().hex[:8]}_{src.name}"
        tmp_dir = Path(tempfile.gettempdir()) / "qa_upload_unique"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        dst = tmp_dir / unique_name
        dst.write_bytes(src.read_bytes())
        return str(dst)

    def _card(self, title: str) -> Locator:
        return self.page.locator(
            "xpath=//div[@data-slot='card-title']"
            f"[normalize-space(text())={_xpath_literal(title)}]"
            "/ancestor::*[@data-slot='card'][1]"
        )

    def _card_for_extension(self, file_path: str) -> Locator:
        ext = file_path.rsplit(".", 1)[-1].lower()
        title = self.EXTENSION_TO_CARD.get(ext, self.DOC_CARD_TITLE)
        return self._card(title)

    def upload_file(self, file_path: str) -> None:
        card = self._card_for_extension(file_path)
        card.locator("input[type='file']").set_input_files(file_path)

    def upload_file_and_capture_response(self, file_path: str, timeout: int = 20_000) -> dict:
        """Загружает файл и возвращает статус и тело ответа POST /api/files —
        сервер теперь отдаёт структурированные коды валидации
        (DANGEROUS_FILE_SIGNATURE, AMBIGUOUS_FILE_FORMAT и т.д.), это надёжнее,
        чем парсить текст ошибки в UI."""
        card = self._card_for_extension(file_path)
        input_ = card.locator("input[type='file']")
        with self.page.expect_response(
            lambda r: "/api/files" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as resp_info:
            input_.set_input_files(file_path)
        response = resp_info.value
        try:
            body = response.json()
        except Exception:
            body = None
        return {"status": response.status, "body": body}

    def upload_multiple(self, file_paths: list[str]) -> None:
        card = self._card_for_extension(file_paths[0])
        card.locator("input[type='file']").set_input_files(file_paths)

    def upload_all_required_documents(self) -> int:
        """Закрывает все обязательные карточки документов на вкладке
        "Документы" валидными файлами — нужно, чтобы разблокировать реальную
        подачу заявки. Карточки-обёртки разделов и альтернативный загрузчик
        "досье целиком" отличаются от карточек одного типа документа именно
        числом input[type=file] (не 1) — по этому признаку и фильтруем,
        т.к. заголовки карточек слишком длинные/неединообразные для матчинга
        по тексту."""
        cards = self.page.locator("[data-slot='card']").all()
        filled = 0
        for card in cards:
            file_inputs = card.locator("input[type='file']")
            if file_inputs.count() != 1:
                continue
            accept = file_inputs.first.get_attribute("accept") or ""
            if "pdf" in accept:
                src = "fixtures/applicant/sample_documents/sample.pdf"
            elif "jpg" in accept or "jpeg" in accept or "png" in accept:
                src = "fixtures/applicant/sample_documents/sample.jpg"
            else:
                continue
            unique_path = self.make_unique_copy(src)
            unique_name = Path(unique_path).name
            file_inputs.first.set_input_files(unique_path)
            # некоторые карточки (сильно накопившие файлы за прошлые прогоны)
            # рендерят ДВА [data-slot='card-content'] (внешний с усечённым
            # описанием + внутренний со списком файлов) — bare-локатор ловит
            # "strict mode violation"; используем тот же точный паттерн
            # "строка одного файла", что и _uploaded_chip/wait_for_upload_complete
            expect(
                card.locator("[data-slot='card-content'] > div").filter(
                    has=self.page.get_by_text(unique_name, exact=True)
                )
            ).to_be_visible(timeout=60_000)
            filled += 1
        return filled

    def _uploaded_chip(self, card: Locator, filename: str) -> Locator:
        """Строка одного конкретного загруженного файла.

        Каждый файл — прямой div-потомок контейнера card-content (класс
        "space-y-2"), без собственного data-slot; строк может быть много
        (карточка копит файлы за все прошлые загрузки). Матчим по точному
        тексту span.truncate с именем файла, а не просто has_text на всём
        контейнере — иначе .locator("button") цепляет случайную/первую
        кнопку среди множества файлов, а не нужную."""
        return card.locator("[data-slot='card-content'] > div").filter(
            has=self.page.get_by_text(filename, exact=True)
        )

    def get_uploaded_filenames(self, card_title: str = DOC_CARD_TITLE) -> list[str]:
        card = self._card(card_title)
        return card.locator("[data-slot='card-content'] span.truncate").all_inner_texts()

    def is_error_visible(self, card_title: str = DOC_CARD_TITLE, timeout: int = 10_000) -> bool:
        # валидация файла на сервере занимает время — снимок .is_visible()
        # без ожидания часто ловит момент ДО отрисовки ошибки (ложный False)
        card = self._card(card_title)
        try:
            expect(
                card.locator("[data-slot='card-content'] .text-destructive")
            ).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

    def get_error_text(self, card_title: str = DOC_CARD_TITLE) -> str:
        card = self._card(card_title)
        locator = card.locator("[data-slot='card-content'] .text-destructive")
        expect(locator).to_be_visible(timeout=10_000)
        return locator.inner_text()

    def delete_uploaded_file(self, filename: str, card_title: str = DOC_CARD_TITLE) -> None:
        card = self._card(card_title)
        self._uploaded_chip(card, filename).locator("button").click()

    def wait_for_upload_complete(
        self, filename: str, card_title: str = DOC_CARD_TITLE, timeout: int = 60_000
    ) -> None:
        card = self._card(card_title)
        expect(self._uploaded_chip(card, filename)).to_be_visible(timeout=timeout)

    def count_uploaded_chips(self, filename: str, card_title: str = DOC_CARD_TITLE) -> int:
        card = self._card(card_title)
        return self._uploaded_chip(card, filename).count()

    def go_to_review(self) -> None:
        self.page.get_by_role("button", name="Проверка", exact=False).click()
        self.page.wait_for_load_state("networkidle")

    def is_submit_enabled(self) -> bool:
        return self.page.get_by_role(
            "button", name=self.SUBMIT_BUTTON_TEXT, exact=True
        ).is_enabled()

    def save_draft(self) -> None:
        self.page.get_by_role("button", name=self.SAVE_DRAFT_BUTTON_TEXT).click()

    def is_draft_saved_toast_visible(self, timeout: int = 5_000) -> bool:
        try:
            expect(self.page.get_by_text(self.DRAFT_SAVED_TOAST_TEXT)).to_be_visible(
                timeout=timeout
            )
            return True
        except AssertionError:
            return False


def _xpath_literal(value: str) -> str:
    """Безопасно оборачивает строку в XPath-литерал, даже если она содержит кавычки."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

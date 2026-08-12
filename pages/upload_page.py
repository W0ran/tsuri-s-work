from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage


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

    def upload_multiple(self, file_paths: list[str]) -> None:
        card = self._card_for_extension(file_paths[0])
        card.locator("input[type='file']").set_input_files(file_paths)

    def _uploaded_chip(self, card: Locator, filename: str) -> Locator:
        return card.locator("[data-slot='card-content']").filter(has_text=filename)

    def get_uploaded_filenames(self, card_title: str = DOC_CARD_TITLE) -> list[str]:
        card = self._card(card_title)
        return card.locator("[data-slot='card-content'] span.truncate").all_inner_texts()

    def is_error_visible(self, card_title: str = DOC_CARD_TITLE) -> bool:
        card = self._card(card_title)
        return card.locator("[data-slot='card-content'] .text-destructive").is_visible()

    def get_error_text(self, card_title: str = DOC_CARD_TITLE) -> str:
        card = self._card(card_title)
        return card.locator("[data-slot='card-content'] .text-destructive").inner_text()

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

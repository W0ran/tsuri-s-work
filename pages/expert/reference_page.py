from playwright.sync_api import Page, Locator
from pages.common.shell_page import ShellPage


class ReferencePage(ShellPage):
    """Умный справочник НПА (/reference) — таблица из 38 обработанных
    нормативных документов с поиском и фильтром по области (Все/ЛС/МИ).

    Каждая строка данных — реальный <tr>, но с атрибутом role="button"
    (кликабельна целиком, в отличие от ExpertPage, где строки — обычные
    <tr> без этого атрибута). Строка-заглушка "Ничего не найдено" рендерится
    как <tr> БЕЗ role="button", поэтому фильтр по этому атрибуту при пустом
    результате поиска корректно даёт row_count() == 0 — специальной
    обработки, в отличие от ExpertPage.no_results_message, не требуется.

    Клик по строке открывает детальную карточку документа НА ТОЙ ЖЕ
    странице (URL остаётся /reference) — см. ReferenceDocumentPanel."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Умный справочник НПА")
        self.admin_link = page.get_by_role("link", name="В админку")
        self.search_input = page.get_by_placeholder("Поиск по НПА ядра MVP")
        self.filter_all_button = page.get_by_role("button", name="Все", exact=True)
        self.filter_ls_button = page.get_by_role("button", name="ЛС", exact=True)
        self.filter_mi_button = page.get_by_role("button", name="МИ", exact=True)
        self.rows = page.get_by_role("table").locator("tbody tr[role='button']")

    def open(self, base_url: str) -> None:
        self.goto(f"{base_url}/reference")

    def metric_value(self, label: str) -> str:
        return self._value_after_label(label)

    def search(self, query: str) -> None:
        self.search_input.fill(query)

    def row_count(self) -> int:
        return self.rows.count()

    def row_by_title(self, title: str) -> Locator:
        return self.rows.filter(has_text=title)

    def open_document(self, row_index: int = 0) -> "ReferenceDocumentPanel":
        from pages.expert.reference_document_panel import ReferenceDocumentPanel

        self.rows.nth(row_index).click()
        return ReferenceDocumentPanel(self.page)

    def open_document_by_title(self, title: str) -> "ReferenceDocumentPanel":
        from pages.expert.reference_document_panel import ReferenceDocumentPanel

        self.row_by_title(title).click()
        return ReferenceDocumentPanel(self.page)

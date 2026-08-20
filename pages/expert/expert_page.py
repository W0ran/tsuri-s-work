from playwright.sync_api import Page, Locator
from pages.common.shell_page import ShellPage


class ExpertPage(ShellPage):
    """Кабинет эксперта (/expert) — список заявок, KPI-плашки, поиск/фильтры
    и переходы в очередь этапов или в досье конкретной заявки.

    Строки таблицы — обычные <tr> (columnheader/row в дереве доступности).
    При поиске без совпадений таблица не пустеет до 0 строк — вместо этого
    рендерится одна строка-заглушка с текстом no_results_message."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Кабинет эксперта")
        self.workflow_link = page.get_by_role("link", name="Очередь этапов")
        self.search_input = page.get_by_placeholder("Поиск по препарату, МНН, заявителю")
        # role="combobox" не поддерживает accessible name из текста содержимого
        # (не входит в name-from-content роли ARIA) — get_by_role(..., name=...)
        # для них всегда возвращает 0 совпадений, поэтому берём по порядку в DOM
        combo_triggers = page.locator("button[role='combobox']")
        self.status_filter = combo_triggers.nth(0)
        self.result_filter = combo_triggers.nth(1)
        self.rows = page.get_by_role("table").locator("tbody tr")
        self.no_results_message = page.get_by_text("Заявки по выбранным фильтрам не найдены.")

    def open(self, base_url: str) -> None:
        self.goto(f"{base_url}/expert")

    def kpi_value(self, label: str) -> str:
        """KPI-плашка — кликабельная кнопка с двумя <p>: сначала подпись
        ("Всего заявок"), потом число."""
        return self._value_after_label(label)

    def filter_by_kpi(self, label: str) -> None:
        self.page.get_by_role("button").filter(has=self.page.get_by_text(label, exact=True)).click()

    def search(self, query: str) -> None:
        self.search_input.fill(query)

    def row_count(self) -> int:
        return self.rows.count()

    def row_by_drug(self, drug_name: str) -> Locator:
        return self.rows.filter(has_text=drug_name)

    def open_application(self, drug_name: str) -> "ApplicationPage":
        from pages.expert.application_page import ApplicationPage

        self.row_by_drug(drug_name).get_by_role("link", name="Открыть").click()
        return ApplicationPage(self.page)

    def open_first_application(self) -> "ApplicationPage":
        from pages.expert.application_page import ApplicationPage

        self.rows.first.get_by_role("link", name="Открыть").click()
        return ApplicationPage(self.page)

    def go_to_workflow(self) -> "WorkflowPage":
        from pages.expert.workflow_page import WorkflowPage

        self.workflow_link.click()
        return WorkflowPage(self.page)

from playwright.sync_api import Page, Locator
from pages.common.shell_page import ShellPage


class WorkflowPage(ShellPage):
    """Очередь экспертизы (/expert/workflow) — дела эксперта на текущем
    этапе. Кнопка "Открыть дело" в строке не переходит на отдельный URL —
    она открывает модалку CaseDialog с быстрыми действиями по этапу."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.back_link = page.get_by_role("link", name="К заявкам")
        self.heading = page.get_by_role("heading", name="Очередь экспертизы")
        # role="combobox" не поддерживает accessible name из текста содержимого
        # (см. комментарий в ExpertPage) — берём единственный комбобокс на странице
        self.stage_filter = page.locator("button[role='combobox']").first
        self.refresh_button = page.get_by_role("button", name="Обновить")
        self.rows = page.get_by_role("table").locator("tbody tr")

    def open(self, base_url: str) -> None:
        self.goto(f"{base_url}/expert/workflow")

    def kpi_value(self, label: str) -> str:
        """KPI-плашка здесь — div с числом ПЕРЕД подписью (обратный порядок
        относительно KPI-кнопок на /expert)."""
        return self._value_before_label(label)

    def row_count(self) -> int:
        return self.rows.count()

    def row_by_drug(self, drug_name: str) -> Locator:
        return self.rows.filter(has_text=drug_name)

    def open_case(self, drug_name: str) -> "CaseDialog":
        from pages.expert.case_dialog import CaseDialog

        self.row_by_drug(drug_name).get_by_role("button", name="Открыть дело").click()
        return CaseDialog(self.page)

    def open_first_case(self) -> "CaseDialog":
        from pages.expert.case_dialog import CaseDialog

        self.rows.first.get_by_role("button", name="Открыть дело").click()
        return CaseDialog(self.page)

    def back_to_applications(self) -> "ExpertPage":
        from pages.expert.expert_page import ExpertPage

        self.back_link.click()
        return ExpertPage(self.page)

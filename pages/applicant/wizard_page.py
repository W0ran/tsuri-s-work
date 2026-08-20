from playwright.sync_api import Page
from pages.common.base_page import BasePage


class WizardPage(BasePage):
    """Мастер создания заявки (/wizard): выбор критериев -> вкладка "Документы"."""

    CRITERIA_SELECT_IDS = [
        "param-object-type",
        "param-procedure",
        "param-manufacturer-country",
        "param-dossier-type",
        "param-expertise-mode",
    ]

    def __init__(self, page: Page):
        super().__init__(page)
        self.create_application_link = page.get_by_role("link", name="Создать заявку")
        self.documents_tab = page.get_by_role("button", name="Документы")

    def open_new_application(self) -> None:
        self.create_application_link.click()
        self.page.wait_for_load_state("networkidle")

    def select_default_criteria(self) -> None:
        """Выбирает первый доступный вариант в каждом из 5 select'ов шага "Критерии"."""
        for select_id in self.CRITERIA_SELECT_IDS:
            trigger = self.page.locator(f"#{select_id}")
            trigger.click()
            self.page.get_by_role("option").first.click()

    def go_to_documents_tab(self) -> None:
        self.documents_tab.click()
        self.page.wait_for_timeout(500)

    def start_new_application_and_reach_documents(self) -> None:
        self.open_new_application()
        self.select_default_criteria()
        self.go_to_documents_tab()

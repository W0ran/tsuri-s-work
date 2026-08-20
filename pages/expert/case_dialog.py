from playwright.sync_api import Page
from pages.common.base_page import BasePage


class CaseDialog(BasePage):
    """Модалка дела, открываемая кнопкой "Открыть дело" в очереди
    (/expert/workflow) — быстрые действия по текущему этапу (назначение,
    запрос заявителю, направление в лабораторию/на инспекцию, завершение
    этапа) и маршрут заявки, без перехода в полное досье."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.dialog = page.get_by_role("dialog")
        self.heading = self.dialog.get_by_role("heading").first
        self.open_application_link = self.dialog.get_by_role("link", name="Открыть заявку")
        self.assign_to_me_button = self.dialog.get_by_role("button", name="Назначить мне")
        self.request_applicant_button = self.dialog.get_by_role("button", name="Запрос заявителю")
        self.send_to_lab_button = self.dialog.get_by_role("button", name="Направить в лабораторию")
        self.send_to_inspection_button = self.dialog.get_by_role("button", name="Направить на инспекцию")
        self.complete_stage_button = self.dialog.get_by_role("button", name="Завершить этап")
        self.close_button = self.dialog.get_by_role("button", name="Close")

    def open_application(self) -> "ApplicationPage":
        from pages.expert.application_page import ApplicationPage

        self.open_application_link.click()
        return ApplicationPage(self.page)

    def close(self) -> None:
        self.close_button.click()

from playwright.sync_api import Page
from pages.common.shell_page import ShellPage


class ApplicationsListPage(ShellPage):
    """Страница "Мои заявки" (/applicant) — список заявок заявителя после входа."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.my_applications_link = page.get_by_role("link", name="Мои заявки")
        self.create_application_link = page.get_by_role("link", name="Создать заявку")
        self.chat_link = page.get_by_role("link", name="Чат")
        self.user_badge = page.get_by_text("Заявитель (демо)")
        self.page_heading = page.get_by_role("heading", name="Мои заявки")
        self.create_application_button = page.get_by_role("button", name="Создать заявку")

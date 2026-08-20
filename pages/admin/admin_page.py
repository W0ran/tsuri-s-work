from playwright.sync_api import Page
from pages.common.shell_page import ShellPage


class AdminPage(ShellPage):
    """Панель администратора (/admin) — полный доступ.

    TODO: UI ещё не разведан — добавить реальные локаторы после сессии
    playwright codegen под учёткой admin.
    """

    def __init__(self, page: Page):
        super().__init__(page)

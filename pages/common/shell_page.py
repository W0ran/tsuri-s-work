from playwright.sync_api import Page
from pages.common.base_page import BasePage


class ShellPage(BasePage):
    """Общая "рамка" сайта после входа — то, что видно у ЛЮБОЙ роли:
    кнопка выхода, переключатели темы и языка.

    Ролевые Page Object'ы (ApplicationsListPage, ExpertPage и т.д.) могут
    наследоваться от этого класса, чтобы не дублировать общий код навигации.

    TODO: локаторы theme_toggle / language_toggle — предположение по тексту
    кнопок ("Тема"), реальный UI переключателей ещё не разведан (не было
    скриншота открытого меню). Сверить через playwright codegen и поправить
    перед тем, как включать test_theme_switch.py / test_language_switch.py.
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self.logout_button = page.get_by_role("button", name="Выйти")
        self.theme_toggle = page.get_by_role("button", name="Тема")
        self.language_toggle = page.get_by_role("button", name="Язык")

    def logout(self) -> None:
        self.logout_button.click()

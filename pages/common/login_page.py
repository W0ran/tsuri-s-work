from playwright.sync_api import Page, expect
from pages.common.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_text("AI эксперт — вход")
        self.login_input = page.get_by_label("Логин")
        self.password_input = page.get_by_label("Пароль")
        self.submit_button = page.get_by_role("button", name="Войти")
        self.error_message = page.get_by_text("Неверный логин или пароль")

    def open(self, base_url: str) -> None:
        self.goto(f"{base_url}/login")

    def login(self, login: str, password: str) -> None:
        self.login_input.fill(login)
        self.password_input.fill(password)
        self.submit_button.click()

    def is_error_visible(self, timeout: int = 10_000) -> bool:
        # ответ сервера на попытку логина занимает время — ждём появления
        # сообщения об ошибке, а не снимаем мгновенное is_visible()
        try:
            expect(self.error_message).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

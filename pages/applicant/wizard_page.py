from playwright.sync_api import Page, Locator
from pages.common.base_page import BasePage


class WizardPage(BasePage):
    """Мастер создания заявки (/wizard): выбор критериев -> вкладка "Документы".

    Раздел "Параметры" (шаг 1 из 3) сразу после выбора критериев показывает
    подраздел "1. Основное" (Заявитель, Держатель, Производитель и т.д.).
    Остальные подразделы (2. Сведения о ЛС и далее) открываются кнопками
    сайдбара с текстом вида "2. Сведения о ЛС" и подгружают свои поля."""

    CRITERIA_SELECT_IDS = [
        "param-object-type",
        "param-procedure",
        "param-manufacturer-country",
        "param-dossier-type",
        "param-expertise-mode",
    ]

    APPLICANT_FIELD_ID = "param-applicant"
    MANUFACTURER_FIELD_ID = "param-manufacturer"
    MANUFACTURER_ADDRESS_FIELD_ID = "param-manufacturer-address"
    TRADE_NAME_RU_FIELD_ID = "param-trade-name-ru"
    SAVE_DRAFT_BUTTON_TEXT = "Сохранить черновик"
    SUBMIT_TEST_COPY_BUTTON_TEXT = "Создать тестовую копию и отправить в экспертизу"

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

    def go_to_section(self, section_name: str) -> None:
        """Переключает подраздел внутри "Параметры", например "2. Сведения о ЛС"."""
        self.page.get_by_role("button", name=section_name, exact=False).click()
        self.page.wait_for_timeout(500)

    def manufacturer_field(self) -> Locator:
        return self.page.locator(f"#{self.MANUFACTURER_FIELD_ID}")

    def trade_name_field(self) -> Locator:
        return self.page.locator(f"#{self.TRADE_NAME_RU_FIELD_ID}")

    def save_draft_button(self) -> Locator:
        return self.page.get_by_role("button", name=self.SAVE_DRAFT_BUTTON_TEXT)

    def save_draft(self) -> None:
        self.save_draft_button().click()
        self.page.wait_for_timeout(800)

    def fill_required_top_level_fields(
        self,
        applicant: str = "QA Test Applicant LLP",
        manufacturer: str = "QA Test Manufacturer LLP",
        manufacturer_address: str = "QA Test Address 1",
    ) -> None:
        """Заполняет обязательные (отмечены *) поля подраздела "1. Основное",
        открытого по умолчанию сразу после выбора критериев."""
        self.page.locator(f"#{self.APPLICANT_FIELD_ID}").fill(applicant)
        self.page.locator(f"#{self.MANUFACTURER_FIELD_ID}").fill(manufacturer)
        self.page.locator(f"#{self.MANUFACTURER_ADDRESS_FIELD_ID}").fill(manufacturer_address)

    def submit_test_copy(self) -> dict:
        """Кнопка "Создать тестовую копию и отправить в экспертизу" — обходит
        незакрытые критичные/серьёзные замечания (в отличие от обычной
        "Отправить в экспертизу"), предназначена именно для тестирования.
        Возвращает распарсенное тело ответа POST .../test-submit."""
        btn = self.page.get_by_role("button", name=self.SUBMIT_TEST_COPY_BUTTON_TEXT)
        with self.page.expect_response(
            lambda r: "/test-submit" in r.url and r.request.method == "POST"
        ) as resp_info:
            btn.click()
        return resp_info.value.json()

    def start_new_application_and_reach_documents(self) -> None:
        self.open_new_application()
        self.select_default_criteria()
        self.go_to_documents_tab()

from playwright.sync_api import Page, Locator
from pages.common.base_page import BasePage


class ReferenceDocumentPanel(BasePage):
    """Детальная карточка одного НПА, открытая из ReferencePage (URL
    остаётся /reference — переключение вида на клиенте, не отдельный роут).

    Вкладка "Требования" разведана подробно (таблица с 10 колонками:
    №, Требование, Описание, Документ, Процедура, Условие, Критичность,
    Почему важно, Пункт, Цитата). Остальные 5 вкладок (Типы документов,
    Параметры, Зависимости, Проверки, Полный текст) пока используются
    только через open_tab() — их внутренняя разметка не разведана."""

    TABS = [
        "Требования",
        "Типы документов",
        "Параметры",
        "Зависимости",
        "Проверки",
        "Полный текст",
    ]

    def __init__(self, page: Page):
        super().__init__(page)
        self.back_button = page.get_by_role("button", name="Назад к таблице")
        # role="tabpanel" не поддерживает accessible name из текста содержимого,
        # но Radix Tabs монтирует в DOM только активную панель — единственный
        # tabpanel на странице достаточен, пока открыта вкладка "Требования"
        # (открыта по умолчанию при первом рендере карточки документа)
        self.requirements_table = page.get_by_role("tabpanel").get_by_role("table")

    def tab(self, name: str) -> Locator:
        return self.page.get_by_role("tab", name=name, exact=False)

    def open_tab(self, name: str) -> None:
        self.tab(name).click()

    def active_tab_name(self) -> str:
        return self.page.get_by_role("tab", selected=True).inner_text()

    def requirement_rows(self) -> Locator:
        return self.requirements_table.locator("tbody tr")

    def back_to_table(self) -> "ReferencePage":
        from pages.expert.reference_page import ReferencePage

        self.back_button.click()
        return ReferencePage(self.page)

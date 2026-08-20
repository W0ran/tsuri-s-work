from playwright.sync_api import Page, Locator
from pages.common.shell_page import ShellPage


class ApplicationPage(ShellPage):
    """Досье заявки на стороне эксперта (/expert/{id}).

    Вкладка "Замечания" открыта по умолчанию и разведана подробно (поиск,
    суб-фильтры с счётчиками, таблица замечаний). Остальные вкладки
    (Документы, Параметры, Досье, Заключение) пока используются только через
    open_tab() — их внутренняя разметка не разведана."""

    TABS = ["Замечания", "Документы", "Параметры", "Досье", "Заключение"]
    REMARK_FILTERS = ["Требуют внимания", "Кандидаты", "В заключении", "Снятые"]

    def __init__(self, page: Page):
        super().__init__(page)
        self.back_link = page.get_by_role("link", name="К списку заявок")
        self.heading = page.get_by_role("heading", level=1)
        self.take_in_work_button = page.get_by_role("button", name="Взять в работу")
        self.remarks_search = page.get_by_placeholder("Найти замечание")
        self.remarks_table = page.get_by_role("table")
        # tabpanel не пропадает даже когда выбранный суб-фильтр не даёт
        # результатов — в этом случае <table> заменяется текстом "По
        # выбранному фильтру записей нет" внутри той же панели
        self.remarks_panel = page.get_by_role("tabpanel")

    def tab(self, name: str) -> Locator:
        return self.page.get_by_role("tab", name=name, exact=False)

    def open_tab(self, name: str) -> None:
        self.tab(name).click()

    def active_tab_name(self) -> str:
        return self.page.get_by_role("tab", selected=True).inner_text()

    def remark_filter_button(self, label: str) -> Locator:
        return self.page.get_by_role("button", name=label, exact=False)

    def select_remark_filter(self, label: str) -> None:
        self.remark_filter_button(label).click()

    def remark_count_in_filter(self, label: str) -> int:
        """Число в скобках у кнопки-фильтра ("Требуют внимания 9" -> 9)."""
        text = self.remark_filter_button(label).inner_text()
        return int(text.strip().split()[-1])

    def search_remarks(self, query: str) -> None:
        self.remarks_search.fill(query)

    def remark_rows(self) -> Locator:
        return self.remarks_table.locator("tbody tr")

    def back_to_list(self) -> "ExpertPage":
        from pages.expert.expert_page import ExpertPage

        self.back_link.click()
        return ExpertPage(self.page)

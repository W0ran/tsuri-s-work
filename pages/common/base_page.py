from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str) -> None:
        # без ожидания networkidle таблицы/KPI-плашки на страницах эксперта
        # (/expert, /expert/workflow, /reference) читаются раньше, чем клиент
        # успевает подгрузить данные асинхронным запросом после навигации —
        # это гонка (например, KPI ещё показывает дефолтный "0", а таблица
        # уже отрисовала первую реальную строку)
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

    def _value_after_label(self, label: str) -> str:
        """Для метрик-плашек вида <p>Подпись</p><p>Значение</p> (например,
        KPI на /expert или счётчики документов на /reference) — значение
        сразу после точного текста подписи."""
        return (
            self.page.get_by_text(label, exact=True)
            .locator("xpath=following-sibling::*[1]")
            .inner_text()
        )

    def _value_before_label(self, label: str) -> str:
        """Для метрик-плашек вида <div>Значение</div><div>Подпись</div>
        (например, KPI очереди на /expert/workflow) — значение сразу перед
        точным текстом подписи (обратный, по сравнению с _value_after_label,
        порядок в разметке)."""
        return (
            self.page.get_by_text(label, exact=True)
            .locator("xpath=preceding-sibling::*[1]")
            .inner_text()
        )

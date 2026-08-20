from playwright.sync_api import Page, Locator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.common.shell_page import ShellPage


class CouncilPage(ShellPage):
    """Специализированная комиссия (/council) — общая страница для ролей
    predsedatel и sovet_tsuri: список разногласий экспертов с результатами
    ИИ, поступивших на рассмотрение комиссии. Обе роли после логина
    попадают на "/", а не сюда — сюда ведёт единственный пункт сайдбара
    "Специализированная комиссия".

    Строки — реальные <tr role="link"> (кликабельны целиком, без вложенной
    <a>), как и строки-документы на /reference (см. ReferencePage)."""

    STATUSES = ["Ожидает рассмотрения", "Подтверждён", "Отклонён"]

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.locator("main").get_by_text("Специализированная комиссия", exact=True)
        self.rows = page.get_by_role("table").locator("tbody tr[role='link']")

    def open(self, base_url: str) -> None:
        self.goto(f"{base_url}/council")

    def filter_by_status(self, status: str) -> None:
        # без ожидания networkidle row_count()/open_review(), вызванные сразу
        # после переключения фильтра, ловят гонку: либо ещё не обновившийся
        # список от предыдущего фильтра, либо промежуточное пустое состояние
        self.page.get_by_role("button", name=status, exact=True).click()
        self.page.wait_for_load_state("networkidle")

    def row_count(self) -> int:
        return self.rows.count()

    def row_by_application_code(self, code: str) -> Locator:
        return self.rows.filter(has_text=code)

    def open_review(self, row_index: int = 0) -> "CouncilReviewPage":
        from pages.common.council_review_page import CouncilReviewPage

        # список рассмотрений периодически перерисовывается (фоновый
        # refetch) — строка иногда отсоединяется от DOM прямо во время
        # клика ("element was detached, retrying") и Playwright не всегда
        # укладывается в дефолтный таймаут одной попытки, поэтому кликаем
        # с ручным повтором на TimeoutError
        last_error = None
        for _ in range(3):
            try:
                self.rows.nth(row_index).click(timeout=10_000)
                last_error = None
                break
            except PlaywrightTimeoutError as e:
                last_error = e
        if last_error is not None:
            raise last_error

        # переход клиентский (SPA-роутинг), контент подгружается асинхронно —
        # без этого ожидания is_decided() (использует мгновенный is_visible(),
        # без авто-retry в отличие от expect()) читает страницу раньше, чем
        # успевает отрисоваться блок "Итоговое решение"
        self.page.wait_for_load_state("networkidle")
        return CouncilReviewPage(self.page)

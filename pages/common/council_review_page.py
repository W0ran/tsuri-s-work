from playwright.sync_api import Page, expect
from pages.common.shell_page import ShellPage


class CouncilReviewPage(ShellPage):
    """Карточка одного рассмотрения (/council/{id}): информация о заявке,
    ответ ИИ, комментарий эксперта (несогласие), голоса членов комиссии и
    финальный блок решения.

    Финальный блок зависит от роли и от того, вынесено ли уже решение:
      - пока статус "Ожидает рассмотрения":
        - predsedatel видит интерактивную форму "Итоговое решение
          (Председатель комиссии)" — decision_comment_input +
          confirm_decision_button/reject_decision_button;
        - sovet_tsuri видит форму "Ваш голос (Член комиссии)" —
          vote_comment_input + confirm_vote_button/reject_vote_button.
      - как только решение вынесено, обеим ролям показывается один и тот же
        read-only блок "Итоговое решение" с записью
        "Председатель комиссии: {email} · {дата}" — см. is_decided().

    ВАЖНО: confirm/reject-кнопки необратимо меняют статус реального
    рассмотрения на дев-стенде (общие данные, не изолированные под тест) —
    методы клика по ним намеренно не вызываются из автотестов, только
    описаны для ручного/будущего использования на заведомо тестовых данных."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.back_link = page.get_by_role("link", name="К списку")
        self.application_link = page.locator("a[href^='/expert/']").first
        self.ai_response_heading = page.get_by_text("Ответ ИИ", exact=True)
        self.expert_comment_heading = page.get_by_text("Комментарий эксперта (несогласие)", exact=True)
        self.votes_heading = page.get_by_text("Голоса членов комиссии", exact=False)

        # председатель: интерактивная форма итогового решения
        self.decision_comment_input = page.get_by_placeholder("Итоговый комментарий (опц.)")
        self.confirm_decision_button = page.get_by_role("button", name="Подтвердить комментарий")
        self.reject_decision_button = page.get_by_role("button", name="Отклонить комментарий")

        # член комиссии: форма голосования
        self.vote_comment_input = page.get_by_placeholder("Комментарий к голосу (опц.)")
        self.confirm_vote_button = page.get_by_role("button", name="За подтверждение")
        self.reject_vote_button = page.get_by_role("button", name="За отклонение")

        # read-only запись — видна обеим ролям, когда решение уже вынесено
        self.final_decision_record = page.get_by_text("Председатель комиссии:", exact=False)

    def open_url(self, base_url: str, review_id: str) -> None:
        self.goto(f"{base_url}/council/{review_id}")

    def is_decided(self) -> bool:
        # запись "Председатель комиссии: ..." подгружается отдельным запросом
        # уже после networkidle основного контента — мгновенный is_visible()
        # ловит гонку, поэтому ждём появления (как в LoginPage.is_error_visible)
        try:
            expect(self.final_decision_record).to_be_visible(timeout=10_000)
            return True
        except AssertionError:
            return False

    def back_to_list(self) -> "CouncilPage":
        from pages.common.council_page import CouncilPage

        self.back_link.click()
        return CouncilPage(self.page)

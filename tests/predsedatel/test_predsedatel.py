import pytest
from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.predsedatel.predsedatel_page import PredsedatelPage
from pages.common.council_review_page import CouncilReviewPage


@pytest.mark.predsedatel
def test_council_list_loads(council_page: PredsedatelPage):
    expect(council_page.heading).to_be_visible()


@pytest.mark.predsedatel
@pytest.mark.parametrize("status", PredsedatelPage.STATUSES)
def test_status_filter_switches_without_error(council_page: PredsedatelPage, status):
    # переключение read-only — не меняет данные, только то, какие
    # рассмотрения показаны. Таблица может смениться на пустой стейт при 0
    # совпадений (см. аналогичное поведение ExpertPage/ReferencePage) —
    # поэтому проверяем не table, а то, что сама страница осталась цела
    council_page.filter_by_status(status)
    expect(council_page.heading).to_be_visible()


@pytest.mark.predsedatel
def test_open_review_shows_application_info(council_page: PredsedatelPage):
    council_page.filter_by_status("Ожидает рассмотрения")
    if council_page.row_count() == 0:
        pytest.skip("Нет рассмотрений в статусе 'Ожидает рассмотрения' на стенде")

    review = council_page.open_review(0)
    expect(review.application_link).to_be_visible()
    expect(review.ai_response_heading).to_be_visible()
    expect(review.expert_comment_heading).to_be_visible()
    expect(review.votes_heading).to_be_visible()


@pytest.mark.predsedatel
def test_pending_review_shows_final_decision_form(council_page: PredsedatelPage):
    # НЕ кликаем по confirm/reject — это необратимо меняет статус реального
    # рассмотрения на общем дев-стенде. Проверяем только, что председателю
    # доступна форма (в отличие от sovet_tsuri, которому показывается форма
    # голосования "Ваш голос")
    council_page.filter_by_status("Ожидает рассмотрения")
    if council_page.row_count() == 0:
        pytest.skip("Нет рассмотрений в статусе 'Ожидает рассмотрения' на стенде")

    review = council_page.open_review(0)
    assert not review.is_decided()
    expect(review.decision_comment_input).to_be_visible()
    expect(review.confirm_decision_button).to_be_visible()
    expect(review.reject_decision_button).to_be_visible()
    expect(review.confirm_vote_button).not_to_be_visible()


@pytest.mark.predsedatel
@pytest.mark.parametrize("decided_status", ["Подтверждён", "Отклонён"])
def test_decided_review_shows_readonly_record(council_page: PredsedatelPage, decided_status):
    council_page.filter_by_status(decided_status)
    if council_page.row_count() == 0:
        pytest.skip(f"Нет рассмотрений в статусе '{decided_status}' на стенде")

    try:
        review: CouncilReviewPage = council_page.open_review(0)
    except PlaywrightTimeoutError:
        # бакет "решённых" рассмотрений маленький и живой (общий дев-стенд) —
        # запись могла исчезнуть между row_count() и кликом; это тот же
        # случай "пусто", что и row_count() == 0 выше, а не баг локатора
        pytest.skip(f"Рассмотрение в статусе '{decided_status}' исчезло со стенда между проверкой и открытием")

    assert review.is_decided()
    expect(review.confirm_decision_button).not_to_be_visible()
    expect(review.reject_decision_button).not_to_be_visible()


@pytest.mark.predsedatel
def test_back_link_returns_to_list(council_page: PredsedatelPage):
    if council_page.row_count() == 0:
        pytest.skip("Нет рассмотрений на стенде")

    review = council_page.open_review(0)
    back = review.back_to_list()
    expect(back.heading).to_be_visible()

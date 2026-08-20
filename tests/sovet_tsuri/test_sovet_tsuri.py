import pytest
from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.sovet_tsuri.sovet_tsuri_page import SovetTsuriPage
from pages.common.council_review_page import CouncilReviewPage


@pytest.mark.sovet_tsuri
def test_council_list_loads(council_page: SovetTsuriPage):
    expect(council_page.heading).to_be_visible()


@pytest.mark.sovet_tsuri
@pytest.mark.parametrize("status", SovetTsuriPage.STATUSES)
def test_status_filter_switches_without_error(council_page: SovetTsuriPage, status):
    # переключение read-only — не меняет данные. Таблица может смениться на
    # пустой стейт при 0 совпадений, поэтому проверяем не table, а то, что
    # сама страница осталась цела
    council_page.filter_by_status(status)
    expect(council_page.heading).to_be_visible()


@pytest.mark.sovet_tsuri
def test_open_review_shows_application_info(council_page: SovetTsuriPage):
    council_page.filter_by_status("Ожидает рассмотрения")
    if council_page.row_count() == 0:
        pytest.skip("Нет рассмотрений в статусе 'Ожидает рассмотрения' на стенде")

    review = council_page.open_review(0)
    expect(review.application_link).to_be_visible()
    expect(review.ai_response_heading).to_be_visible()
    expect(review.expert_comment_heading).to_be_visible()
    expect(review.votes_heading).to_be_visible()


@pytest.mark.sovet_tsuri
def test_pending_review_shows_vote_form(council_page: SovetTsuriPage):
    # НЕ кликаем по confirm/reject — это необратимо меняет статус реального
    # рассмотрения на общем дев-стенде. Проверяем только, что члену совета
    # доступна форма голосования (в отличие от predsedatel, которому
    # показывается форма "Итоговое решение")
    council_page.filter_by_status("Ожидает рассмотрения")
    if council_page.row_count() == 0:
        pytest.skip("Нет рассмотрений в статусе 'Ожидает рассмотрения' на стенде")

    review = council_page.open_review(0)
    assert not review.is_decided()
    expect(review.vote_comment_input).to_be_visible()
    expect(review.confirm_vote_button).to_be_visible()
    expect(review.reject_vote_button).to_be_visible()
    expect(review.confirm_decision_button).not_to_be_visible()


@pytest.mark.sovet_tsuri
@pytest.mark.parametrize("decided_status", ["Подтверждён", "Отклонён"])
def test_decided_review_shows_readonly_record(council_page: SovetTsuriPage, decided_status):
    council_page.filter_by_status(decided_status)
    if council_page.row_count() == 0:
        pytest.skip(f"Нет рассмотрений в статусе '{decided_status}' на стенде")

    try:
        review: CouncilReviewPage = council_page.open_review(0)
    except PlaywrightTimeoutError:
        # см. аналогичный комментарий в tests/predsedatel/test_predsedatel.py
        pytest.skip(f"Рассмотрение в статусе '{decided_status}' исчезло со стенда между проверкой и открытием")

    assert review.is_decided()
    expect(review.confirm_vote_button).not_to_be_visible()
    expect(review.reject_vote_button).not_to_be_visible()


@pytest.mark.sovet_tsuri
def test_back_link_returns_to_list(council_page: SovetTsuriPage):
    if council_page.row_count() == 0:
        pytest.skip("Нет рассмотрений на стенде")

    review = council_page.open_review(0)
    back = review.back_to_list()
    expect(back.heading).to_be_visible()

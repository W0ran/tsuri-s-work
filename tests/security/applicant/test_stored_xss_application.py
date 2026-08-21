"""Stored XSS в поле "название" заявки (Торговое наименование).

Проверка разделена на два этапа, потому что тестовые копии заявок
(test-submit) обрабатываются очередью эксперта асинхронно и небыстро —
уже видимые эксперту test-заявки на стенде имеют возраст порядка 10 дней,
синхронный тест не может столько ждать:

  1. test_stored_xss_application_submission — синхронный, часть обычного
     прогона. Реально подаёт заявку с XSS-payload'ом в названии через
     "Создать тестовую копию и отправить в экспертизу", проверяет что
     значение сохранилось без искажений и не выполнилось при перезагрузке
     страницы заявителем. Помечает заявку уникальным маркером и запоминает
     её в fixtures/_stored_xss_pending.jsonl для второго этапа.

  2. test_stored_xss_visible_to_expert — отдельный, самостоятельно
     пропускает себя (skip), если ни одна из ранее отправленных заявок
     ещё не стала видна эксперту (OCR не завершился). Предназначен для
     ручного/отложенного запуска после того, как заявки из первого этапа
     "дозреют" в очереди эксперта.
"""

import pytest
from playwright.sync_api import expect

import config
from pages.common.login_page import LoginPage
from pages.applicant.upload_page import UploadPage
from utils.security_checks import XSS_PAYLOADS
from utils.test_data_marker import (
    load_pending_submissions,
    make_test_application_name,
    record_pending_submission,
)


@pytest.mark.security
@pytest.mark.applicant
@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_stored_xss_application_submission(application_params_page, payload):
    wizard = application_params_page
    page = wizard.page

    wizard.fill_required_top_level_fields()
    wizard.go_to_section("2. Сведения о ЛС")

    marker_name = make_test_application_name()
    full_value = f"{marker_name} {payload}"
    wizard.trade_name_field().fill(full_value)

    wizard.go_to_documents_tab()
    upload_page = UploadPage(page)
    filled = upload_page.upload_all_required_documents()
    assert filled > 0, "Не нашлось ни одной обязательной карточки документа для заполнения"

    upload_page.go_to_review()
    body = wizard.submit_test_copy()

    application = body["application"]
    assert application.get("id"), f"Заявка не создана: {body}"
    stored_value = application["values"].get("param-trade-name-ru")
    assert stored_value == full_value, (
        f"Значение поля исказилось при сохранении: отправили {full_value!r}, "
        f"получили {stored_value!r}"
    )

    record_pending_submission(application["id"], marker_name, payload)

    # stored XSS не должен выполниться и у самого заявителя при перезагрузке
    page.add_init_script("window.__xss_fired = false;")
    page.reload()
    page.wait_for_load_state("networkidle")
    executed = page.evaluate("() => window.__xss_fired === true")
    assert not executed, f"XSS выполнился в интерфейсе заявителя для payload: {payload!r}"


@pytest.mark.security
@pytest.mark.applicant
def test_stored_xss_visible_to_expert(browser):
    pending = load_pending_submissions()
    if not pending:
        pytest.skip(
            "Нет ранее отправленных test-submit заявок с XSS-маркером — "
            "сначала прогоните test_stored_xss_application_submission"
        )

    checked_any = False
    page = browser.new_page()
    try:
        page.add_init_script("window.__xss_fired = false;")
        lp = LoginPage(page)
        lp.open(config.BASE_URL)
        lp.login(config.USERS["expert"]["login"], config.USERS["expert"]["password"])
        # не доверяем мгновенному page.url сразу после клика — SPA-переход
        # ещё не успел произойти (тот же класс гонки, что чинили в
        # is_error_visible/is_draft_saved_toast_visible); ждём явный маркер
        # страницы эксперта вместо page.wait_for_load_state("networkidle")
        try:
            expect(page.get_by_text("Кабинет эксперта")).to_be_visible(timeout=15_000)
        except AssertionError:
            pytest.fail(f"Не удалось залогиниться экспертом — URL после логина: {page.url}")

        for entry in pending:
            page.goto(f"{config.BASE_URL}/expert/{entry['app_id']}")
            page.wait_for_load_state("networkidle")
            body = page.locator("body").inner_text()
            if "Нет доступа к заявке" in body:
                continue  # OCR/проверки ещё не завершились — заявка ещё не видна эксперту
            if "К списку заявок" not in body:
                pytest.fail(
                    f"Неожиданное состояние страницы для заявки {entry['app_id']} "
                    f"(ни доступа, ни отказа в доступе): {body[:300]!r}"
                )
            checked_any = True
            executed = page.evaluate("() => window.__xss_fired === true")
            assert not executed, (
                f"Stored XSS выполнился в просмотре эксперта: маркер "
                f"{entry['marker_name']!r}, payload {entry['payload']!r}, "
                f"заявка {entry['app_id']}"
            )
    finally:
        page.close()

    if not checked_any:
        pytest.skip(
            f"Ни одна из {len(pending)} ожидающих test-заявок ещё не видна эксперту "
            f"(OCR тестовых копий может занимать часы) — запустите тест позже"
        )

import pytest
from utils.security_checks import (
    SQLI_PAYLOADS,
    assert_field_no_time_based_sqli,
    assert_field_rejects_sqli,
)


@pytest.mark.security
@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_login_sqli_no_bypass(login_page, payload):
    login_page.login(payload, payload)
    assert login_page.is_error_visible(), f"Возможный обход аутентификации через SQLi: {payload}"
    assert login_page.page.url.endswith("/login")


@pytest.mark.security
@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_login_sqli_no_error_leak(login_page, payload):
    # пароль должен быть непустым, иначе клиентская HTML5-валидация ("required")
    # блокирует сабмит и запрос вообще не уходит на бэкенд — payload в логине
    # никогда не будет реально проверен
    login_page.password_input.fill("anything")
    assert_field_rejects_sqli(
        login_page.page, login_page.login_input, login_page.submit_button, payload
    )


@pytest.mark.security
def test_login_sqli_time_based_no_delay(login_page):
    login_page.password_input.fill("anything")
    assert_field_no_time_based_sqli(
        login_page.page, login_page.login_input, login_page.submit_button
    )

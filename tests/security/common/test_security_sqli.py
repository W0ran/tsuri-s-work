import time
import pytest

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "admin'--",
    "'; DROP TABLE users; --",
    "1' UNION SELECT NULL--",
]

TIME_BASED_PAYLOAD = "' AND SLEEP(5)--"  # безопасен: если инъекция не проходит, ничего не произойдёт

ERROR_LEAK_MARKERS = [
    "sql syntax", "sqlstate", "postgresql", "mysql", "ORA-", "syntax error at or near",
    "unclosed quotation", "npgsql", "psycopg",
]


@pytest.mark.security
@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_login_sqli_no_bypass(login_page, payload):
    login_page.login(payload, payload)
    assert login_page.is_error_visible(), f"Возможный обход аутентификации через SQLi: {payload}"
    assert login_page.page.url.endswith("/login")


@pytest.mark.security
@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_login_sqli_no_error_leak(login_page, payload):
    login_page.login(payload, "anything")
    body_text = login_page.page.locator("body").inner_text().lower()
    leaked = [m for m in ERROR_LEAK_MARKERS if m in body_text]
    assert not leaked, f"Утечка деталей SQL-ошибки: {leaked} для payload {payload}"


@pytest.mark.security
def test_login_sqli_time_based_no_delay(login_page):
    start = time.monotonic()
    login_page.login(TIME_BASED_PAYLOAD, "anything")
    login_page.page.wait_for_load_state("networkidle")
    elapsed = time.monotonic() - start
    assert elapsed < 3, (
        f"Ответ занял {elapsed:.1f}с — подозрение на time-based SQL-инъекцию "
        f"(ожидание SLEEP(5) могло сработать на сервере)"
    )

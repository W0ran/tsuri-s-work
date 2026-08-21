import time
from playwright.sync_api import Page, Locator

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "1' UNION SELECT NULL--",
    "admin'--",
]

TIME_BASED_SQLI_PAYLOAD = "' AND SLEEP(5)--"

ERROR_LEAK_MARKERS = [
    "sql syntax", "sqlstate", "postgresql", "mysql", "ora-",
    "syntax error at or near", "unclosed quotation", "npgsql", "psycopg",
]


def assert_field_rejects_sqli(page: Page, field: Locator, submit: Locator, payload: str) -> None:
    """Универсальная проверка: заполняем поле payload'ом, отправляем форму,
    убеждаемся что нет утечки деталей SQL-ошибки и приложение не падает."""
    field.fill(payload)
    submit.click()
    page.wait_for_load_state("networkidle")

    body_text = page.locator("body").inner_text().lower()
    leaked = [m for m in ERROR_LEAK_MARKERS if m in body_text]
    assert not leaked, f"Утечка деталей SQL-ошибки для payload {payload!r}: {leaked}"

    # проверка, что страница не превратилась в "белый экран" / 500-ошибку
    assert page.locator("body").inner_text().strip(), "Пустая страница после payload — возможен краш сервера"


def assert_field_no_time_based_sqli(page: Page, field: Locator, submit: Locator, threshold_sec: float = 3.0) -> None:
    """Проверка на time-based слепую инъекцию: если SLEEP(5) выполнился на
    сервере, ответ придёт заметно дольше порога."""
    field.fill(TIME_BASED_SQLI_PAYLOAD)
    start = time.monotonic()
    submit.click()
    page.wait_for_load_state("networkidle")
    elapsed = time.monotonic() - start
    assert elapsed < threshold_sec, (
        f"Ответ занял {elapsed:.1f}с при пороге {threshold_sec}с — "
        f"подозрение на time-based SQL-инъекцию"
    )


XSS_PAYLOADS = [
    "<script>window.__xss_fired = true</script>",
    "<img src=x onerror=window.__xss_fired=true>",
    "<svg onload=window.__xss_fired=true>",
    "\"><script>window.__xss_fired=true</script>",  # закрытие атрибута + инъекция
    "javascript:window.__xss_fired=true",  # для полей, которые могут стать href
]


def assert_no_xss_executed(page: Page, field: Locator, submit: Locator, payload: str) -> None:
    """Заполняем поле payload'ом, отправляем, проверяем что скрипт НЕ выполнился
    в текущем контексте страницы."""
    page.evaluate("() => { window.__xss_fired = false; }")  # сброс перед проверкой
    field.fill(payload)
    submit.click()
    page.wait_for_load_state("networkidle")

    executed = page.evaluate("() => window.__xss_fired === true")
    assert not executed, f"XSS выполнился для payload: {payload!r}"


def assert_no_xss_executed_on_reload(page: Page, url: str, payload: str) -> None:
    """Для stored XSS: сохранённое значение не должно выполниться и при
    свежей загрузке страницы (не только сразу после ввода)."""
    page.evaluate("() => { window.__xss_fired = false; }")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    executed = page.evaluate("() => window.__xss_fired === true")
    assert not executed, f"Stored XSS выполнился при перезагрузке страницы: {payload!r}"

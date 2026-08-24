"""Isolated SQLi sweep for every known application values{} field."""

import json

import pytest

from utils.all_param_fields import ALL_FIELDS
from utils.security_checks import SQLI_PAYLOADS

SQL_ERROR_MARKERS = [
    "sqlstate", "syntax error", "ora-", "postgresql", "sqlite", "odbc",
    "unclosed quotation", "mysql_fetch",
]

CLIENT_SIDE_FORMAT_VALIDATED_FIELDS = {
    "param-mi-mfr-email",
}


def pytest_generate_tests(metafunc):
    if "payload" not in metafunc.fixturenames and "field_name" not in metafunc.fixturenames:
        return
    if "payload" in metafunc.fixturenames:
        selected = metafunc.config.getoption("--sqli-payload")
        metafunc.parametrize("payload", [selected] if selected else SQLI_PAYLOADS)
    if "field_name" in metafunc.fixturenames:
        chunk = metafunc.config.getoption("--sqli-chunk")
        chunk_size = metafunc.config.getoption("--sqli-chunk-size")
        if chunk_size < 1:
            raise pytest.UsageError("--sqli-chunk-size должен быть больше нуля")
        if chunk is not None:
            if chunk < 1:
                raise pytest.UsageError("--sqli-chunk должен быть не меньше 1")
            start = (chunk - 1) * chunk_size
            fields = ALL_FIELDS[start : start + chunk_size]
            if not fields:
                raise pytest.UsageError(
                    f"Чанк {chunk} пуст: всего доступно {len(ALL_FIELDS)} полей "
                    f"при размере чанка {chunk_size}"
                )
        else:
            fields = ALL_FIELDS
        metafunc.parametrize("field_name", fields)


@pytest.mark.security
@pytest.mark.applicant
@pytest.mark.slow
@pytest.mark.full_sweep
def test_sqli_full_sweep(wizard_page, field_name, payload):
    """Replace one values{} field in the real draft-save request and verify
    that the server does not expose SQL errors or return a 5xx response.
    """
    if field_name in CLIENT_SIDE_FORMAT_VALIDATED_FIELDS:
        pytest.skip(
            f"{field_name!r} имеет клиентскую валидацию формата (email/tel/url) — "
            "SQLi payload не проходит через UI-сабмит, нужен отдельный прямой API-тест"
        )

    def handle_route(route):
        request = route.request
        try:
            body = json.loads(request.post_data or "{}")
        except json.JSONDecodeError:
            route.continue_()
            return

        values = body.get("values")
        if isinstance(values, dict):
            values[field_name] = payload
            route.continue_(post_data=json.dumps(body))
            return
        route.continue_()

    page = wizard_page.page
    page.route("**/api/applications/**", handle_route)
    with page.expect_response(
        lambda response: "/api/applications" in response.url
        and response.request.method in ("POST", "PUT", "PATCH"),
        timeout=15_000,
    ) as response_info:
        wizard_page.save_draft()

    response = response_info.value
    body_lower = response.text().lower()
    leaked = [marker for marker in SQL_ERROR_MARKERS if marker in body_lower]
    assert not leaked, (
        f"Утечка SQL-ошибки для поля {field_name!r}, payload={payload!r}: {leaked}"
    )
    assert response.status < 500, (
        f"HTTP {response.status} для поля {field_name!r}, payload={payload!r}"
    )

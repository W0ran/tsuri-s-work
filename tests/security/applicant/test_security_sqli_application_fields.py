import pytest
from utils.security_checks import (
    SQLI_PAYLOADS, assert_field_rejects_sqli, assert_field_no_time_based_sqli,
)


@pytest.mark.security
@pytest.mark.applicant
@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_manufacturer_field_sqli(application_params_page, payload):
    # "1. Основное" открыт по умолчанию сразу после выбора критериев
    wizard = application_params_page
    assert_field_rejects_sqli(
        wizard.page, wizard.manufacturer_field(), wizard.save_draft_button(), payload
    )


@pytest.mark.security
@pytest.mark.applicant
@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_trade_name_field_sqli(application_params_page, payload):
    wizard = application_params_page
    wizard.go_to_section("2. Сведения о ЛС")
    assert_field_rejects_sqli(
        wizard.page, wizard.trade_name_field(), wizard.save_draft_button(), payload
    )


@pytest.mark.security
@pytest.mark.applicant
def test_trade_name_field_time_based_sqli(application_params_page):
    wizard = application_params_page
    wizard.go_to_section("2. Сведения о ЛС")
    assert_field_no_time_based_sqli(
        wizard.page, wizard.trade_name_field(), wizard.save_draft_button()
    )

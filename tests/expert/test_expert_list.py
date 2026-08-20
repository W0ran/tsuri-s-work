import pytest
from playwright.sync_api import expect
from pages.expert.expert_page import ExpertPage
import config


@pytest.mark.expert
def test_expert_dashboard_loads(expert_list_page: ExpertPage):
    expect(expert_list_page.heading).to_be_visible()
    expect(expert_list_page.search_input).to_be_visible()
    expect(expert_list_page.status_filter).to_be_visible()
    expect(expert_list_page.result_filter).to_be_visible()


@pytest.mark.expert
def test_total_kpi_matches_row_count(expert_list_page: ExpertPage):
    # "Всего заявок" — единственная KPI-плашка, гарантированно равная числу
    # строк в таблице независимо от того, сколько заявок сейчас на стенде
    total = int(expert_list_page.kpi_value("Всего заявок"))
    assert expert_list_page.row_count() == total


@pytest.mark.expert
def test_search_filters_to_matching_row(expert_list_page: ExpertPage):
    total_before = expert_list_page.row_count()
    assert total_before > 0, "На стенде должна быть хотя бы одна заявка эксперту"

    drug_name = expert_list_page.rows.first.inner_text().splitlines()[0]

    expert_list_page.search(drug_name)
    expect(expert_list_page.rows.first).to_contain_text(drug_name)
    assert expert_list_page.row_count() <= total_before


@pytest.mark.expert
def test_search_with_no_matches_shows_empty_state(expert_list_page: ExpertPage):
    # таблица не пустеет до 0 строк при отсутствии совпадений — вместо этого
    # рендерится строка-заглушка с сообщением (см. docstring ExpertPage)
    expert_list_page.search("несуществующий-препарат-xyz-000")
    expect(expert_list_page.no_results_message).to_be_visible()


@pytest.mark.expert
def test_open_application_navigates_to_detail(expert_list_page: ExpertPage):
    assert expert_list_page.row_count() > 0
    application_page = expert_list_page.open_first_application()
    expect(application_page.heading).to_be_visible()
    expect(application_page.back_link).to_be_visible()


@pytest.mark.expert
def test_go_to_workflow_queue(expert_list_page: ExpertPage):
    workflow_page = expert_list_page.go_to_workflow()
    expect(workflow_page.heading).to_be_visible()
    expect(workflow_page.page).to_have_url(f"{config.BASE_URL}/expert/workflow")

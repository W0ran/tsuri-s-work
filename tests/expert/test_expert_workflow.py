import pytest
from playwright.sync_api import expect
from pages.expert.workflow_page import WorkflowPage


@pytest.mark.expert
def test_workflow_queue_loads(workflow_page: WorkflowPage):
    expect(workflow_page.heading).to_be_visible()
    expect(workflow_page.stage_filter).to_be_visible()
    expect(workflow_page.refresh_button).to_be_visible()


@pytest.mark.expert
def test_queued_kpi_matches_row_count(workflow_page: WorkflowPage):
    # "В очереди" — единственная KPI-плашка, гарантированно равная числу дел
    # в таблице "Дела по текущему этапу" независимо от размера очереди
    queued = int(workflow_page.kpi_value("В очереди"))
    assert workflow_page.row_count() == queued


@pytest.mark.expert
def test_back_link_returns_to_expert_list(workflow_page: WorkflowPage):
    expert_page = workflow_page.back_to_applications()
    expect(expert_page.heading).to_be_visible()


@pytest.mark.expert
def test_open_case_dialog_shows_actions_and_route(workflow_page: WorkflowPage):
    assert workflow_page.row_count() > 0, "В очереди должно быть хотя бы одно дело"
    drug_name = workflow_page.rows.first.inner_text().splitlines()[0]

    dialog = workflow_page.open_first_case()
    expect(dialog.dialog).to_be_visible()
    expect(dialog.heading).to_have_text(drug_name)
    expect(dialog.open_application_link).to_be_visible()
    expect(dialog.assign_to_me_button).to_be_visible()
    expect(dialog.complete_stage_button).to_be_visible()


@pytest.mark.expert
def test_close_case_dialog(workflow_page: WorkflowPage):
    assert workflow_page.row_count() > 0
    dialog = workflow_page.open_first_case()
    expect(dialog.dialog).to_be_visible()

    dialog.close()
    expect(dialog.dialog).not_to_be_visible()


@pytest.mark.expert
def test_open_application_from_case_dialog(workflow_page: WorkflowPage):
    assert workflow_page.row_count() > 0
    dialog = workflow_page.open_first_case()

    application_page = dialog.open_application()
    expect(application_page.heading).to_be_visible()
    expect(application_page.back_link).to_be_visible()

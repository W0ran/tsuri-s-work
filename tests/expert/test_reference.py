import pytest
from playwright.sync_api import expect
from pages.expert.reference_page import ReferencePage
from pages.expert.reference_document_panel import ReferenceDocumentPanel


@pytest.mark.expert
def test_reference_page_loads(reference_page: ReferencePage):
    expect(reference_page.heading).to_be_visible()
    expect(reference_page.search_input).to_be_visible()


@pytest.mark.expert
def test_documents_metric_matches_row_count(reference_page: ReferencePage):
    # "Документы ядра" — метрика, гарантированно равная числу строк в
    # таблице независимо от того, сколько НПА сейчас в справочнике
    total = int(reference_page.metric_value("Документы ядра"))
    assert reference_page.row_count() == total


@pytest.mark.expert
@pytest.mark.parametrize("filter_button_name", ["filter_ls_button", "filter_mi_button"])
def test_area_filter_narrows_results(reference_page: ReferencePage, filter_button_name):
    total_before = reference_page.row_count()
    assert total_before > 0

    getattr(reference_page, filter_button_name).click()
    filtered_count = reference_page.row_count()
    assert 0 < filtered_count < total_before


@pytest.mark.expert
def test_all_filter_restores_full_list(reference_page: ReferencePage):
    total_before = reference_page.row_count()
    reference_page.filter_ls_button.click()
    assert reference_page.row_count() < total_before

    reference_page.filter_all_button.click()
    assert reference_page.row_count() == total_before


@pytest.mark.expert
def test_search_with_no_matches_shows_empty_state(reference_page: ReferencePage):
    reference_page.search("zzz-несуществующий-нпа-000")
    expect(reference_page.page.get_by_text("Ничего не найдено")).to_be_visible()
    assert reference_page.row_count() == 0


@pytest.mark.expert
def test_open_document_shows_detail_panel(reference_page: ReferencePage):
    assert reference_page.row_count() > 0
    panel = reference_page.open_document(0)
    expect(panel.back_button).to_be_visible()
    expect(panel.tab("Требования")).to_have_attribute("aria-selected", "true")


@pytest.mark.expert
@pytest.mark.parametrize("tab_name", ReferenceDocumentPanel.TABS)
def test_document_tabs_are_switchable(reference_page: ReferencePage, tab_name):
    panel = reference_page.open_document(0)
    panel.open_tab(tab_name)
    expect(panel.tab(tab_name)).to_have_attribute("aria-selected", "true")


@pytest.mark.expert
def test_back_button_returns_to_table(reference_page: ReferencePage):
    panel = reference_page.open_document(0)
    back_page = panel.back_to_table()
    expect(back_page.heading).to_be_visible()
    assert back_page.row_count() > 0

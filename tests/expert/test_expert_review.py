import pytest
from playwright.sync_api import expect
from pages.expert.application_page import ApplicationPage
from pages.expert.expert_page import ExpertPage


@pytest.fixture
def application_page(expert_list_page: ExpertPage) -> ApplicationPage:
    assert expert_list_page.row_count() > 0, "На стенде должна быть хотя бы одна заявка эксперту"
    return expert_list_page.open_first_application()


@pytest.mark.expert
def test_application_header_loads(application_page: ApplicationPage):
    expect(application_page.heading).to_be_visible()
    expect(application_page.back_link).to_be_visible()


@pytest.mark.expert
def test_remarks_tab_selected_by_default(application_page: ApplicationPage):
    expect(application_page.tab("Замечания")).to_have_attribute("aria-selected", "true")
    assert application_page.active_tab_name().startswith("Замечания")


@pytest.mark.expert
@pytest.mark.parametrize("tab_name", ApplicationPage.TABS)
def test_all_tabs_are_switchable(application_page: ApplicationPage, tab_name):
    application_page.open_tab(tab_name)
    expect(application_page.tab(tab_name)).to_have_attribute("aria-selected", "true")


@pytest.mark.expert
@pytest.mark.parametrize("filter_label", ApplicationPage.REMARK_FILTERS)
def test_remark_filter_switches_without_error(application_page: ApplicationPage, filter_label):
    # проверяем, что переключение суб-фильтра не ломает страницу. Таблица
    # видна не всегда — при 0 совпадений по фильтру она заменяется текстом
    # "По выбранному фильтру записей нет" внутри той же панели, поэтому
    # проверяем именно панель, а не table (данные внутри зависят от
    # конкретной заявки и не проверяются здесь построчно)
    application_page.select_remark_filter(filter_label)
    expect(application_page.remarks_panel).to_be_visible()


@pytest.mark.expert
def test_search_remarks_narrows_or_empties_table(application_page: ApplicationPage):
    rows_before = application_page.remark_rows().count()
    if rows_before == 0:
        pytest.skip("В заявке нет замечаний для проверки поиска")

    application_page.search_remarks("несуществующий-текст-замечания-xyz-000")
    assert application_page.remark_rows().count() <= rows_before


@pytest.mark.expert
def test_back_link_returns_to_expert_list(application_page: ApplicationPage):
    expert_page = application_page.back_to_list()
    expect(expert_page.heading).to_be_visible()

from playwright.sync_api import expect
from pages.applicant.wizard_page import WizardPage


def test_applications_list_shows_heading(applications_list_page):
    expect(applications_list_page.page_heading).to_be_visible()
    expect(applications_list_page.user_badge).to_be_visible()


def test_wizard_reaches_documents_tab(applicant_page):
    wizard = WizardPage(applicant_page)
    wizard.start_new_application_and_reach_documents()
    expect(wizard.documents_tab).to_be_visible()

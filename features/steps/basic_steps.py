from behave import when, then
from playwright.sync_api import expect

@when('I type "{text}" directly in the search input')
def type_text(context, text):
    search_input = context.page.get_by_role("textbox", name="Search")
    search_input.fill(text)

@when('I click directly on the search button')
def click_search(context):
    button = context.page.get_by_role("button", name="Search")
    button.click()

@when('I click directly on the "{link_text}" link')
def click_link(context, link_text):
    link = context.page.get_by_role("link", name=link_text)
    link.click()

@when('I click directly on the "{button_text}" button')
def click_button(context, button_text):
    button = context.page.get_by_role("button", name=button_text)
    button.click()

@then('the search results should be visible')
def verify_search_results(context):
    results = context.page.locator("#search")
    expect(results).to_be_visible(timeout=5000)

@then('the settings menu should be visible')
def verify_settings_menu(context):
    menu = context.page.locator('[role="menu"]')
    expect(menu).to_be_visible(timeout=5000)
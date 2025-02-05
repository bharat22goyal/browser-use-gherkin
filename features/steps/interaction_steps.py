from behave import when, then
from playwright.sync_api import expect

@when('I type "{text}" in the llm search box')
def step_impl(context, text):
    search_input = context.page.get_by_role("textbox", name="Search")
    search_input.fill(text)

@when('I click the llm search button')
def step_impl(context):
    button = context.page.get_by_role("button", name="Search")
    button.click()

@when('I click the first search result link')
def step_impl(context):
    link = context.page.locator("#search a").first
    link.click()

@when('I scroll page to the {position}')
def step_impl(context, position):
    if position.lower() == "bottom":
        context.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    elif position.lower() == "top":
        context.page.evaluate("window.scrollTo(0, 0)")

@when('I scroll page to top')
def step_impl(context):
    context.page.evaluate("window.scrollTo(0, 0)")

@then('I should see page element: {element}')
def step_impl(context, element):
    if "navigation bar" in element:
        nav = context.page.locator("nav").first
        expect(nav).to_be_visible(timeout=5000)
    elif "search bar" in element:
        search = context.page.get_by_role("textbox", name="Search")
        expect(search).to_be_visible(timeout=5000)

@then('page header should be visible')
def step_impl(context):
    header = context.page.locator("header").first
    expect(header).to_be_visible(timeout=5000)

@then('page footer should be visible')
def step_impl(context):
    footer = context.page.locator("footer").first
    expect(footer).to_be_visible(timeout=5000) 
from behave import when, then
from playwright.sync_api import expect

@when('I click directly on the "{link_text}" link')
def click_link(context, link_text):
    link = context.page.get_by_role("link", name=link_text)
    link.click()

@then('I should see the playwright heading')
def verify_playwright_heading(context):
    heading = context.page.get_by_text("Playwright enables reliable end-to-end testing")
    expect(heading).to_be_visible(timeout=5000)

@then('I should see the node js selector')
def verify_node_selector(context):
    selector = context.page.get_by_role("tab", name="Node.js")
    expect(selector).to_be_visible(timeout=5000)

@then('I should see the get started button')
def verify_get_started(context):
    button = context.page.get_by_role("link", name="Get started")
    expect(button).to_be_visible(timeout=5000)
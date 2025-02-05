from behave import when, then
from playwright.sync_api import expect
import logging

@when('I click directly on the "{link_text}" link')
def click_link(context, link_text):
    logging.info(f"Clicking on link with text: {link_text}")
    link = context.page.get_by_role("link", name=link_text)
    link.click()
    logging.info(f"Successfully clicked on link: {link_text}")

@then('I should see the playwright heading')
def verify_playwright_heading(context):
    logging.info("Verifying Playwright heading visibility")
    heading = context.page.get_by_text("Playwright enables reliable end-to-end testing for modern web apps")
    expect(heading).to_be_visible(timeout=5000)
    logging.info("Playwright heading verification successful")

@then('I should see the node js selector')
def verify_node_selector(context):
    logging.info("Verifying Node.js selector visibility")
    selector = context.page.get_by_role("tab", name="Node.js")
    expect(selector).to_be_visible(timeout=5000)
    logging.info("Node.js selector verification successful")

@then('I should see the get started button')
def verify_get_started(context):
    logging.info("Verifying 'Get started' button visibility")
    button = context.page.get_by_role("link", name="Get started")
    expect(button).to_be_visible(timeout=5000)
    logging.info("'Get started' button verification successful")
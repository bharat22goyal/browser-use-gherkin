from behave import when, then
from playwright.sync_api import expect
import logging

@when('I type "{text}" in the search box')
def type_in_search_box(context, text):
    logging.info(f"Typing text in search box: {text}")
    search_input = context.page.get_by_role("textbox", name="Search")
    search_input.fill(text)
    logging.info("Text input successful")

@when('I click the search button')
def click_search_button(context):
    logging.info("Clicking search button")
    button = context.page.get_by_role("button", name="Search")
    button.click()
    logging.info("Search button click successful")

@when('I click the first search result link')
def click_first_result(context):
    logging.info("Clicking first search result link")
    link = context.page.locator("#search a").first
    link.click()
    logging.info("First result link click successful")

@when('I scroll page to the {position}')
def scroll_page(context, position):
    logging.info(f"Scrolling page to position: {position}")
    if position.lower() == "bottom":
        context.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        logging.info("Scrolled to bottom of page")
    elif position.lower() == "top":
        context.page.evaluate("window.scrollTo(0, 0)")
        logging.info("Scrolled to top of page")

@when('I scroll page to top')
def scroll_to_top(context):
    logging.info("Scrolling page to top")
    context.page.evaluate("window.scrollTo(0, 0)")
    logging.info("Scrolled to top of page")

@then('I should see page element: {element}')
def verify_element_visibility(context, element):
    logging.info(f"Verifying visibility of element: {element}")
    if "navigation bar" in element:
        nav = context.page.locator("nav").first
        expect(nav).to_be_visible(timeout=5000)
        logging.info("Navigation bar visibility verified")
    elif "search bar" in element:
        search = context.page.get_by_role("textbox", name="Search")
        expect(search).to_be_visible(timeout=5000)
        logging.info("Search bar visibility verified")

@then('page header should be visible')
def verify_header_visibility(context):
    logging.info("Verifying header visibility")
    header = context.page.locator("header").first
    expect(header).to_be_visible(timeout=5000)
    logging.info("Header visibility verified")

@then('page footer should be visible')
def verify_footer_visibility(context):
    logging.info("Verifying footer visibility")
    footer = context.page.locator("footer").first
    expect(footer).to_be_visible(timeout=5000)
    logging.info("Footer visibility verified") 
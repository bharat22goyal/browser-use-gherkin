from behave import given, when, then
from playwright.sync_api import expect
import logging

@given('I am on "{url}"')
def navigate_to_url(context, url):
    logging.info(f"Navigating to URL: {url}")
    # Handle URLs without protocol
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    context.page.goto(url)
    logging.info(f"Successfully navigated to {url}")

@when('I go back in browser history')
def step_impl(context):
    logging.info("Going back in browser history")
    context.page.go_back()
    logging.info("Successfully went back in browser history")

@when('I go forward in browser history')
def step_impl(context):
    logging.info("Going forward in browser history")
    context.page.go_forward()
    logging.info("Successfully went forward in browser history")

@then('the page title should contain "{text}"')
def verify_page_title(context, text):
    logging.info(f"Verifying page title contains: {text}")
    # Wait for the title to contain the expected text
    current_title = context.page.title()
    logging.info(f"Current page title: {current_title}")
    assert text in current_title, f"Expected title to contain '{text}', but got '{current_title}'"
    logging.info(f"Title verification successful. Actual title: {current_title}")

@then('I should be on "{url}"')
def verify_current_url(context, url):
    logging.info(f"Verifying current URL is: {url}")
    # Handle URLs without protocol
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    # Wait for the URL to match
    expect(context.page).to_have_url(url, timeout=5000)
    actual_url = context.page.url
    logging.info(f"URL verification successful. Current URL: {actual_url}") 
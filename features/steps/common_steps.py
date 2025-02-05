from behave import given, when, then
from playwright.sync_api import expect

@given('I am on "{url}"')
def step_impl(context, url):
    # Handle URLs without protocol
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    context.page.goto(url)

@when('I go back in browser history')
def step_impl(context):
    context.page.go_back()

@when('I go forward in browser history')
def step_impl(context):
    context.page.go_forward()

@then('the page title should contain "{text}"')
def step_impl(context, text):
    # Wait for the title to contain the expected text
    expect(context.page).to_have_title(lambda t: text in t, timeout=5000)

@then('I should be on "{url}"')
def step_impl(context, url):
    # Handle URLs without protocol
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    # Wait for the URL to match
    expect(context.page).to_have_url(url, timeout=5000) 
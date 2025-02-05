@non-llm
Feature: Basic Browser Navigation
    As a user
    I want to perform basic browser navigation
    To verify browser automation functionality without LLM

    @non-llm
    Scenario: Basic Page Navigation
        Given I am on "https://playwright.dev"
        When I click directly on the "Get started" link
        Then the page title should contain "Getting Started"

    @non-llm
    Scenario: Basic Navigation History
        Given I am on "https://playwright.dev"
        When I click directly on the "Docs" link
        Then the page title should contain "Docs"
        When I go back in browser history
        Then I should be on "https://playwright.dev"
        And the page title should contain "Playwright"

    @non-llm
    Scenario: Basic Element Visibility
        Given I am on "https://playwright.dev"
        Then I should see the playwright heading
        And I should see the get started button 
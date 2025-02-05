@non-llm
Feature: Basic Browser Navigation
    As a user
    I want to perform basic browser navigation
    To verify browser automation functionality without LLM

    Scenario: Basic Google Search
        Given I am on "https://www.google.com"
        When I type "Browser Automation" directly in the search input
        And I click directly on the search button
        Then the page title should contain "Browser Automation"
        And the search results should be visible

    Scenario: Basic Navigation and History
        Given I am on "https://www.google.com"
        When I click directly on the "Gmail" link
        Then the page title should contain "Gmail"
        When I go back in browser history
        Then I should be on "https://www.google.com"

    Scenario: Basic Element Interactions
        Given I am on "https://www.google.com"
        When I click directly on the "Images" link
        And I click directly on the "Settings" button
        Then the settings menu should be visible 
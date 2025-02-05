@llm
Feature: Browser Search Functionality
    As a user
    I want to perform searches in the browser
    So that I can find relevant information

    Scenario: Search with LLM
        Given I am on the Google homepage
        When I search for "OpenAI ChatGPT"
        Then I should see search results
        And the first result should contain "openai.com"

    Scenario: Visual Search with LLM
        Given I am on the Google homepage
        When I search for "OpenAI logo" with vision enabled
        Then I should see search results with images
        And I should see the OpenAI logo 
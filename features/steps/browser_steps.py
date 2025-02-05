from behave import given, when, then
from browser_use import Agent
import asyncio
import logging

@given('I am on the Google homepage')
def step_impl(context):
    logging.info("Setting up Google homepage task")
    context.task = "go to google.com"
    context.add_infos = ""
    context.use_vision = False
    logging.info("Task setup completed")

@when('I search for "{query}"')
def step_impl(context, query):
    logging.info(f"Setting up search task for query: {query}")
    context.task = f"go to google.com and search for '{query}'"
    context.query = query
    async def run_agent():
        logging.info("Initializing agent for search task")
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=getattr(context, 'use_vision', False)
        )
        logging.info("Running agent with max_steps=10")
        return await agent.run(max_steps=10)
    
    logging.info("Executing agent in event loop")
    context.history = context.loop.run_until_complete(run_agent())
    logging.info("Agent execution completed")

@when('I search for "{query}" with vision enabled')
def step_impl(context, query):
    logging.info(f"Setting up vision-enabled search task for query: {query}")
    context.task = f"go to google.com and search for '{query}'"
    context.query = query
    context.use_vision = True
    async def run_agent():
        logging.info("Initializing agent with vision enabled")
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=True
        )
        logging.info("Running agent with max_steps=10")
        return await agent.run(max_steps=10)
    
    logging.info("Executing agent in event loop")
    context.history = context.loop.run_until_complete(run_agent())
    logging.info("Agent execution completed")

@then('I should see search results')
def step_impl(context):
    logging.info(f"Verifying search results for query: {context.query}")
    context.task = f"verify that search results are visible for '{context.query}'"
    async def run_agent():
        logging.info("Initializing agent for results verification")
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=getattr(context, 'use_vision', False)
        )
        logging.info("Running agent with max_steps=5")
        return await agent.run(max_steps=5)
    
    logging.info("Executing agent in event loop")
    context.history = context.loop.run_until_complete(run_agent())
    if context.history.errors():
        logging.error(f"Verification failed with errors: {context.history.errors()}")
    else:
        logging.info("Search results verification successful")
    assert context.history.errors() == []

@then('I should see search results with images')
def step_impl(context):
    logging.info(f"Verifying image search results for query: {context.query}")
    context.task = f"verify that image search results are visible for '{context.query}'"
    async def run_agent():
        logging.info("Initializing agent for image results verification")
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=True
        )
        logging.info("Running agent with max_steps=5")
        return await agent.run(max_steps=5)
    
    logging.info("Executing agent in event loop")
    context.history = context.loop.run_until_complete(run_agent())
    if context.history.errors():
        logging.error(f"Image verification failed with errors: {context.history.errors()}")
    else:
        logging.info("Image search results verification successful")
    assert context.history.errors() == []

@then('the first result should contain "{expected_url}"')
def step_impl(context, expected_url):
    logging.info(f"Verifying first result contains URL: {expected_url}")
    context.task = f"verify that the first search result contains {expected_url}"
    async def run_agent():
        logging.info("Initializing agent for URL verification")
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=getattr(context, 'use_vision', False)
        )
        logging.info("Running agent with max_steps=5")
        return await agent.run(max_steps=5)
    
    logging.info("Executing agent in event loop")
    context.history = context.loop.run_until_complete(run_agent())
    if context.history.errors():
        logging.error(f"URL verification failed with errors: {context.history.errors()}")
    else:
        logging.info(f"First result URL verification successful for {expected_url}")
    assert context.history.errors() == []

@then('I should see the OpenAI logo')
def step_impl(context):
    logging.info("Verifying OpenAI logo visibility")
    context.task = "verify that the OpenAI logo is visible in the search results"
    async def run_agent():
        logging.info("Initializing agent for logo verification")
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=True
        )
        logging.info("Running agent with max_steps=5")
        return await agent.run(max_steps=5)
    
    logging.info("Executing agent in event loop")
    context.history = context.loop.run_until_complete(run_agent())
    if context.history.errors():
        logging.error(f"Logo verification failed with errors: {context.history.errors()}")
    else:
        logging.info("OpenAI logo verification successful")
    assert context.history.errors() == [] 
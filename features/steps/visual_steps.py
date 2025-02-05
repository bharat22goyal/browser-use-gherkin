from behave import when, then
from browser_use import Agent
import asyncio
import logging

@then('I should see the company logo for {company}')
def step_impl(context, company):
    logging.info(f"Verifying logo visibility for company: {company}")
    context.task = f"verify that the {company} logo is visible on the page"
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
        logging.info(f"Logo verification successful for {company}")
    assert context.history.errors() == []

@then('I should see images of the {landmark}')
def step_impl(context, landmark):
    logging.info(f"Verifying images of landmark: {landmark}")
    context.task = f"verify that images of the {landmark} are visible in the search results"
    async def run_agent():
        logging.info("Initializing agent for landmark images verification")
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
        logging.error(f"Landmark images verification failed with errors: {context.history.errors()}")
    else:
        logging.info(f"Landmark images verification successful for {landmark}")
    assert context.history.errors() == []

@when('I switch to dark mode')
def step_impl(context):
    logging.info("Setting up dark mode switch task")
    context.task = "switch the website to dark mode"
    async def run_agent():
        logging.info("Initializing agent for dark mode switch")
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
        logging.error(f"Dark mode switch failed with errors: {context.history.errors()}")
    else:
        logging.info("Dark mode switch successful")

@then('the background should be dark')
def step_impl(context):
    logging.info("Verifying dark background")
    context.task = "verify that the page background is dark"
    async def run_agent():
        logging.info("Initializing agent for dark background verification")
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
        logging.error(f"Dark background verification failed with errors: {context.history.errors()}")
    else:
        logging.info("Dark background verification successful")
    assert context.history.errors() == []

@then('text should be light colored')
def step_impl(context):
    logging.info("Verifying light colored text")
    context.task = "verify that the text color is light against the dark background"
    async def run_agent():
        logging.info("Initializing agent for text color verification")
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
        logging.error(f"Text color verification failed with errors: {context.history.errors()}")
    else:
        logging.info("Light text color verification successful")
    assert context.history.errors() == [] 
from behave import given, when, then
from browser_use import Agent
import asyncio

@given('I am on the Google homepage')
def step_impl(context):
    context.task = "go to google.com"
    context.add_infos = ""
    context.use_vision = False

@when('I search for "{query}"')
def step_impl(context, query):
    context.task = f"go to google.com and search for '{query}'"
    context.query = query
    async def run_agent():
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=getattr(context, 'use_vision', False)
        )
        return await agent.run(max_steps=10)
    
    context.history = context.loop.run_until_complete(run_agent())

@when('I search for "{query}" with vision enabled')
def step_impl(context, query):
    context.task = f"go to google.com and search for '{query}'"
    context.query = query
    context.use_vision = True
    async def run_agent():
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=True
        )
        return await agent.run(max_steps=10)
    
    context.history = context.loop.run_until_complete(run_agent())

@then('I should see search results')
def step_impl(context):
    context.task = f"verify that search results are visible for '{context.query}'"
    async def run_agent():
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=getattr(context, 'use_vision', False)
        )
        return await agent.run(max_steps=5)
    
    context.history = context.loop.run_until_complete(run_agent())
    assert context.history.errors() == []

@then('I should see search results with images')
def step_impl(context):
    context.task = f"verify that image search results are visible for '{context.query}'"
    async def run_agent():
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=True
        )
        return await agent.run(max_steps=5)
    
    context.history = context.loop.run_until_complete(run_agent())
    assert context.history.errors() == []

@then('the first result should contain "{expected_url}"')
def step_impl(context, expected_url):
    context.task = f"verify that the first search result contains {expected_url}"
    async def run_agent():
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=getattr(context, 'use_vision', False)
        )
        return await agent.run(max_steps=5)
    
    context.history = context.loop.run_until_complete(run_agent())
    assert context.history.errors() == []

@then('I should see the OpenAI logo')
def step_impl(context):
    context.task = "verify that the OpenAI logo is visible in the search results"
    async def run_agent():
        agent = Agent(
            task=context.task,
            llm=context.llm,
            browser_context=context.browser_context,
            use_vision=True
        )
        return await agent.run(max_steps=5)
    
    context.history = context.loop.run_until_complete(run_agent())
    assert context.history.errors() == [] 
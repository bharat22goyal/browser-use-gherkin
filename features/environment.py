from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import asyncio
import nest_asyncio
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContextWindowSize
import logging

# Enable nested event loops
nest_asyncio.apply()

load_dotenv()

def before_all(context):
    logging.info("Starting test execution setup")
    
    # Create a single event loop for all tests
    context.loop = asyncio.get_event_loop()
    if context.loop.is_closed():
        context.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(context.loop)
    logging.info("Event loop initialized")

    # Initialize browser-use for LLM tests
    logging.info("Initializing browser-use for LLM tests")
    browser_config = BrowserConfig(
        headless=False,
        disable_security=False,
        extra_chromium_args=['--start-maximized']
    )
    context.browser_instance = Browser(config=browser_config)

    # Set up LLM configuration from environment variables
    context.llm_provider = os.getenv('TEST_LLM_PROVIDER', 'gemini')
    context.llm_model = os.getenv('TEST_LLM_MODEL', 'gemini-2.0-flash-exp')
    context.llm_base_url = os.getenv('TEST_LLM_BASE_URL', 'https://api.gemini.com')
    context.llm_api_key = os.getenv('GOOGLE_API_KEY', '')

    logging.info("LLM Configuration:")
    logging.info(f"Provider: {context.llm_provider}")
    logging.info(f"Model: {context.llm_model}")
    logging.info(f"Base URL: {context.llm_base_url}")

    # Initialize LLM
    from src.utils import utils
    context.llm = utils.get_llm_model(
        provider=context.llm_provider,
        model_name=context.llm_model,
        temperature=0.5,
        base_url=context.llm_base_url,
        api_key=context.llm_api_key
    )
    logging.info("LLM initialized successfully")

def before_scenario(context, scenario):
    logging.info(f"\nStarting scenario: {scenario.name}")
    logging.info(f"Tags: {scenario.tags}")
    
    logging.info("Setting up browser-use context for LLM test")
    # For LLM tests, use browser-use
    async def init_browser_context():
        context_config = BrowserContextConfig(
            no_viewport=False,
            browser_window_size=BrowserContextWindowSize(
                width=1920,
                height=1080
            )
        )
        context.browser_context = await context.browser_instance.new_context(config=context_config)
        logging.info("Browser-use context initialized")

    # Run the async initialization in the event loop
    context.loop.run_until_complete(init_browser_context())

def after_scenario(context, scenario):
    logging.info(f"\nCompleting scenario: {scenario.name}")
    logging.info(f"Status: {'Passed' if scenario.status == 'passed' else 'Failed'}")
    
    logging.info("Cleaning up browser-use context")
    async def cleanup_browser_context():
        if hasattr(context, 'browser_context'):
            await context.browser_context.close()
    
    # Run the async cleanup in the event loop
    context.loop.run_until_complete(cleanup_browser_context())

def after_all(context):
    logging.info("\nPerforming final cleanup")
    
    # Clean up LLM browser
    if hasattr(context, 'browser_instance'):
        logging.info("Cleaning up LLM browser")
        async def cleanup_browser():
            await context.browser_instance.close()
        
        # Run the async cleanup in the event loop
        try:
            context.loop.run_until_complete(cleanup_browser())
            pending = asyncio.all_tasks(context.loop)
            context.loop.run_until_complete(asyncio.gather(*pending))
            logging.info("LLM browser cleanup completed")
        except Exception as e:
            logging.error(f"Error during LLM browser cleanup: {str(e)}")
    
    # Clean up event loop
    if hasattr(context, 'loop'):
        try:
            context.loop.close()
            logging.info("Event loop closed")
        except Exception as e:
            logging.error(f"Error closing event loop: {str(e)}")
        asyncio.set_event_loop(None) 
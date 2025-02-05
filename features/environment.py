from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import asyncio
import nest_asyncio
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContextWindowSize

# Enable nested event loops
nest_asyncio.apply()

load_dotenv()

def before_all(context):
    # Get test type from environment
    test_type = os.getenv('TEST_TYPE', 'all')
    
    # Create a single event loop for all tests
    context.loop = asyncio.get_event_loop()
    if context.loop.is_closed():
        context.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(context.loop)

    # Initialize Playwright for non-LLM tests
    if test_type in ['non-llm', 'all']:
        context.playwright = sync_playwright().start()
        context.browser = context.playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

    # Initialize browser-use for LLM tests
    if test_type in ['llm', 'all']:
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

        print(f"\nUsing LLM Configuration:")
        print(f"Provider: {context.llm_provider}")
        print(f"Model: {context.llm_model}")
        print(f"Base URL: {context.llm_base_url}")

        # Initialize LLM
        from src.utils import utils
        context.llm = utils.get_llm_model(
            provider=context.llm_provider,
            model_name=context.llm_model,
            temperature=0.5,
            base_url=context.llm_base_url,
            api_key=context.llm_api_key
        )

def before_scenario(context, scenario):
    if 'non-llm' in scenario.tags:
        # For non-LLM tests, use Playwright directly
        context.browser_context = context.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        context.page = context.browser_context.new_page()
    else:
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

        # Run the async initialization in the event loop
        context.loop.run_until_complete(init_browser_context())

def after_scenario(context, scenario):
    if 'non-llm' in scenario.tags:
        # For non-LLM tests, close Playwright context
        if hasattr(context, 'browser_context'):
            context.browser_context.close()
    else:
        # For LLM tests, close browser-use context
        async def cleanup_browser_context():
            if hasattr(context, 'browser_context'):
                await context.browser_context.close()
        
        # Run the async cleanup in the event loop
        context.loop.run_until_complete(cleanup_browser_context())

def after_all(context):
    # Clean up LLM browser
    if hasattr(context, 'browser_instance'):
        async def cleanup_browser():
            await context.browser_instance.close()
        
        # Run the async cleanup in the event loop
        try:
            context.loop.run_until_complete(cleanup_browser())
            pending = asyncio.all_tasks(context.loop)
            context.loop.run_until_complete(asyncio.gather(*pending))
        except:
            pass
    
    # Clean up Playwright
    if hasattr(context, 'browser'):
        context.browser.close()
    if hasattr(context, 'playwright'):
        context.playwright.stop()
    
    # Clean up event loop
    if hasattr(context, 'loop'):
        try:
            context.loop.close()
        except:
            pass
        asyncio.set_event_loop(None) 
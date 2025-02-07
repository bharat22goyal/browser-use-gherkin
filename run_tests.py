import subprocess
import os
import sys
import argparse
from setup_test_env import setup_test_environment
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

def get_available_models():
    return {
        'anthropic': [
            'claude-3-5-sonnet-20240620',
            'claude-3-opus-20240229'
        ],
        'openai': [
            'gpt-4o',
            'gpt-4',
            'gpt-3.5-turbo',
            'o3-mini'
        ],
        'deepseek': [
            'deepseek-chat',
            'deepseek-reasoner'
        ],
        'gemini': [
            'gemini-2.0-flash-exp',
            'gemini-2.0-flash-thinking-exp',
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash-8b-latest',
            'gemini-2.0-flash-thinking-exp-1219'
        ],
        'ollama': [
            'qwen2.5:7b',
            'llama2:7b',
            'deepseek-r1:14b',
            'deepseek-r1:32b'
        ],
        'azure_openai': [
            'gpt-4o',
            'gpt-4',
            'gpt-3.5-turbo'
        ],
        'mistral': [
            'pixtral-large-latest',
            'mistral-large-latest',
            'mistral-small-latest',
            'ministral-8b-latest'
        ]
    }

def get_provider_config(provider):
    """Get API key and base URL for a provider from .env file"""
    config = {
        'openai': {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'base_url': os.getenv('OPENAI_ENDPOINT', 'https://api.openai.com/v1')
        },
        'anthropic': {
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'base_url': os.getenv('ANTHROPIC_ENDPOINT', 'https://api.anthropic.com')
        },
        'mistral': {
            'api_key': os.getenv('MISTRAL_API_KEY'),
            'base_url': os.getenv('MISTRAL_ENDPOINT', 'https://api.mistral.ai/v1')
        },
        'deepseek': {
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
            'base_url': os.getenv('DEEPSEEK_ENDPOINT', 'https://api.deepseek.com')
        },
        'gemini': {
            'api_key': os.getenv('GOOGLE_API_KEY'),
            'base_url': None  # Gemini doesn't need a base URL
        },
        'ollama': {
            'api_key': None,  # Ollama doesn't need an API key
            'base_url': os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434')
        }
    }
    return config.get(provider, {})

def run_tests(test_type='llm', provider=None, model=None, base_url=None, api_key=None):
    try:
        import behave.runner
        from behave.configuration import Configuration
        from behave.__main__ import run_behave
    except ImportError:
        print("Error: behave package is not installed. Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        import behave.runner
        from behave.configuration import Configuration
        from behave.__main__ import run_behave

    # Setup test environment
    setup_test_environment()
    
    # Set environment variables for LLM if needed
    env = os.environ.copy()
    
    # Set test type in environment
    env['TEST_TYPE'] = test_type

    # Configure logging
    log_level = os.getenv('TEST_LOG_LEVEL', 'INFO').upper()
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }

    # Reset root logger
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Set up file logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"test-reports/complete_test_{timestamp}.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create and configure file handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(log_level_map.get(log_level, logging.INFO))
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level_map.get(log_level, logging.INFO))
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root.setLevel(log_level_map.get(log_level, logging.INFO))
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Configure agent loggers
    agent_loggers = [
        'browser_use.agent',
        'browser_use.browser',
        'browser_use.controller',
        'browser_use.llm',
        'browser_use.tools'
    ]
    
    for logger_name in agent_loggers:
        agent_logger = logging.getLogger(logger_name)
        agent_logger.setLevel(log_level_map.get(log_level, logging.INFO))
        agent_logger.addHandler(file_handler)
        agent_logger.addHandler(console_handler)
    
    # Log initial message
    logging.info(f"Log file created at: {log_file}")
    
    # Print test configuration
    print(f"\nRunning {test_type} tests")
    if test_type == 'llm':
        # If provider is specified, update environment variables
        if provider:
            env['TEST_LLM_PROVIDER'] = provider
            provider_config = get_provider_config(provider)
            if api_key:
                env['TEST_LLM_API_KEY'] = api_key
            if base_url:
                env['TEST_LLM_BASE_URL'] = base_url
            if model:
                env['TEST_LLM_MODEL'] = model

        logging.info("\nUsing LLM Configuration:")
        logging.info(f"Provider: {env.get('TEST_LLM_PROVIDER', 'default from .env')}")
        logging.info(f"Model: {env.get('TEST_LLM_MODEL', 'default from .env')}")
        logging.info(f"Base URL: {env.get('TEST_LLM_BASE_URL', 'default from .env')}")
    
    # Set up behave configuration with tags based on test type
    args = [
        '--format=behave_html_formatter:HTMLFormatter',
        '--outfile=test-reports/behave-report.html',
        '--format=pretty',  # Also show console output
        f'--logging-level={log_level.lower()}',  # Set behave logging level
        '--define',
        f'logging.level={log_level.lower()}'  # Pass logging level to steps
    ]
    
    # Add tag filtering based on test type
    if test_type == 'llm':
        args.append('--tags=llm')
    elif test_type == 'non-llm':
        args.append('--tags=~llm')  # Exclude LLM tests
    elif test_type == 'all':
        pass  # Don't add any tag filters to run all tests
    
    args.append('features/')
    
    try:
        # Log test configuration
        logging.info(f"Running behave with arguments: {' '.join(args)}")
        
        # Run behave with configuration
        os.environ.update(env)  # Update environment variables
        config = Configuration(args)
        run_behave(config)
        
        logging.info("\nTest execution completed. HTML report generated at test-reports/behave-report.html")
        
        # Make the report more readable by adding CSS
        report_file = 'test-reports/behave-report.html'
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                content = f.read()
            
            # Add CSS for better styling
            css = '''
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .feature { margin-bottom: 30px; }
                .scenario { margin: 20px 0; padding: 10px; background: #f5f5f5; }
                .passed { color: green; }
                .failed { color: red; }
                .skipped { color: orange; }
                .step { margin: 5px 0; }
                .description { font-style: italic; color: #666; }
            </style>
            '''
            
            content = content.replace('</head>', f'{css}</head>')
            
            with open(report_file, 'w') as f:
                f.write(content)
    except Exception as e:
        logging.error(f"\nTest execution failed with error: {str(e)}")
        raise
    finally:
        # Clean up logging handlers
        if file_handler:
            file_handler.close()
            logging.getLogger().removeHandler(file_handler)
        
        # Reset root logger to default state
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
        
        # Restore basic console logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def list_available_models():
    models = get_available_models()
    print("\nAvailable LLM Providers and Models:")
    for provider, provider_models in models.items():
        config = get_provider_config(provider)
        api_key_status = "API Key Required" if provider not in ['ollama'] else "No API Key Required"
        api_key_set = "✓ Set" if config.get('api_key') else "✗ Not Set"
        
        print(f"\n{provider.upper()}:")
        print(f"Status: {api_key_status} ({api_key_set})")
        print("Models:")
        for model in provider_models:
            print(f"  - {model}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run browser automation tests with specified configuration')
    parser.add_argument('--test-type', choices=['llm', 'non-llm', 'all'], default='llm',
                      help='Type of tests to run: llm, non-llm, or all (default: llm)')
    parser.add_argument('--provider', choices=['ollama', 'openai', 'anthropic', 'mistral', 'deepseek', 'gemini'],
                      help='LLM provider to use (optional, will use value from .env)')
    parser.add_argument('--model', help='Model name to use (optional, will use value from .env)')
    parser.add_argument('--base-url', help='Base URL for the LLM API (optional, will use default from .env)')
    parser.add_argument('--api-key', help='API key for the LLM service (optional, will use from .env)')
    parser.add_argument('--list-models', action='store_true', help='List available models for each provider')
    
    args = parser.parse_args()
    
    if args.list_models:
        list_available_models()
    else:
        # Validate model if provider is specified
        if args.provider and args.model:
            available_models = get_available_models().get(args.provider, [])
            if args.model not in available_models:
                print(f"\nWarning: Model '{args.model}' is not in the list of known models for provider '{args.provider}'")
                print("Available models for this provider:")
                for model in available_models:
                    print(f"  - {model}")
                print("\nContinuing with specified model anyway...\n")
        
        run_tests(
            test_type=args.test_type,
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key
        ) 
import subprocess
import os
import sys
import argparse
from setup_test_env import setup_test_environment
from dotenv import load_dotenv

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

def run_tests(provider=None, model=None, base_url=None, api_key=None):
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
    
    # Set environment variables for LLM if provided
    env = os.environ.copy()
    
    if provider:
        env['TEST_LLM_PROVIDER'] = provider
        # Get provider configuration from .env
        provider_config = get_provider_config(provider)
        
        # Use provided values or fall back to .env values
        api_key = api_key or provider_config.get('api_key')
        base_url = base_url or provider_config.get('base_url')
        
        if api_key:
            env['TEST_LLM_API_KEY'] = api_key
        if base_url:
            env['TEST_LLM_BASE_URL'] = base_url
            
        # Warn if API key is missing for providers that require it
        if provider not in ['ollama'] and not api_key:
            print(f"\nWarning: No API key found for {provider}. Make sure to set {provider.upper()}_API_KEY in your .env file")
    
    if model:
        env['TEST_LLM_MODEL'] = model
    
    # Print LLM configuration
    print("\nUsing LLM Configuration:")
    print(f"Provider: {env.get('TEST_LLM_PROVIDER', 'default from .env')}")
    print(f"Model: {env.get('TEST_LLM_MODEL', 'default from .env')}")
    print(f"Base URL: {env.get('TEST_LLM_BASE_URL', 'default from .env')}")
    if provider and provider != 'ollama':
        print(f"API Key: {'Set' if api_key else 'Not Set'}")
    
    # Set up behave configuration
    args = [
        '--format=behave_html_formatter:HTMLFormatter',
        '--outfile=test-reports/behave-report.html',
        '--format=pretty',  # Also show console output
        'features/'
    ]
    
    try:
        # Run behave with configuration
        os.environ.update(env)  # Update environment variables
        config = Configuration(args)
        run_behave(config)
        
        print("\nTest execution completed. HTML report generated at test-reports/behave-report.html")
        
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
        print(f"\nTest execution failed with error: {str(e)}")
        raise

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
    parser = argparse.ArgumentParser(description='Run browser automation tests with specified LLM configuration')
    parser.add_argument('--provider', choices=['ollama', 'openai', 'anthropic', 'mistral', 'deepseek', 'gemini'],
                      help='LLM provider to use')
    parser.add_argument('--model', help='Model name to use')
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
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key
        ) 
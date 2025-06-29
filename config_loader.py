import os
import yaml

def load_config():
    # Load general configuration from config.yaml (non-sensitive settings)
    config = {}
    try:
        with open('config/config.yaml', 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print("config/config.yaml not found. Using environment variables for all settings.")

    # Override/add sensitive API keys from environment variables
    config['deepgram_api_key'] = os.getenv('DEEPGRAM_API_KEY', config.get('deepgram_api_key'))
    config['gemini_api_key'] = os.getenv('GEMINI_API_KEY', config.get('gemini_api_key'))

    return config
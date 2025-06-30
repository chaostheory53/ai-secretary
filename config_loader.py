import os
import yaml
from dotenv import load_dotenv

def load_config():
    load_dotenv() # Load environment variables from .env file

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
    config['evolution_api_instance_key'] = os.getenv('EVOLUTION_API_INSTANCE_KEY', config.get('evolution_api_instance_key'))
    config['evolution_api_base_url'] = os.getenv('EVOLUTION_API_BASE_URL', config.get('evolution_api_base_url', 'http://localhost:8080'))
    config['google_calendar_credentials_path'] = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH', config.get('google_calendar_credentials_path'))

    return config
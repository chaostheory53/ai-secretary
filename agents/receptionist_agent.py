import google.generativeai as genai
from config_loader import load_config
import yaml

class ReceptionistAgent:
    def __init__(self):
        config = load_config()
        self.gemini_api_key = config.get('gemini_api_key')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in config.yaml")
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')

        # Load prompts
        with open('config/prompts.yaml', 'r') as file:
            prompts = yaml.safe_load(file)
        self.receptionist_prompt = prompts.get('receptionist_prompt')

    def determine_intent(self, user_request: str) -> str:
        prompt = self.receptionist_prompt.format(user_request=user_request)
        try:
            response = self.model.generate_content(prompt)
            # Assuming the model returns only the intent name
            intent = response.text.strip()
            return intent
        except Exception as e:
            print(f"Error determining intent: {e}")
            return "outro" # Default to 'other' on error

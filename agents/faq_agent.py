import google.generativeai as genai
from config_loader import load_config
import yaml

class FAQAgent:
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
        self.faq_prompt = prompts.get('faq_prompt')

    def answer_question(self, user_question: str) -> str:
        prompt = self.faq_prompt.format(user_question=user_question)
        try:
            response = self.model.generate_content(prompt)
            # Assuming the model returns a direct answer
            answer = response.text.strip()
            return answer
        except Exception as e:
            print(f"Error answering FAQ: {e}")
            return "Desculpe, não consegui encontrar uma resposta para sua pergunta no momento." # Default on error

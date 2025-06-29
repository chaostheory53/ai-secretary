import google.generativeai as genai
from config_loader import load_config
import yaml

class BookingAgent:
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
        self.booking_prompt = prompts.get('booking_prompt')

    def extract_booking_details(self, user_request: str) -> dict:
        prompt = self.booking_prompt.format(user_request=user_request)
        try:
            response = self.model.generate_content(prompt)
            # Assuming the model returns a JSON string
            details_str = response.text.strip()
            import json
            details = json.loads(details_str)
            return details
        except Exception as e:
            print(f"Error extracting booking details: {e}")
            return {}

    def book_appointment(self, details: dict) -> str:
        # TODO: Integrate with CalendarTool here
        # For now, just acknowledge the details
        if details:
            response = "Entendi. Você gostaria de agendar um "
            if details.get('servico'):
                response += f"{details['servico']} "
            if details.get('data'):
                response += f"para {details['data']} "
            if details.get('hora'):
                response += f"às {details['hora']} "
            if details.get('nome_barbeiro'):
                response += f"com {details['nome_barbeiro']}. "
            response += "Vou verificar a disponibilidade." # This will be replaced by actual calendar check
            return response
        else:
            return "Não consegui entender os detalhes do agendamento. Poderia repetir?"

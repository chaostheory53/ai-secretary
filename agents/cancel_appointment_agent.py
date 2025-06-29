import google.generativeai as genai
from config_loader import load_config
import yaml

class CancelAppointmentAgent:
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
        self.cancel_appointment_prompt = prompts.get('cancel_appointment_prompt')

    def extract_cancellation_details(self, user_request: str) -> dict:
        prompt = self.cancel_appointment_prompt.format(user_request=user_request)
        try:
            response = self.model.generate_content(prompt)
            # Assuming the model returns a JSON string
            details_str = response.text.strip()
            import json
            details = json.loads(details_str)
            return details
        except Exception as e:
            print(f"Error extracting cancellation details: {e}")
            return {}

    def cancel_appointment(self, details: dict) -> str:
        # TODO: Integrate with a tool to actually cancel the appointment in a database/calendar
        # For now, just acknowledge the details
        if details:
            response = "Entendi. Você deseja cancelar um agendamento. "
            if details.get('nome_completo'):
                response += f"Para {details['nome_completo']}, "
            if details.get('servico'):
                response += f"o serviço de {details['servico']} "
            if details.get('data_agendamento'):
                response += f"na data {details['data_agendamento']}. "
            response += "Vou processar o cancelamento." # This will be replaced by actual cancellation logic
            return response
        else:
            return "Não consegui entender os detalhes para o cancelamento. Poderia fornecer o nome completo, a data e o serviço?"

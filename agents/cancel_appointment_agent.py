import google.generativeai as genai
from config_loader import load_config
import yaml
from tools.calendar_tool import GoogleCalendarTool
import datetime

class CancelAppointmentAgent:
    def __init__(self, calendar_tool: GoogleCalendarTool):
        config = load_config()
        self.gemini_api_key = config.get('gemini_api_key')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in config.yaml")
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.calendar_tool = calendar_tool

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
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from model response: {e}")
            return {}
        except Exception as e:
            print(f"Error extracting cancellation details: {e}")
            return {}

    def cancel_appointment(self, details: dict) -> str:
        if details:
            nome_completo = details.get('nome_completo')
            data_agendamento_str = details.get('data_agendamento')
            servico = details.get('servico')

            if not all([nome_completo, data_agendamento_str, servico]):
                return "Desculpe, preciso do nome completo, data e serviço para cancelar o agendamento. Poderia fornecer?"

            try:
                # For demonstration, we'll assume we can find the event by searching for it.
                # In a real application, you'd likely have an event ID stored somewhere.
                # For now, let's simulate finding an event ID.
                # This part needs actual implementation to search for the event and get its ID.
                # For simplicity, let's assume a dummy event_id for now.
                # You would need to implement a search function in GoogleCalendarTool to find the event_id.
                
                # Example: Search for events on the given date and service
                # This is a placeholder. Actual implementation would involve more robust search.
                data_obj = datetime.datetime.strptime(data_agendamento_str, '%d/%m/%Y').date()
                start_of_day = datetime.datetime.combine(data_obj, datetime.time.min)
                end_of_day = datetime.datetime.combine(data_obj, datetime.time.max)

                events = self.calendar_tool.list_events(start_of_day, end_of_day)
                event_to_cancel = None
                for event in events:
                    if servico.lower() in event.get('summary', '').lower() and nome_completo.lower() in event.get('description', '').lower():
                        event_to_cancel = event
                        break

                if event_to_cancel:
                    event_id = event_to_cancel['id']
                    if self.calendar_tool.cancel_event(event_id):
                        return f"Agendamento de {servico} para {nome_completo} em {data_agendamento_str} cancelado com sucesso."
                    else:
                        return "Não foi possível cancelar o agendamento no Google Calendar. Por favor, tente novamente mais tarde."
                else:
                    return "Não encontrei um agendamento correspondente com os detalhes fornecidos."

            except ValueError:
                return "Formato de data inválido. Por favor, use DD/MM/YYYY para a data."
            except ConnectionError as e:
                print(f"Connection error during cancellation: {e}")
                return "Não foi possível conectar ao serviço de calendário. Verifique sua conexão e tente novamente."
            except Exception as e:
                print(f"An unexpected error occurred during appointment cancellation: {e}")
                return "Ocorreu um erro inesperado ao tentar cancelar seu agendamento. A equipe de suporte foi notificada."
        else:
            return "Não consegui entender os detalhes para o cancelamento. Poderia fornecer o nome completo, a data e o serviço?"

import google.generativeai as genai
from config_loader import load_config
import yaml
from tools.calendar_tool import GoogleCalendarTool
import datetime
from service_manager import ServiceManager
from contextlib import contextmanager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BookingError(Exception):
    """Custom exception for booking errors"""
    pass

class ServiceNotFoundError(BookingError):
    """Raised when service is not found"""
    pass

class TimeSlotUnavailableError(BookingError):
    """Raised when requested time slot is unavailable"""
    pass

class Config:
    """Centralized configuration management"""
    def __init__(self):
        self.config = load_config()
        self._validate_config()
    
    def _validate_config(self):
        required_keys = [
            'deepgram_api_key',
            'gemini_api_key', 
            'evolution_api_instance_key'
        ]
        
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"Missing required configuration: {key}")
    
    @property
    def session_timeout_minutes(self):
        return self.config.get('session_timeout_minutes', 5)
    
    @property
    def max_booking_attempts(self):
        return self.config.get('max_booking_attempts', 48)

class BookingAgent:
    def __init__(self, calendar_tool: GoogleCalendarTool):
        config = load_config()
        self.gemini_api_key = config.get('gemini_api_key')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in config.yaml")
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.calendar_tool = calendar_tool
        self.service_manager = ServiceManager()

        # Load prompts
        with open('config/prompts.yaml', 'r') as file:
            prompts = yaml.safe_load(file)
        self.booking_prompt = prompts.get('booking_prompt')

    def round_to_next_20_minutes(self, dt: datetime.datetime) -> datetime.datetime:
        """Round a datetime to the next 20-minute slot (00, 20, 40)."""
        minute = ((dt.minute // 20) + (1 if dt.minute % 20 else 0)) * 20
        if minute == 60:
            dt = dt.replace(hour=dt.hour + 1, minute=0)
        else:
            dt = dt.replace(minute=minute)
        return dt.replace(second=0, microsecond=0)

    def find_next_available_slot(self, requested_datetime: datetime.datetime, duration_minutes: int) -> datetime.datetime:
        """Find the next available 20-minute slot that can accommodate the service duration."""
        # Start with the rounded requested time
        start_datetime = self.round_to_next_20_minutes(requested_datetime)
        
        # Get all events for the day
        day_start = start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = start_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        try:
            events = self.calendar_tool.list_events(day_start, day_end)
        except Exception as e:
            print(f"Error listing events: {e}")
            # If we can't check events, just use the rounded time
            return start_datetime
        
        # Check for conflicts and find next available slot
        max_attempts = 48  # Maximum attempts (24 hours * 2 slots per hour)
        attempts = 0
        
        while attempts < max_attempts:
            end_datetime = start_datetime + datetime.timedelta(minutes=duration_minutes)
            
            # Check if this slot conflicts with any existing events
            has_conflict = False
            for event in events:
                try:
                    event_start = datetime.datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    event_end = datetime.datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                    
                    # Check for overlap
                    if (start_datetime < event_end and end_datetime > event_start):
                        has_conflict = True
                        break
                except Exception as e:
                    print(f"Error parsing event time: {e}")
                    continue
            
            if not has_conflict:
                return start_datetime
            
            # Move to next 20-minute slot
            start_datetime += datetime.timedelta(minutes=20)
            attempts += 1
        
        # If no slot found, return the original rounded time
        return self.round_to_next_20_minutes(requested_datetime)

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
        if details:
            servico = details.get('servico')
            data_str = details.get('data')
            hora_str = details.get('hora')
            nome_barbeiro = details.get('nome_barbeiro')

            if not all([servico, data_str, hora_str]):
                return "Desculpe, preciso do serviço, data e hora para agendar. Poderia fornecer?"

            try:
                # Type checking to ensure we have valid strings
                if not isinstance(data_str, str) or not isinstance(hora_str, str) or not isinstance(servico, str):
                    return "Dados inválidos recebidos. Por favor, tente novamente."
                
                # Parse the requested date and time
                data_obj = datetime.datetime.strptime(data_str, '%d/%m/%Y').date()
                hora_obj = datetime.datetime.strptime(hora_str, '%H:%M').time()
                requested_datetime = datetime.datetime.combine(data_obj, hora_obj)
                
                # Get service duration
                duration_minutes = self.service_manager.get_service_duration_minutes(servico)
                
                # Find the next available 20-minute slot
                start_datetime = self.find_next_available_slot(requested_datetime, duration_minutes)
                end_datetime = start_datetime + datetime.timedelta(minutes=duration_minutes)
                
                # Check if the suggested time is different from the requested time
                time_difference = abs((start_datetime - requested_datetime).total_seconds() / 60)
                suggested_time_str = start_datetime.strftime('%H:%M')
                
                summary = f"Agendamento: {servico}"
                description = f"Serviço: {servico}\nBarbeiro: {nome_barbeiro or 'Não especificado'}\nDuração: {duration_minutes} minutos"

                event_link = self.calendar_tool.create_event(summary, start_datetime, end_datetime, description)

                if event_link:
                    # If the suggested time is significantly different, mention it
                    if time_difference > 5:  # More than 5 minutes difference
                        response = f"Agendamento de {servico} confirmado para {data_str} às {suggested_time_str} (próximo horário disponível). Duração: {duration_minutes} minutos. Link do evento: {event_link}"
                    else:
                        response = f"Agendamento de {servico} para {data_str} às {suggested_time_str} com {nome_barbeiro or 'o barbeiro disponível'} confirmado. Duração: {duration_minutes} minutos. Link do evento: {event_link}"
                else:
                    response = "Não foi possível agendar no Google Calendar. Por favor, tente novamente mais tarde."
                return response
            except ValueError:
                return "Formato de data ou hora inválido. Por favor, use DD/MM/YYYY para a data e HH:MM para a hora."
            except Exception as e:
                print(f"Error during appointment booking: {e}")
                return "Ocorreu um erro ao tentar agendar seu horário. Por favor, tente novamente."
        else:
            return "Não consegui entender os detalhes do agendamento. Poderia repetir?"

    def validate_phone_number(self, phone: str) -> bool:
        """Validate Brazilian phone number format"""
        import re
        pattern = r'^\+?55\d{10,11}$'
        return bool(re.match(pattern, phone))

    def sanitize_user_input(self, text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        import html
        return html.escape(text.strip())

    def validate_service_config(self, services: dict) -> bool:
        """Validate service configuration"""
        required_fields = ['name', 'price', 'duration_minutes', 'description']
        
        for service_key, service_data in services.items():
            for field in required_fields:
                if field not in service_data:
                    raise ValueError(f"Missing required field '{field}' in service '{service_key}'")
            
            if service_data['duration_minutes'] < 0:
                raise ValueError(f"Duration cannot be negative for service '{service_key}'")
            
            if service_data['price'] < 0:
                raise ValueError(f"Price cannot be negative for service '{service_key}'")
        
        return True

class AsyncGoogleCalendarTool:
    async def list_events_async(self, time_min, time_max):
        # Async implementation for better performance
        pass

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

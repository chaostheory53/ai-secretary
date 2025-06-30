from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import datetime

class GoogleCalendarTool:
    from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import datetime
import json # Importar json

class GoogleCalendarTool:
    def __init__(self, credentials_path: str):
        # O credentials_path agora é um fallback. A prioridade é a variável de ambiente.
        self.credentials_path = credentials_path
        self.creds = None
        self.service = self._authenticate()

    def _authenticate(self):
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None

        # 1. Tenta carregar o token.json existente (contém o refresh_token)
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # 2. Se não houver token válido, tenta autenticar
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # 3. Lógica de autenticação principal: prioriza a variável de ambiente
                creds_json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
                if creds_json_str:
                    # Se a variável de ambiente existe (ideal para produção/EasyPanel)
                    creds_info = json.loads(creds_json_str)
                    flow = InstalledAppFlow.from_client_config(creds_info, SCOPES)
                elif self.credentials_path and os.path.exists(self.credentials_path):
                    # Senão, usa o arquivo (ideal para desenvolvimento local)
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                else:
                    raise FileNotFoundError(
                        "Não foi possível encontrar as credenciais do Google. "
                        "Defina a variável de ambiente GOOGLE_CREDENTIALS_JSON ou "
                        "verifique o caminho em GOOGLE_CALENDAR_CREDENTIALS_PATH."
                    )
                
                creds = flow.run_local_server(port=0)

            # 4. Salva o novo token para as próximas execuções
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.creds = creds
        return build('calendar', 'v3', credentials=self.creds)

    def create_event(self, summary: str, start_time: datetime.datetime, end_time: datetime.datetime, description: str = '', attendees: list = None):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'attendees': [{'email': att} for att in attendees] if attendees else [],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f'Event created: {event.get('htmlLink')}')
            return event.get('htmlLink')
        except Exception as e:
            print(f'Error creating event: {e}')
            return None

    def cancel_event(self, event_id: str) -> bool:
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            print(f'Event {event_id} cancelled successfully.')
            return True
        except Exception as e:
            print(f'Error cancelling event {event_id}: {e}')
            return False

    def list_events(self, time_min: datetime.datetime, time_max: datetime.datetime):
        try:
            events_result = self.service.events().list(calendarId='primary', timeMin=time_min.isoformat() + 'Z', timeMax=time_max.isoformat() + 'Z', singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])
            return events
        except Exception as e:
            print(f'Error listing events: {e}')
            return []

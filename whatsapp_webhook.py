from flask import Flask, request, jsonify
import os
import requests
import threading
import time
from collections import defaultdict
from deepgram import DeepgramClient, PrerecordedOptions
from agents.receptionist_agent import ReceptionistAgent
from agents.booking_agent import BookingAgent
from agents.faq_agent import FAQAgent
from agents.cancel_appointment_agent import CancelAppointmentAgent
from tools.evolution_api_client import EvolutionAPIClient
from tools.calendar_tool import GoogleCalendarTool
from database import SessionLocal, engine
from models import Base, Client, ConversationSummary
from client_manager import ClientManager
from config_loader import load_config
from datetime import datetime, timedelta

app = Flask(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Load configuration
config = load_config()
DEEPGRAM_API_KEY = config.get('deepgram_api_key')
GOOGLE_CALENDAR_CREDENTIALS_PATH = config.get('google_calendar_credentials_path')

# Ensure API keys are available
if not DEEPGRAM_API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable not set.")
if not GOOGLE_CALENDAR_CREDENTIALS_PATH:
    raise ValueError("GOOGLE_CALENDAR_CREDENTIALS_PATH environment variable not set.")

EVOLUTION_API_BASE_URL = config.get('evolution_api_base_url')
EVOLUTION_API_INSTANCE_KEY = config.get('evolution_api_instance_key')

if not EVOLUTION_API_BASE_URL:
    raise ValueError("EVOLUTION_API_BASE_URL not set in config.")
if not EVOLUTION_API_INSTANCE_KEY:
    raise ValueError("EVOLUTION_API_INSTANCE_KEY environment variable not set. Please set it for production.")

# Initialize agents and clients
receptionist_agent = ReceptionistAgent()
google_calendar_tool = GoogleCalendarTool(GOOGLE_CALENDAR_CREDENTIALS_PATH)
booking_agent = BookingAgent(google_calendar_tool)
faq_agent = FAQAgent()
cancel_appointment_agent = CancelAppointmentAgent(google_calendar_tool)
evolution_api_client = EvolutionAPIClient(EVOLUTION_API_BASE_URL, EVOLUTION_API_INSTANCE_KEY)

SESSION_TIMEOUT_MINUTES = 5
MESSAGE_BUFFER_DELAY = 15  # 15 seconds delay

# Message buffering system
message_buffers = defaultdict(list)
message_timers = {}
timer_lock = threading.Lock()

def process_buffered_messages(phone_number):
    """Process all buffered messages for a phone number after 15-second delay"""
    print(f"Processing buffered messages for {phone_number}")
    
    with timer_lock:
        if phone_number in message_buffers and message_buffers[phone_number]:
            messages = message_buffers[phone_number]
            message_buffers[phone_number] = []
            
            # Combine all text messages into one context
            text_messages = [msg.get('body', '') for msg in messages if msg.get('body')]
            combined_text = " ".join(text_messages)
            
            if combined_text.strip():
                print(f"Combined text from {len(messages)} messages: {combined_text}")
                process_single_message(phone_number, combined_text, messages[-1])
            else:
                print(f"No text content found in buffered messages for {phone_number}")
        
        # Clean up timer reference
        if phone_number in message_timers:
            del message_timers[phone_number]

def schedule_message_processing(phone_number, message):
    """Schedule message processing with 15-second delay"""
    print(f"Scheduling message processing for {phone_number}")
    
    with timer_lock:
        # Cancel existing timer if it exists
        if phone_number in message_timers:
            print(f"Cancelling existing timer for {phone_number}")
            message_timers[phone_number].cancel()
        
        # Add message to buffer
        message_buffers[phone_number].append(message)
        print(f"Added message to buffer. Total buffered: {len(message_buffers[phone_number])}")
        
        # Create new timer
        timer = threading.Timer(MESSAGE_BUFFER_DELAY, process_buffered_messages, args=[phone_number])
        message_timers[phone_number] = timer
        timer.start()
        print(f"Started {MESSAGE_BUFFER_DELAY}-second timer for {phone_number}")

def process_single_message(phone_number, user_text, original_message):
    """Process a single message with all the existing logic"""
    print(f"Processing message for {phone_number}: {user_text}")
    
    db = SessionLocal()
    client_manager = ClientManager(db)
    
    try:
        client = client_manager.get_or_create_client(phone_number)
        print(f"Client: {client.name or 'Novo Cliente'} ({client.phone_number})")

        # Check for session timeout
        if client.is_active_session and client.last_interaction_timestamp:
            time_since_last_interaction = datetime.now() - client.last_interaction_timestamp
            if time_since_last_interaction > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                client.is_active_session = False
                client_manager.update_client(client)
                print(f"Session for {client.phone_number} timed out.")

        intent = receptionist_agent.determine_intent(user_text)
        print(f"Determined intent: {intent}")

        agent_response = "Desculpe, não entendi sua solicitação."

        if not client.is_active_session:
            # Secretary is in standby mode
            if intent == 'ativar_secretaria' or intent == 'agendar_horario' or intent == 'fazer_pergunta' or intent == 'cancelar_horario':
                client.is_active_session = True
                client.last_interaction_timestamp = datetime.now()
                client_manager.update_client(client)
                agent_response = "Olá! Sou a secretária virtual da barbearia. Como posso ajudar você hoje?"
                if client.name:
                    agent_response = f"Olá {client.name}! Sou a secretária virtual da barbearia. Como posso ajudar você hoje?"
                
                # If the activation intent was also a request, process it
                if intent == 'agendar_horario':
                    booking_details = booking_agent.extract_booking_details(user_text)
                    agent_response += "\n" + booking_agent.book_appointment(booking_details)
                elif intent == 'fazer_pergunta':
                    agent_response += "\n" + faq_agent.answer_question(user_text)
                elif intent == 'cancelar_horario':
                    cancellation_details = cancel_appointment_agent.extract_cancellation_details(user_text)
                    agent_response += "\n" + cancel_appointment_agent.cancel_appointment(cancellation_details)
            else:
                agent_response = "Olá! Sou a secretária virtual da barbearia. Estou em modo de espera. Se precisar de ajuda, diga 'Olá secretária' ou pergunte sobre horários/serviços."
        else:
            # Session is active
            client.last_interaction_timestamp = datetime.now()
            client_manager.update_client(client)

            if intent == 'agendar_horario':
                booking_details = booking_agent.extract_booking_details(user_text)
                agent_response = booking_agent.book_appointment(booking_details)
            elif intent == 'fazer_pergunta':
                agent_response = faq_agent.answer_question(user_text)
            elif intent == 'cancelar_horario':
                cancellation_details = cancel_appointment_agent.extract_cancellation_details(user_text)
                agent_response = cancel_appointment_agent.cancel_appointment(cancellation_details)
            elif intent == 'desativar_secretaria':
                client.is_active_session = False
                client_manager.update_client(client)
                agent_response = "Certo! Estarei aqui se precisar de mais alguma coisa. Tenha um ótimo dia!"
            elif intent == 'outro':
                if client.name:
                    agent_response = f"Olá {client.name}! Como posso ajudar você hoje?"
                else:
                    agent_response = "Olá! Como posso ajudar você hoje?"

        print(f"Sending response to {phone_number}: {agent_response}")
        evolution_api_client.send_message(phone_number, agent_response)

        # Save conversation summary
        client_manager.add_conversation_summary(client.id, user_text, agent_response)
        
    except Exception as e:
        print(f"Error processing message for {phone_number}: {e}")
    finally:
        db.close()

def process_audio_message(message):
    """Process audio messages immediately (they're usually complete thoughts)"""
    from_number = message.get('from')
    audio_url = message.get('fileUrl')
    
    if not audio_url:
        print("Audio message received but no fileUrl found.")
        return
    
    print(f"Processing audio message from {from_number}")
    
    try:
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        source = {'url': audio_url}
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language="pt-BR",
            punctuate=True
        )

        response = deepgram.listen.rest.v("1").transcribe_url(source, options)
        user_text = response.results.channels[0].alternatives[0].transcript
        print(f"Transcribed audio: {user_text}")
        
        # Process audio message immediately (no buffering)
        process_single_message(from_number, user_text, message)
        
    except Exception as e:
        print(f"Error processing audio: {e}")

@app.route('/webhook/evolution', methods=['POST'])
def evolution_webhook():
    data = request.json
    print(f"Received webhook data: {data}")

    messages = data.get('messages', [])

    for message in messages:
        message_type = message.get('type')
        from_number = message.get('from')

        if not from_number:
            print("No 'from' number found in message. Skipping.")
            continue

        print(f"Processing {message_type} message from {from_number}")

        if message_type == 'text':
            # Buffer text messages for 15 seconds
            schedule_message_processing(from_number, message)
        elif message_type in ['ptt', 'audio']:
            # Process audio messages immediately
            process_audio_message(message)
        else:
            print(f"Unsupported message type: {message_type}")

    return jsonify({"status": "received", "data": data}), 200

def run_webhook_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run_webhook_server()

from flask import Flask, request, jsonify
import os
import requests
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, SpeakOptions, Microphone
from config_loader import load_config
from agents.receptionist_agent import ReceptionistAgent
from agents.booking_agent import BookingAgent
from agents.faq_agent import FAQAgent
from agents.cancel_appointment_agent import CancelAppointmentAgent
from tools.evolution_api_client import EvolutionAPIClient

app = Flask(__name__)

# Load configuration
config = load_config()
DEEPGRAM_API_KEY = config.get('deepgram_api_key')

# Ensure API keys are available
if not DEEPGRAM_API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable not set.")

EVOLUTION_API_BASE_URL = os.environ.get('EVOLUTION_API_BASE_URL', 'http://localhost:8080') # Default to localhost for development
EVOLUTION_API_INSTANCE_KEY = os.environ.get('EVOLUTION_API_INSTANCE_KEY') # MUST be set as an environment variable

if not EVOLUTION_API_INSTANCE_KEY:
    raise ValueError("EVOLUTION_API_INSTANCE_KEY environment variable not set. Please set it for production.")

# Initialize agents and clients
receptionist_agent = ReceptionistAgent()
booking_agent = BookingAgent()
faq_agent = FAQAgent()
cancel_appointment_agent = CancelAppointmentAgent()
evolution_api_client = EvolutionAPIClient(EVOLUTION_API_BASE_URL, EVOLUTION_API_INSTANCE_KEY)

@app.route('/webhook/evolution', methods=['POST'])
def evolution_webhook():
    data = request.json
    print(f"Received webhook data: {data}")

    messages = data.get('messages', [])

    for message in messages:
        message_type = message.get('type')
        user_text = None
        from_number = message.get('from') # The sender's number

        if message_type == 'text':
            user_text = message.get('body')
            print(f"Text message from {from_number}: {user_text}")
        elif message_type == 'ptt' or message_type == 'audio':
            audio_url = message.get('fileUrl')
            if audio_url:
                print(f"Audio message from {from_number}: {audio_url}")
                try:
                    audio_response = requests.get(audio_url)
                    audio_response.raise_for_status()

                    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
                    source = {'buffer': audio_response.content, 'mimetype': audio_response.headers['Content-Type']}
                    options = {"punctuate": True, "language": "pt-BR"}

                    response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)
                    user_text = response.results.channels[0].alternatives[0].transcript
                    print(f"Transcribed audio: {user_text}")

                except Exception as e:
                    print(f"Error processing audio: {e}")
            else:
                print("Audio message received but no fileUrl found.")
        else:
            print(f"Unsupported message type: {message_type}")

        if user_text and from_number:
            intent = receptionist_agent.determine_intent(user_text)
            print(f"Determined intent: {intent}")

            agent_response = "Desculpe, não entendi sua solicitação." # Default response

            if intent == 'agendar_horario':
                booking_details = booking_agent.extract_booking_details(user_text)
                agent_response = booking_agent.book_appointment(booking_details)
            elif intent == 'fazer_pergunta':
                agent_response = faq_agent.answer_question(user_text)
            elif intent == 'cancelar_horario':
                cancellation_details = cancel_appointment_agent.extract_cancellation_details(user_text)
                agent_response = cancel_appointment_agent.cancel_appointment(cancellation_details)
            elif intent == 'outro':
                agent_response = "Olá! Como posso ajudar você hoje?"

            evolution_api_client.send_message(from_number, agent_response)

    return jsonify({"status": "received", "data": data}), 200

def run_webhook_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run_webhook_server()
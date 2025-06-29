from flask import Flask, request, jsonify
import os
import requests
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, SpeakOptions, Microphone
from config_loader import load_config

app = Flask(__name__)

# Load configuration
config = load_config()
DEEPGRAM_API_KEY = config.get('deepgram_api_key')

@app.route('/webhook/evolution', methods=['POST'])
def evolution_webhook():
    data = request.json
    print(f"Received webhook data: {data}")

    # Assuming evolutionAPI sends messages in a specific format
    # You might need to adjust these paths based on your actual evolutionAPI payload
    messages = data.get('messages', [])

    for message in messages:
        message_type = message.get('type')
        user_text = None

        if message_type == 'text':
            user_text = message.get('body')
            print(f"Text message from {message.get('from')}: {user_text}")
        elif message_type == 'ptt' or message_type == 'audio': # 'ptt' for push-to-talk, 'audio' for general audio
            audio_url = message.get('fileUrl') # Assuming fileUrl for audio
            if audio_url:
                print(f"Audio message from {message.get('from')}: {audio_url}")
                try:
                    # Download audio file
                    audio_response = requests.get(audio_url)
                    audio_response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

                    # Initialize Deepgram client
                    if not DEEPGRAM_API_KEY:
                        print("Deepgram API key not found in config.yaml")
                        continue

                    deepgram = DeepgramClient(DEEPGRAM_API_KEY)

                    # Transcribe audio
                    # For pt-BR, use 'pt-BR' as the language code
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

        if user_text:
            # TODO: Pass user_text to ReceptionistAgent for NLU processing
            print(f"Processed text for NLU: {user_text}")
            # Placeholder for sending response back via evolutionAPI
            # For now, just acknowledge receipt

    return jsonify({"status": "received", "data": data}), 200

def run_webhook_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run_webhook_server()
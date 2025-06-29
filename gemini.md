# Project: Barber AI Secretary

This document provides essential context for the Gemini CLI to assist in developing the 'Barber AI Secretary' application.

## Project Overview
The 'Barber AI Secretary' is a conversational AI assistant for barbershops, designed to handle appointment booking, answer FAQs, and send reminders. It features a modular, multi-agent architecture.

## Core Architecture
The system comprises:
1.  **Speech-to-Text (STT):** Uses Deepgram for transcribing voice to text.
2.  **Natural Language Understanding (NLU):** Uses Google's Gemini API for intent recognition and entity extraction, orchestrated by `ReceptionistAgent`.
3.  **Business Logic & Tools:** Python agents (`BookingAgent`, `FAQAgent`) use tools (`CalendarTool`) to interact with real-world data.
4.  **Text-to-Speech (TTS):** (Optional) For converting text responses to speech.

## Agent Preferences
- **Conciseness:** Provide concise and direct responses.

## Project Structure
```
barber-ai-secretary/
├── agents/
│   ├── receptionist_agent.py   # Routes requests to other agents
│   ├── booking_agent.py        # Handles appointment logic
│   └── faq_agent.py            # Answers frequently asked questions
├── tools/
│   └── calendar_tool.py        # Interacts with the calendar (e.g., Google Calendar)
├── config/
│   ├── config.yaml             # API keys, settings
│   └── prompts.yaml            # Prompts for the LLM
├── main.py                     # Main application entry point
├── requirements.txt            # Project dependencies
└── README.md                   # Project README
```

## Dependencies (from requirements.txt)
- deepgram-sdk
- google-generativeai
- PyYAML
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib

## Getting Started
1.  **Prerequisites:** Python 3.8+, API keys for Deepgram, Google Gemini, (Optional) Google Cloud TTS.
2.  **Installation:**
    ```bash
    git clone <your-github-repo-url>
    cd barber-ai-secretary
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Configuration:** Configure API keys in `config/config.yaml` and set up calendar authentication.
4.  **Running:** `python main.py` (listens for audio input).

## Contribution Areas
- Improving/adding agents
- Expanding tools
- Implementing TTS

# AI Secretary for Barbershop

This project is a conversational AI assistant designed to act as a virtual secretary for a barbershop. It can understand spoken requests from customers, book appointments, answer frequently asked questions, and send reminders.

The system is built with a modular, multi-agent architecture, making it easy to maintain and extend.

## 🤖 Core Architecture

The AI secretary is composed of a pipeline of specialized services that work together to create a seamless conversational experience.

1.  **Speech-to-Text (STT):** The "Ears"
    *   **Technology:** Deepgram (or a similar service)
    *   **Function:** Listens to the user's voice via a microphone and transcribes it into text. It is configured for "endpointing," meaning it waits for the user to finish speaking before sending the final transcription. This allows for natural pauses in speech without interrupting the user.

2.  **Natural Language Understanding (NLU):** The "Brain"
    *   **Technology:** Google's Gemini API
    *   **Function:** The transcribed text is sent to a powerful Large Language Model (LLM). The LLM's job is to understand the user's *intent* (e.g., `book_appointment`, `ask_question`) and extract key *entities* (e.g., `service: "haircut"`, `date: "tomorrow"`). This is orchestrated by the `ReceptionistAgent`.

3.  **Business Logic & Tools:** The "Hands"
    *   **Technology:** Python agents and tools.
    *   **Function:** Based on the intent identified by the NLU, the system routes the request to the appropriate agent (`BookingAgent`, `FAQAgent`). These agents then use "tools" to interact with real-world data, such as a `CalendarTool` to check for availability or a knowledge base for answering questions.

4.  **Text-to-Speech (TTS):** The "Voice" (Optional)
    *   **Technology:** Google Cloud TTS, ElevenLabs, etc.
    *   **Function:** Once the agent has a response, this component converts the text into natural-sounding speech to be played back to the user. *This is an optional feature and can be implemented later. Initially, responses can be text-based.*

## 📂 Project Structure

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
└── README.md                   # This file
```

## 🚀 Getting Started

### 1. Prerequisites

*   Python 3.8+
*   API keys for:
    *   Deepgram (for Speech-to-Text)
    *   Google Gemini (for Natural Language Understanding)
    *   (Optional) Google Cloud TTS (for Text-to-Speech)

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-github-repo-url>
    cd barber-ai-secretary
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    *   Open `config/config.yaml` and add your API keys.
    *   Set up authentication for your calendar tool (e.g., for Google Calendar, you'll need to follow their instructions to get a `credentials.json` file).

### 3. Running the Application

To start the AI secretary, run the main application file:

```bash
python main.py
```

The application will start listening for audio input from the microphone.

## 🛠️ How to Contribute

This project is designed to be modular. You can contribute by:

*   **Improving Agents:** Enhance the logic within the existing agents.
*   **Adding New Agents:** Create new agents for new functionalities (e.g., a `ProductAgent` to answer questions about items for sale).
*   **Expanding Tools:** Add new tools, such as an interface to a CRM or a tool for sending email/SMS notifications.
*   **Implementing TTS:** Integrate a Text-to-Speech service to give the secretary a voice.


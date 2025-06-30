# Barber AI Secretary

A conversational AI assistant for barbershops, designed to handle appointment booking, answer FAQs, and send reminders. Features a modular, multi-agent architecture with WhatsApp integration via Evolution API.

## Features

- **Multi-Agent Architecture**: Specialized agents for booking, FAQ, cancellations, and reception
- **WhatsApp Integration**: Seamless communication via Evolution API
- **Google Calendar Integration**: Automatic appointment scheduling and management
- **Speech-to-Text**: Voice message transcription using Deepgram
- **Natural Language Understanding**: Intent recognition and entity extraction with Google Gemini
- **Service Duration System**: Configurable service durations with 20-minute slot scheduling
- **Session Management**: Smart conversation flow with timeout handling
- **Production Ready**: Comprehensive error handling, logging, and health checks

## Architecture

```
barber-ai-secretary/
├── agents/
│   ├── receptionist_agent.py   # Routes requests to other agents
│   ├── booking_agent.py        # Handles appointment logic
│   ├── faq_agent.py            # Answers frequently asked questions
│   └── cancel_appointment_agent.py # Handles appointment cancellations
├── tools/
│   ├── calendar_tool.py        # Google Calendar integration
│   └── evolution_api_client.py # WhatsApp API client
├── config/
│   ├── config.yaml             # Non-sensitive configuration
│   ├── prompts.yaml            # AI prompts and responses
│   └── services.yaml           # Service definitions and pricing
├── main.py                     # Application entry point
├── whatsapp_webhook.py         # Webhook handler
├── client_manager.py           # Client session management
├── service_manager.py          # Service configuration management
├── database.py                 # Database connection and models
├── config_loader.py            # Configuration loading utility
├── requirements.txt            # Python dependencies
└── Dockerfile                  # Production container configuration
```

## Quick Start

### Prerequisites

- Python 3.8+
- API keys for:
  - Google Gemini (for NLU)
  - Deepgram (for speech-to-text)
  - Evolution API (for WhatsApp)
  - Google Calendar API credentials

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd barber-ai-secretary
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root with:
   ```env
   DEEPGRAM_API_KEY="your_deepgram_key_here"
   GEMINI_API_KEY="your_gemini_key_here"
   EVOLUTION_API_INSTANCE_KEY="your_evolution_instance_key_here"
   EVOLUTION_API_BASE_URL="http://localhost:8080"
   GOOGLE_CALENDAR_CREDENTIALS_PATH="/path/to/your/credentials.json"
   DATABASE_URL="postgresql://user:password@host:port/database_name"
   ```

4. **Set up Google Calendar credentials:**
   - Follow Google's instructions to obtain a `credentials.json` file
   - Enable Google Calendar API in your Google Cloud project
   - Place the credentials file in a secure location

5. **Run the application:**
   ```bash
   python whatsapp_webhook.py
   ```

## Local Development with Docker Compose

For a streamlined local development experience, you can use Docker Compose to start the application, the Evolution API, and a PostgreSQL database with a single command.

### Prerequisites

- Docker and Docker Compose installed.
- A `.env` file in the project root with your `GEMINI_API_KEY`, `DEEPGRAM_API_KEY`, and `GOOGLE_CREDENTIALS_JSON`.

### Running the Application

1. **Build and start the services:**
   ```bash
   docker-compose up --build
   ```
2. The application will be available at `http://localhost:5000`, and the Evolution API will be at `http://localhost:8080`.

## Configuration

### Services Configuration

Edit `config/services.yaml` to customize your barbershop services:

```yaml
services:
  corte:
    name: "Corte"
    price: 49.00
    duration_minutes: 40
    description: "Corte de cabelo tradicional"
  
  barba:
    name: "Barba"
    price: 40.00
    duration_minutes: 20
    description: "Fazer a barba"
```

### AI Prompts

Customize the AI assistant's personality and responses in `config/prompts.yaml`.

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPGRAM_API_KEY` | Deepgram API key for speech-to-text | Yes |
| `GEMINI_API_KEY` | Google Gemini API key for NLU | Yes |
| `EVOLUTION_API_INSTANCE_KEY` | Evolution API instance key | Yes |
| `EVOLUTION_API_BASE_URL` | Evolution API base URL | Yes |
| `GOOGLE_CALENDAR_CREDENTIALS_PATH` | Path to Google Calendar credentials | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |

## Security

### 🔒 Security Best Practices

This project follows security best practices:

- **No sensitive data in code**: All API keys and credentials are loaded from environment variables
- **Secure configuration**: Sensitive files are excluded from version control via `.gitignore`
- **Input validation**: All user inputs are validated and sanitized
- **Error handling**: Comprehensive error handling prevents information leakage
- **Rate limiting**: Built-in rate limiting to prevent abuse
- **Logging**: Secure logging without sensitive data exposure

### Files Excluded from Version Control

The following files are automatically excluded from Git:
- `.env` (environment variables)
- `credentials.json` (Google Calendar credentials)
- `token.json` (Google OAuth tokens)
- Planning and documentation files (not needed for app functionality)
- Database files and logs

### Production Deployment

For production deployment:
1. Set all environment variables securely in your hosting platform
2. Use HTTPS for all webhook endpoints
3. Configure proper firewall rules
4. Use a production-grade database
5. Set up monitoring and alerting

## API Endpoints

- `POST /webhook/evolution` - WhatsApp webhook endpoint
- `GET /health` - Health check endpoint

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

### Code Style

This project follows PEP 8 style guidelines. Use a linter like `flake8` or `black` for code formatting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation in the `docs/` folder
- Review the configuration guides
- Open an issue on GitHub

---

**Note**: This is a production-ready application designed for real-world barbershop operations. Ensure proper testing before deploying to production environments.

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


from sqlalchemy.orm import Session
from models import Client, ConversationSummary
from datetime import datetime
from sqlalchemy import desc
import google.generativeai as genai
from config_loader import load_config
import yaml

CONVERSATION_HISTORY_LIMIT = 5 # Store up to 5 conversations per client

class ClientManager:
    def __init__(self, db: Session):
        self.db = db
        config = load_config()
        self.gemini_api_key = config.get('gemini_api_key')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in config.yaml")
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # Load prompts
        with open('config/prompts.yaml', 'r') as file:
            prompts = yaml.safe_load(file)
        self.summarization_prompt = prompts.get('summarization_prompt')

    def get_or_create_client(self, phone_number: str) -> Client:
        client = self.db.query(Client).filter(Client.phone_number == phone_number).first()
        if not client:
            client = Client(phone_number=phone_number)
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
        return client

    def update_client(self, client: Client, **kwargs) -> Client:
        for key, value in kwargs.items():
            setattr(client, key, value)
        self.db.commit()
        self.db.refresh(client)
        return client

    def add_conversation_summary(self, client_id: int, user_input: str, agent_response: str):
        # Summarize the conversation
        prompt = self.summarization_prompt.format(user_input=user_input, agent_response=agent_response)
        try:
            response = self.model.generate_content(prompt)
            summarized_text = response.text.strip()
        except Exception as e:
            print(f"Error summarizing conversation: {e}. Using raw user input as summary.")
            summarized_text = user_input # Fallback to raw user input on error

        # Add the new conversation summary
        summary = ConversationSummary(
            client_id=client_id,
            summary=summarized_text,
            agent_response=agent_response,
            timestamp=datetime.now()
        )
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)

        # Clean up old conversations if limit is exceeded
        existing_conversations = self.db.query(ConversationSummary).filter(ConversationSummary.client_id == client_id).order_by(desc(ConversationSummary.timestamp)).all()
        if len(existing_conversations) > CONVERSATION_HISTORY_LIMIT:
            # Delete the oldest conversation(s)
            conversations_to_delete = existing_conversations[CONVERSATION_HISTORY_LIMIT:]
            for old_summary in conversations_to_delete:
                self.db.delete(old_summary)
            self.db.commit()

        return summary

    def get_client_conversation_history(self, client_id: int, limit: int = CONVERSATION_HISTORY_LIMIT) -> list[ConversationSummary]:
        return self.db.query(ConversationSummary).filter(ConversationSummary.client_id == client_id).order_by(desc(ConversationSummary.timestamp)).limit(limit).all()

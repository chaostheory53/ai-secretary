from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    birthday = Column(String, nullable=True) # Storing as string for flexibility (e.g., "DD/MM")
    preferred_service = Column(String, nullable=True)
    preferred_barber = Column(String, nullable=True)
    last_visit_date = Column(DateTime, nullable=True)
    total_appointments = Column(Integer, default=0)
    loyalty_status = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_active_session = Column(Boolean, default=False) # New field
    last_interaction_timestamp = Column(DateTime, nullable=True) # New field
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    conversations = relationship("ConversationSummary", back_populates="client", order_by="ConversationSummary.timestamp.desc()", limit=5)

class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    summary = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=True)

    client = relationship("Client", back_populates="conversations")

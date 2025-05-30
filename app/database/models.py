# app/database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from enum import Enum
import os

Base = declarative_base()

# Use JSONB for PostgreSQL, JSON for others
USE_CLOUD_SQL = os.getenv("USE_CLOUD_SQL", "true").lower() == "true"
JsonType = JSONB if USE_CLOUD_SQL else JSON

class HypothesisStatus(str, Enum):
    ACTIVE = "active"
    ON_SCHEDULE = "on_schedule"
    ON_DEMAND = "on_demand"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TradingHypothesis(Base):
    __tablename__ = "hypotheses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)  # Increased length for longer titles
    description = Column(Text)
    thesis = Column(Text)
    confidence_score = Column(Float, default=0.0)
    status = Column(String(50), default=HypothesisStatus.ACTIVE)
    target_price = Column(Float)
    current_price = Column(Float)
    instruments = Column(JsonType)  # Use JSONB for PostgreSQL
    timeframe = Column(String(100))
    success_criteria = Column(Text)
    risk_factors = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    last_analysis_at = Column(DateTime, index=True)
    
    # Relationships
    contradictions = relationship("Contradiction", back_populates="hypothesis", cascade="all, delete-orphan")
    confirmations = relationship("Confirmation", back_populates="hypothesis", cascade="all, delete-orphan")
    research_data = relationship("ResearchData", back_populates="hypothesis", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="hypothesis", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="hypothesis", cascade="all, delete-orphan")

class Contradiction(Base):
    __tablename__ = "contradictions"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id", ondelete="CASCADE"), index=True)
    quote = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    source = Column(String(500))
    strength = Column(String(50), index=True)  # Strong, Medium, Weak
    url = Column(String(1000))
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    hypothesis = relationship("TradingHypothesis", back_populates="contradictions")

class Confirmation(Base):
    __tablename__ = "confirmations"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id", ondelete="CASCADE"), index=True)
    quote = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    source = Column(String(500))
    strength = Column(String(50), index=True)  # Strong, Medium, Weak
    url = Column(String(1000))
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    hypothesis = relationship("TradingHypothesis", back_populates="confirmations")

class ResearchData(Base):
    __tablename__ = "research_data"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id", ondelete="CASCADE"), index=True)
    summary = Column(Text)
    market_data = Column(JsonType)
    news_data = Column(JsonType)
    analysis_type = Column(String(100), index=True)  # research, synthesis, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    hypothesis = relationship("TradingHypothesis", back_populates="research_data")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id", ondelete="CASCADE"), index=True)
    alert_type = Column(String(50), index=True)  # recommendation, warning, trigger
    message = Column(Text, nullable=False)
    priority = Column(String(50), default="medium", index=True)  # high, medium, low
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    hypothesis = relationship("TradingHypothesis", back_populates="alerts")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id", ondelete="CASCADE"), index=True)
    symbol = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    hypothesis = relationship("TradingHypothesis", back_populates="price_history")

# Additional table for RAG integration (if needed for sync)
class DocumentSync(Base):
    __tablename__ = "document_sync"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id", ondelete="CASCADE"), index=True)
    document_id = Column(String(100), index=True)  # Reference to RAG document
    sync_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    hypothesis = relationship("TradingHypothesis")

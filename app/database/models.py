# app/database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

class HypothesisStatus(str, Enum):
    ACTIVE = "active"
    ON_SCHEDULE = "on_schedule"
    ON_DEMAND = "on_demand"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TradingHypothesis(Base):
    __tablename__ = "hypotheses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    thesis = Column(Text)
    confidence_score = Column(Float, default=0.0)
    status = Column(String(50), default=HypothesisStatus.ACTIVE)
    target_price = Column(Float)
    current_price = Column(Float)
    instruments = Column(JSON)  # List of symbols/instruments
    timeframe = Column(String(50))
    success_criteria = Column(Text)
    risk_factors = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analysis_at = Column(DateTime)
    
    # Relationships
    contradictions = relationship("Contradiction", back_populates="hypothesis")
    confirmations = relationship("Confirmation", back_populates="hypothesis")
    research_data = relationship("ResearchData", back_populates="hypothesis")
    alerts = relationship("Alert", back_populates="hypothesis")
    price_history = relationship("PriceHistory", back_populates="hypothesis")

class Contradiction(Base):
    __tablename__ = "contradictions"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id"))
    quote = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    source = Column(String(255))
    strength = Column(String(50))  # Strong, Medium, Weak
    url = Column(String(500))
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hypothesis = relationship("TradingHypothesis", back_populates="contradictions")

class Confirmation(Base):
    __tablename__ = "confirmations"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id"))
    quote = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    source = Column(String(255))
    strength = Column(String(50))  # Strong, Medium, Weak
    url = Column(String(500))
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hypothesis = relationship("TradingHypothesis", back_populates="confirmations")

class ResearchData(Base):
    __tablename__ = "research_data"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id"))
    summary = Column(Text)
    market_data = Column(JSON)
    news_data = Column(JSON)
    analysis_type = Column(String(50))  # research, synthesis, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hypothesis = relationship("TradingHypothesis", back_populates="research_data")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id"))
    alert_type = Column(String(50))  # recommendation, warning, trigger
    message = Column(Text, nullable=False)
    priority = Column(String(50), default="medium")  # high, medium, low
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hypothesis = relationship("TradingHypothesis", back_populates="alerts")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id"))
    symbol = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    hypothesis = relationship("TradingHypothesis", back_populates="price_history")

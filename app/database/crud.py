# app/database/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.models import (
    TradingHypothesis, Contradiction, Confirmation, 
    ResearchData, Alert, PriceHistory
)
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

class HypothesisCRUD:
    @staticmethod
    def create_hypothesis(db: Session, hypothesis_data: Dict[str, Any]) -> TradingHypothesis:
        """Create a new trading hypothesis."""
        db_hypothesis = TradingHypothesis(**hypothesis_data)
        db.add(db_hypothesis)
        db.commit()
        db.refresh(db_hypothesis)
        return db_hypothesis
    
    @staticmethod
    def get_hypothesis(db: Session, hypothesis_id: int) -> Optional[TradingHypothesis]:
        """Get a hypothesis by ID."""
        return db.query(TradingHypothesis).filter(TradingHypothesis.id == hypothesis_id).first()
    
    @staticmethod
    def get_hypotheses(db: Session, skip: int = 0, limit: int = 100) -> List[TradingHypothesis]:
        """Get all hypotheses with pagination."""
        return db.query(TradingHypothesis).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_hypothesis(db: Session, hypothesis_id: int, update_data: Dict[str, Any]) -> Optional[TradingHypothesis]:
        """Update a hypothesis."""
        db_hypothesis = db.query(TradingHypothesis).filter(TradingHypothesis.id == hypothesis_id).first()
        if db_hypothesis:
            for key, value in update_data.items():
                setattr(db_hypothesis, key, value)
            db_hypothesis.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_hypothesis)
        return db_hypothesis
    
    @staticmethod
    def delete_hypothesis(db: Session, hypothesis_id: int) -> bool:
        """Delete a hypothesis."""
        db_hypothesis = db.query(TradingHypothesis).filter(TradingHypothesis.id == hypothesis_id).first()
        if db_hypothesis:
            db.delete(db_hypothesis)
            db.commit()
            return True
        return False

class ContradictionCRUD:
    @staticmethod
    def create_contradiction(db: Session, contradiction_data: Dict[str, Any]) -> Contradiction:
        """Create a new contradiction."""
        db_contradiction = Contradiction(**contradiction_data)
        db.add(db_contradiction)
        db.commit()
        db.refresh(db_contradiction)
        return db_contradiction
    
    @staticmethod
    def get_contradictions_by_hypothesis(db: Session, hypothesis_id: int) -> List[Contradiction]:
        """Get all contradictions for a hypothesis."""
        return db.query(Contradiction).filter(Contradiction.hypothesis_id == hypothesis_id).all()

class ConfirmationCRUD:
    @staticmethod
    def create_confirmation(db: Session, confirmation_data: Dict[str, Any]) -> Confirmation:
        """Create a new confirmation."""
        db_confirmation = Confirmation(**confirmation_data)
        db.add(db_confirmation)
        db.commit()
        db.refresh(db_confirmation)
        return db_confirmation
    
    @staticmethod
    def get_confirmations_by_hypothesis(db: Session, hypothesis_id: int) -> List[Confirmation]:
        """Get all confirmations for a hypothesis."""
        return db.query(Confirmation).filter(Confirmation.hypothesis_id == hypothesis_id).all()

class ResearchDataCRUD:
    @staticmethod
    def create_research_data(db: Session, research_data: Dict[str, Any]) -> ResearchData:
        """Create research data entry."""
        db_research = ResearchData(**research_data)
        db.add(db_research)
        db.commit()
        db.refresh(db_research)
        return db_research
    
    @staticmethod
    def get_research_data_by_hypothesis(db: Session, hypothesis_id: int) -> List[ResearchData]:
        """Get all research data for a hypothesis."""
        return db.query(ResearchData).filter(ResearchData.hypothesis_id == hypothesis_id).all()

class AlertCRUD:
    @staticmethod
    def create_alert(db: Session, alert_data: Dict[str, Any]) -> Alert:
        """Create a new alert."""
        db_alert = Alert(**alert_data)
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert
    
    @staticmethod
    def get_alerts_by_hypothesis(db: Session, hypothesis_id: int) -> List[Alert]:
        """Get all alerts for a hypothesis."""
        return db.query(Alert).filter(Alert.hypothesis_id == hypothesis_id).all()
    
    @staticmethod
    def get_unread_alerts(db: Session) -> List[Alert]:
        """Get all unread alerts."""
        return db.query(Alert).filter(Alert.is_read == False).all()
    
    @staticmethod
    def mark_alert_as_read(db: Session, alert_id: int) -> Optional[Alert]:
        """Mark an alert as read."""
        db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if db_alert:
            db_alert.is_read = True
            db.commit()
            db.refresh(db_alert)
        return db_alert

class PriceHistoryCRUD:
    @staticmethod
    def create_price_entry(db: Session, price_data: Dict[str, Any]) -> PriceHistory:
        """Create a price history entry."""
        db_price = PriceHistory(**price_data)
        db.add(db_price)
        db.commit()
        db.refresh(db_price)
        return db_price
    
    @staticmethod
    def get_price_history(db: Session, hypothesis_id: int, symbol: str, days: int = 7) -> List[PriceHistory]:
        """Get price history for a symbol and hypothesis."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(PriceHistory).filter(
            PriceHistory.hypothesis_id == hypothesis_id,
            PriceHistory.symbol == symbol,
            PriceHistory.timestamp >= cutoff_date
        ).order_by(PriceHistory.timestamp).all()
    
    @staticmethod
    def get_latest_price(db: Session, hypothesis_id: int, symbol: str) -> Optional[PriceHistory]:
        """Get the latest price for a symbol."""
        return db.query(PriceHistory).filter(
            PriceHistory.hypothesis_id == hypothesis_id,
            PriceHistory.symbol == symbol
        ).order_by(desc(PriceHistory.timestamp)).first()

# Aggregate methods for dashboard
class DashboardCRUD:
    @staticmethod
    def get_hypothesis_summary(db: Session, hypothesis_id: int) -> Dict[str, Any]:
        """Get complete hypothesis summary with counts and data."""
        hypothesis = HypothesisCRUD.get_hypothesis(db, hypothesis_id)
        if not hypothesis:
            return None
        
        contradictions = ContradictionCRUD.get_contradictions_by_hypothesis(db, hypothesis_id)
        confirmations = ConfirmationCRUD.get_confirmations_by_hypothesis(db, hypothesis_id)
        alerts = AlertCRUD.get_alerts_by_hypothesis(db, hypothesis_id)
        
        # Get recent price data
        if hypothesis.instruments:
            # Assuming first instrument for trend
            symbol = hypothesis.instruments[0] if isinstance(hypothesis.instruments, list) else hypothesis.instruments.get('primary')
            price_history = PriceHistoryCRUD.get_price_history(db, hypothesis_id, symbol, days=7)
        else:
            price_history = []
        
        return {
            "hypothesis": hypothesis,
            "contradictions_count": len(contradictions),
            "confirmations_count": len(confirmations),
            "alerts_count": len(alerts),
            "contradictions_detail": contradictions,
            "confirmations_detail": confirmations,
            "price_history": price_history,
            "trend_data": [
                {"date": p.timestamp.strftime("%d/%m"), "value": p.price}
                for p in price_history
            ]
        }
    
    @staticmethod
    def get_all_hypotheses_summary(db: Session) -> List[Dict[str, Any]]:
        """Get summary for all hypotheses for dashboard cards."""
        hypotheses = HypothesisCRUD.get_hypotheses(db)
        summaries = []
        
        for hyp in hypotheses:
            summary = DashboardCRUD.get_hypothesis_summary(db, hyp.id)
            summaries.append(summary)
        
        return summaries

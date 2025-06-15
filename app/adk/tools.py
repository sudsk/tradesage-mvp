# app/adk/tools.py - Corrected for ADK v1.0.0
from typing import Dict, Any, List
import json
from app.services.market_data_service import get_market_data
from app.tools.news_data_tool import news_data_tool

def market_data_search(instrument: str) -> Dict[str, Any]:
    """Get market data for a financial instrument."""
    try:
        result = get_market_data(instrument)
        return {
            "status": "success",
            "data": result,
            "instrument": instrument
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "instrument": instrument
        }

def news_search(query: str, days: int = 7) -> Dict[str, Any]:
    """Search for financial news."""
    try:
        result = news_data_tool(query, days, "tradesage-mvp")
        return {
            "status": "success",
            "data": result,
            "query": query
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e), 
            "query": query
        }

def database_save(data_type: str, hypothesis_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Save data to the database."""
    try:
        from app.database.database import get_db
        from app.database.crud import ContradictionCRUD, ConfirmationCRUD
        
        db = next(get_db())
        
        if data_type == "contradiction":
            ContradictionCRUD.create_contradiction(db, {
                "hypothesis_id": hypothesis_id,
                **data
            })
        elif data_type == "confirmation": 
            ConfirmationCRUD.create_confirmation(db, {
                "hypothesis_id": hypothesis_id,
                **data
            })
        
        return {"status": "success", "message": f"Saved {data_type} to database"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# No need for Tool wrapper classes - functions are automatically converted

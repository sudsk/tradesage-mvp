# app/adk/tools.py
from typing import Dict, Any, List
import json
from google.adk.tools import Tool
from app.services.market_data_service import get_market_data
from app.tools.news_data_tool import news_data_tool
from app.services.hybrid_rag_service import get_hybrid_rag_service

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

async def rag_search(hypothesis: str, instruments: List[str] = None) -> Dict[str, Any]:
    """Search RAG database for historical insights."""
    try:
        rag_service = get_hybrid_rag_service()
        result = await rag_service.hybrid_research(hypothesis, instruments)
        return {
            "status": "success",
            "data": result,
            "hypothesis": hypothesis
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "hypothesis": hypothesis
        }

def database_save(data_type: str, hypothesis_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Save data to the database."""
    try:
        from app.database.database import get_db
        from app.database.crud import HypothesisCRUD, ContradictionCRUD, ConfirmationCRUD
        
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

# ADK Tool Instances
MARKET_DATA_TOOL = Tool(
    name="market_data_search",
    description="Get current market data for financial instruments",
    function=market_data_search
)

NEWS_TOOL = Tool(
    name="news_search", 
    description="Search for recent financial news and analysis",
    function=news_search
)

RAG_TOOL = Tool(
    name="rag_search",
    description="Search historical database for relevant financial insights", 
    function=rag_search
)

DATABASE_TOOL = Tool(
    name="database_save",
    description="Save analysis results to database",
    function=database_save
)

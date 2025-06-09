# app/main_with_db.py
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
#from .graph import create_graph
from .graph_hybrid import create_graph
from .database.database import get_db
from .database.crud import (
    HypothesisCRUD, ContradictionCRUD, ConfirmationCRUD, 
    ResearchDataCRUD, AlertCRUD, PriceHistoryCRUD, DashboardCRUD
)
import uvicorn
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="TradeSage AI", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the workflow graph
workflow = create_graph()

@app.get("/")
async def root():
    return {"message": "TradeSage AI - Multi-Agent Trading Analysis System with SQLite Database"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tradesage-ai"}

@app.post("/process")
async def process_hypothesis(request: Request, db: Session = Depends(get_db)):
    """Process a trading hypothesis through the TradeSage AI system and store in database."""
    try:
        # Get request data
        data = await request.json()
        logger.info(f"Received request: {data}")
        
        # Import the processor
        from app.utils.text_processor import ResponseProcessor
        
        # Extract and validate input
        mode = data.get("mode", "analyze")
        
        # Initialize state
        initial_state = {
            "input": data.get("hypothesis", "") or data.get("idea", ""),
            "mode": mode,
            "hypothesis": "",
            "processed_hypothesis": "",
            "context": {},
            "research_data": {},
            "contradictions": [],
            "synthesis": "",
            "alerts": [],
            "final_response": "",
            "error": "",
            "data_sources": {},
            "confidence_score": 0.0,
            "research_method": ""
        }
        
        # Handle different modes
        if mode == "generate":
            initial_state["hypothesis"] = "GENERATE_NEW"
            initial_state["context"] = data.get("context", {})
        elif mode == "refine":
            initial_state["hypothesis"] = data.get("idea", "")
            if not initial_state["hypothesis"]:
                raise HTTPException(status_code=400, detail="Missing idea for refinement")
        else:  # analyze mode
            initial_state["hypothesis"] = data.get("hypothesis", "")
            if not initial_state["hypothesis"]:
                raise HTTPException(status_code=400, detail="Missing hypothesis for analysis")

        logger.info(f"Processing with initial state: {initial_state}")
        
        # Process through the workflow
        result = workflow.invoke(initial_state)
        logger.info(f"Workflow result keys: {list(result.keys())}")
        
        # Check for errors
        if result.get("error"):
            logger.error(f"Workflow error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Clean and process the hypothesis title
        processed_hypothesis = result.get("processed_hypothesis", initial_state["input"])
        clean_title = ResponseProcessor.clean_hypothesis_title(processed_hypothesis)
        
        # Save to database with cleaned title
        hypothesis_data = {
            "title": clean_title,
            "description": initial_state["input"],
            "thesis": processed_hypothesis,
            "confidence_score": 0.5,  # Default
            "status": "active",
            "created_at": datetime.utcnow(),
            "instruments": ["SPY"]  # Default, should be extracted from hypothesis
        }
        
        # Create hypothesis in database
        db_hypothesis = HypothesisCRUD.create_hypothesis(db, hypothesis_data)
        
        # Initialize lists for processing
        contradiction_list = []
        confirmation_list = []
        
        # Process and save contradictions with CLEAN formatting
        if result.get("contradictions"):
            # If contradictions come as a string (LLM response), process it
            if isinstance(result["contradictions"], str):
                contradiction_list = ResponseProcessor.extract_contradictions(result["contradictions"])
            elif isinstance(result["contradictions"], list):
                contradiction_list = result["contradictions"]
            
            # Clean the contradictions for frontend display
            cleaned_contradictions = []
            for contradiction in contradiction_list:
                if isinstance(contradiction, dict):
                    # Save to database with full structure
                    contradiction_data = {
                        "hypothesis_id": db_hypothesis.id,
                        "quote": contradiction.get("quote", ""),
                        "reason": contradiction.get("reason", "Market analysis challenges this thesis"),
                        "source": contradiction.get("source", "Agent Analysis"),
                        "strength": contradiction.get("strength", "Medium")
                    }
                    ContradictionCRUD.create_contradiction(db, contradiction_data)
                    
                    # Create clean version for frontend (just the quote text)
                    cleaned_contradictions.append(contradiction.get("quote", ""))
            
            # Update the list for response
            contradiction_list = cleaned_contradictions
        
        # Process confirmations similarly
        if result.get("confirmations"):
            if isinstance(result["confirmations"], str):
                confirmation_list = ResponseProcessor.extract_confirmations(result["confirmations"])
            elif isinstance(result["confirmations"], list):
                confirmation_list = result["confirmations"]
                
            # Clean the confirmations for frontend display
            cleaned_confirmations = []
            for confirmation in confirmation_list:
                if isinstance(confirmation, dict):
                    # Save to database with full structure
                    confirmation_data = {
                        "hypothesis_id": db_hypothesis.id,
                        "quote": confirmation.get("quote", ""),
                        "reason": confirmation.get("reason", "Market data supports this thesis"),
                        "source": confirmation.get("source", "Agent Analysis"),
                        "strength": confirmation.get("strength", "Strong")
                    }
                    ConfirmationCRUD.create_confirmation(db, confirmation_data)
                    
                    # Create clean version for frontend (just the quote text)
                    cleaned_confirmations.append(confirmation.get("quote", ""))
            
            # Update the list for response
            confirmation_list = cleaned_confirmations
        
        # Add research data
        if result.get("research_data"):
            research_data = {
                "hypothesis_id": db_hypothesis.id,
                "summary": result.get("research_data", {}).get("summary", ""),
                "market_data": result.get("research_data", {}).get("market_data", {}),
                "news_data": result.get("research_data", {}).get("news_data", {}),
                "analysis_type": "research"
            }
            ResearchDataCRUD.create_research_data(db, research_data)
        
        # Save alerts
        if result.get("alerts"):
            for alert in result["alerts"]:
                if isinstance(alert, dict):
                    alert_data = {
                        "hypothesis_id": db_hypothesis.id,
                        "alert_type": "recommendation",
                        "message": alert.get("message", str(alert)),
                        "priority": "medium"
                    }
                    AlertCRUD.create_alert(db, alert_data)
        
        # Add some sample price data
        sample_prices = [82.0, 83.5, 82.8, 84.2, 83.9]
        dates = [(datetime.utcnow().date().replace(day=20 + i)) for i in range(5)]
        
        for i, price in enumerate(sample_prices):
            price_data = {
                "hypothesis_id": db_hypothesis.id,
                "symbol": "SPY",
                "price": price,
                "timestamp": datetime.combine(dates[i], datetime.min.time())
            }
            PriceHistoryCRUD.create_price_entry(db, price_data)
        
        # Return structured response with cleaned data
        response = {
            "status": "success",
            "mode": mode,
            "hypothesis_id": db_hypothesis.id,
            "input": initial_state["input"],
            "processed_hypothesis": clean_title,  # Use clean title
            "research": {
                "summary": result.get("research_data", {}).get("summary", ""),
                "market_data": result.get("research_data", {}).get("market_data", {}),
                "news_data": result.get("research_data", {}).get("news_data", {})
            },
            "contradictions": contradiction_list,  # Now contains clean strings only
            "synthesis": ResponseProcessor.process_agent_response(result.get("synthesis", ""), "general"),
            "alerts": result.get("alerts", []),
            "recommendations": ResponseProcessor.process_agent_response(result.get("final_response", ""), "general"),
            "timestamp": result.get("timestamp", datetime.utcnow().isoformat())
        }
        logger.info(f"Returning response with hypothesis_id: {db_hypothesis.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Get all hypothesis data for the dashboard."""
    try:
        summaries = DashboardCRUD.get_all_hypotheses_summary(db)
        
        # Format for frontend
        formatted_summaries = []
        for summary in summaries:
            if summary:
                hypothesis = summary["hypothesis"]
                formatted_summary = {
                    "id": hypothesis.id,
                    "title": hypothesis.title,
                    "status": hypothesis.status.replace("_", " ").title(),
                    "contradictions": summary["contradictions_count"],
                    "confirmations": summary["confirmations_count"],
                    "confidence": int(hypothesis.confidence_score * 100),
                    "lastUpdated": hypothesis.updated_at.strftime("%d/%m/%Y %H:%M"),
                    "trendData": summary["trend_data"],
                    "contradictions_detail": [
                        {
                            "quote": c.quote,
                            "reason": c.reason,
                            "source": c.source,
                            "strength": c.strength
                        } for c in summary["contradictions_detail"]
                    ],
                    "confirmations_detail": [
                        {
                            "quote": c.quote,
                            "reason": c.reason,
                            "source": c.source,
                            "strength": c.strength
                        } for c in summary["confirmations_detail"]
                    ]
                }
                formatted_summaries.append(formatted_summary)
        
        return {"status": "success", "data": formatted_summaries}
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@app.get("/hypothesis/{hypothesis_id}")
async def get_hypothesis_detail(hypothesis_id: int, db: Session = Depends(get_db)):
    """Get detailed hypothesis information."""
    try:
        summary = DashboardCRUD.get_hypothesis_summary(db, hypothesis_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
        
        return {
            "status": "success",
            "data": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hypothesis {hypothesis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """Get all unread alerts."""
    try:
        alerts = AlertCRUD.get_unread_alerts(db)
        return {
            "status": "success",
            "alerts": [
                {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "message": alert.message,
                    "priority": alert.priority,
                    "created_at": alert.created_at.isoformat()
                } for alert in alerts
            ]
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as read."""
    try:
        alert = AlertCRUD.mark_alert_as_read(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "success", "message": "Alert marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert {alert_id} as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

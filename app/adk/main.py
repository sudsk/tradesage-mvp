# app/adk/main.py  
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime
from typing import Dict, Any

from app.adk.orchestrator import orchestrator
from app.database.database import get_db
from app.database.crud import HypothesisCRUD, ContradictionCRUD, ConfirmationCRUD, AlertCRUD
from app.utils.text_processor import ResponseProcessor

app = FastAPI(title="TradeSage AI - ADK Version", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "TradeSage AI - Google ADK v1.0.0 Implementation"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tradesage-ai-adk", "version": "2.0.0"}

@app.post("/process")
async def process_hypothesis_adk(request_data: dict, db: Session = Depends(get_db)):
    """Process trading hypothesis using ADK agents."""
    
    try:
        # Extract input
        hypothesis = request_data.get("hypothesis", "")
        mode = request_data.get("mode", "analyze")
        
        if not hypothesis:
            raise HTTPException(status_code=400, detail="Missing hypothesis")
        
        print(f"🚀 Processing with ADK: {hypothesis}")
        
        # Process through ADK orchestrator
        result = await orchestrator.process_hypothesis({
            "hypothesis": hypothesis,
            "mode": mode
        })
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        # Clean and save to database
        clean_title = ResponseProcessor.clean_hypothesis_title(
            result.get("processed_hypothesis", hypothesis)
        )
        
        # Create hypothesis in database
        hypothesis_data = {
            "title": clean_title,
            "description": hypothesis,
            "thesis": result.get("processed_hypothesis", hypothesis),
            "confidence_score": result.get("confidence_score", 0.5),
            "status": "active",
            "created_at": datetime.utcnow(),
            "instruments": ["SPY"]  # Extract from context in production
        }
        
        db_hypothesis = HypothesisCRUD.create_hypothesis(db, hypothesis_data)
        
        # Save contradictions
        for contradiction in result.get("contradictions", []):
            ContradictionCRUD.create_contradiction(db, {
                "hypothesis_id": db_hypothesis.id,
                **contradiction
            })
        
        # Save confirmations
        for confirmation in result.get("confirmations", []):
            ConfirmationCRUD.create_confirmation(db, {
                "hypothesis_id": db_hypothesis.id,
                **confirmation
            })
        
        # Save alerts
        for alert in result.get("alerts", []):
            AlertCRUD.create_alert(db, {
                "hypothesis_id": db_hypothesis.id,
                "alert_type": alert.get("type", "recommendation"),
                "message": alert.get("message", ""),
                "priority": alert.get("priority", "medium")
            })
        
        # Return response
        return {
            "status": "success",
            "method": "adk_v1.0.0",
            "hypothesis_id": db_hypothesis.id,
            "processed_hypothesis": clean_title,
            "confidence_score": result.get("confidence_score", 0.5),
            "research": result.get("research_data", {}),
            "contradictions": [c.get("quote", str(c)) for c in result.get("contradictions", [])],
            "synthesis": result.get("synthesis", ""),
            "alerts": result.get("alerts", []),
            "recommendations": result.get("recommendations", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ADK processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ADK processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port from LangGraph version

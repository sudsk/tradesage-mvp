# app/adk/main.py - Updated with minor fixes
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import os 
from datetime import datetime
from typing import Dict, Any

from app.adk.orchestrator import orchestrator
from app.database.database import get_db
from app.database.crud import HypothesisCRUD, ContradictionCRUD, ConfirmationCRUD, AlertCRUD, DashboardCRUD
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
        
        # Save contradictions with validation
        cleaned_contradictions = []
        for contradiction in result.get("contradictions", []):
            if isinstance(contradiction, dict):
                try:
                    # Ensure database field limits
                    contradiction_data = {
                        "hypothesis_id": db_hypothesis.id,
                        "quote": contradiction.get("quote", "")[:500],
                        "reason": contradiction.get("reason", "Market analysis challenges this thesis")[:500],
                        "source": contradiction.get("source", "Agent Analysis")[:500],
                        "strength": contradiction.get("strength", "Medium")
                    }
                    ContradictionCRUD.create_contradiction(db, contradiction_data)
                    cleaned_contradictions.append(contradiction.get("quote", ""))
                except Exception as e:
                    print(f"⚠️  Failed to save contradiction: {str(e)}")
                    continue
        
        # Save confirmations with validation
        cleaned_confirmations = []
        for confirmation in result.get("confirmations", []):
            if isinstance(confirmation, dict):
                try:
                    # Ensure database field limits
                    confirmation_data = {
                        "hypothesis_id": db_hypothesis.id,
                        "quote": confirmation.get("quote", "")[:500],
                        "reason": confirmation.get("reason", "Market analysis supports this thesis")[:500],
                        "source": confirmation.get("source", "Agent Analysis")[:500],
                        "strength": confirmation.get("strength", "Strong")
                    }
                    ConfirmationCRUD.create_confirmation(db, confirmation_data)
                    cleaned_confirmations.append(confirmation.get("quote", ""))
                except Exception as e:
                    print(f"⚠️  Failed to save confirmation: {str(e)}")
                    continue
        
        # Save alerts with validation
        for alert in result.get("alerts", []):
            if isinstance(alert, dict):
                try:
                    alert_data = {
                        "hypothesis_id": db_hypothesis.id,
                        "alert_type": alert.get("type", "recommendation")[:50],  # Enforce limit
                        "message": alert.get("message", "")[:1000],  # Enforce limit (adjust based on your schema)
                        "priority": alert.get("priority", "medium")
                    }
                    # Validate priority
                    if alert_data["priority"] not in ["high", "medium", "low"]:
                        alert_data["priority"] = "medium"
                    
                    AlertCRUD.create_alert(db, alert_data)
                except Exception as e:
                    print(f"⚠️  Failed to save alert: {str(e)}")
                    continue
        
        # Return response with both contradictions AND confirmations
        return {
            "status": "success",
            "method": "enhanced_adk_v1.0.0",
            "hypothesis_id": db_hypothesis.id,
            "processed_hypothesis": clean_title,
            "confidence_score": result.get("confidence_score", 0.5),
            "research": result.get("research_data", {}),
            "contradictions": cleaned_contradictions,  # ✅ Now includes clean quotes
            "confirmations": cleaned_confirmations,    # ✅ Added missing confirmations
            "synthesis": result.get("synthesis", ""),
            "alerts": result.get("alerts", []),
            "recommendations": result.get("recommendations", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "processing_stats": result.get("processing_stats", {})  # ✅ Added processing stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ADK processing error: {str(e)}")
        import traceback
        traceback.print_exc()  # ✅ Better error debugging
        raise HTTPException(status_code=500, detail=f"ADK processing failed: {str(e)}")

@app.get("/dashboard")
async def get_dashboard_data_adk(db: Session = Depends(get_db)):
    """Get all hypothesis data for the dashboard - ADK version."""
    try:
        summaries = DashboardCRUD.get_all_hypotheses_summary(db)
        
        # Format for frontend (same as LangGraph version)
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
        print(f"❌ Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@app.get("/hypothesis/{hypothesis_id}")
async def get_hypothesis_detail_adk(hypothesis_id: int, db: Session = Depends(get_db)):
    """Get detailed hypothesis information - ADK version."""
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
        print(f"❌ Error getting hypothesis {hypothesis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_alerts_adk(db: Session = Depends(get_db)):
    """Get all unread alerts - ADK version."""
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
        print(f"❌ Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/alerts/{alert_id}/read")
async def mark_alert_read_adk(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as read - ADK version."""
    try:
        alert = AlertCRUD.mark_alert_as_read(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "success", "message": "Alert marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error marking alert {alert_id} as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

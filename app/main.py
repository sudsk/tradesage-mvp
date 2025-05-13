# app/main.py
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from .graph import create_graph
import uvicorn

import logging
import traceback

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
    return {"message": "TradeSage AI - Multi-Agent Trading Analysis System"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tradesage-ai"}

@app.post("/process")
async def process_hypothesis(request: Request):
    """Process a trading hypothesis through the TradeSage AI system."""
    try:
        # Get request data
        data = await request.json()
        logger.info(f"Received request: {data}")        
        
        # Extract and validate input
        mode = data.get("mode", "analyze")  # analyze, generate, refine
        
        # Initialize state
        initial_state = {
            "input": data.get("hypothesis", "") or data.get("idea", ""),
            "mode": mode,
            "hypothesis": "",
            "processed_hypothesis": "",
            "research_data": {},
            "contradictions": [],
            "synthesis": "",
            "alerts": [],
            "final_response": "",
            "error": ""
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
        logger.info(f"Workflow result: {result}")        
        
        # Check for errors
        if result.get("error"):
            logger.error(f"Workflow error: {result['error']}")            
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Return structured response
        response = {
            "status": "success",
            "mode": mode,
            "input": initial_state["input"],
            "processed_hypothesis": result.get("processed_hypothesis", ""),
            "research": {
                "summary": result.get("research_data", {}).get("summary", ""),
                "market_data": result.get("research_data", {}).get("market_data", {}),
                "news_data": result.get("research_data", {}).get("news_data", {})
            },
            "contradictions": result.get("contradictions", []),
            "synthesis": result.get("synthesis", ""),
            "alerts": result.get("alerts", []),
            "recommendations": result.get("final_response", ""),
            "timestamp": result.get("timestamp", "")
        }
        logger.info(f"Returning response: {response}")
        return response        
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/test")
async def test_endpoint():
    """Test endpoint for basic functionality."""
    test_hypothesis = "Technology stocks will outperform the market in Q2 2024 due to AI adoption"
    
    try:
        result = workflow.invoke({
            "input": test_hypothesis,
            "mode": "analyze",
            "hypothesis": test_hypothesis,
            "processed_hypothesis": "",
            "research_data": {},
            "contradictions": [],
            "synthesis": "",
            "alerts": [],
            "final_response": "",
            "error": ""
        })
        
        return {
            "status": "test_successful",
            "result": {
                "processed_hypothesis": result.get("processed_hypothesis", ""),
                "research_summary": result.get("research_data", {}).get("summary", ""),
                "contradictions_count": len(result.get("contradictions", [])),
                "synthesis_length": len(result.get("synthesis", "")),
                "alerts_count": len(result.get("alerts", []))
            }
        }
    except Exception as e:
        return {
            "status": "test_failed",
            "error": str(e)
        }

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

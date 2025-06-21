# deploy_to_agent_engine.py - Fixed for proper module import

import os
import sys
from pathlib import Path

def main():
    """Simple deployment script for TradeSage AI to Google Agent Engine"""
    
    print("🚀 TradeSage AI - Agent Engine Deployment")
    print("=" * 50)
    
    # Check environment setup
    project_id = os.getenv("PROJECT_ID", "tradesage-mvp")
    location = os.getenv("REGION", "us-central1")  
    staging_bucket = os.getenv("STAGING_BUCKET")
    
    if not staging_bucket:
        print("❌ Error: STAGING_BUCKET environment variable not set")
        print("Please set: export STAGING_BUCKET=gs://your-bucket-name")
        sys.exit(1)
    
    print(f"📋 Configuration:")
    print(f"   Project ID: {project_id}")
    print(f"   Location: {location}")
    print(f"   Staging Bucket: {staging_bucket}")
    print()
    
    # Check required files exist
    required_files = [
        "requirements.txt",
        "app/adk/orchestrator.py",
        "app/__init__.py",
        "app/adk/__init__.py"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            if file_path.endswith("__init__.py"):
                print(f"📝 Creating missing {file_path}...")
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                Path(file_path).touch()
            else:
                print(f"❌ Error: Required file {file_path} not found")
                sys.exit(1)
    
    # Check if main_agent.py exists, create if needed
    if not Path("main_agent.py").exists():
        print("📝 Creating Agent Engine wrapper (main_agent.py) in root directory...")
        create_main_agent_file()
    
    print("✅ All required files found")
    print()
    
    # Import and deploy
    try:
        print("📦 Installing required packages...")
        os.system("pip install google-cloud-aiplatform[adk,agent_engines]")
        
        print("🔧 Initializing Vertex AI...")
        import vertexai
        from vertexai import agent_engines
        from vertexai.preview import reasoning_engines
        
        # Initialize Vertex AI
        vertexai.init(
            project=project_id,
            location=location,
            staging_bucket=staging_bucket
        )
        
        print("🤖 Loading TradeSage agent...")
        # Import our agent from root directory
        from main_agent import tradesage_agent
        
        print("📊 Creating ADK App wrapper...")
        # Wrap agent for deployment
        app = reasoning_engines.AdkApp(
            agent=tradesage_agent,
            enable_tracing=True,
        )
        
        # Test locally first
        print("🧪 Testing locally...")
        test_session = app.create_session(user_id="test_user")
        print(f"   Local test session created: {test_session.id}")
        
        # Test with simple query
        print("   Running test query...")
        events = list(app.stream_query(
            user_id="test_user",
            session_id=test_session.id,
            message="Apple will reach $220 by Q2 2025"
        ))
        print(f"   ✅ Test completed with {len(events)} events")
        
        print("🚀 Deploying to Agent Engine...")
        # Deploy to Agent Engine
        remote_app = agent_engines.create(
            agent_engine=tradesage_agent,
            requirements=[
                "google-cloud-aiplatform[adk,agent_engines]>=1.72.0",
                "google-adk>=1.0.0",
                "vertexai>=1.72.0",
                "fastapi>=0.104.1",
                "uvicorn[standard]>=0.24.0",
                "sqlalchemy>=2.0.23",
                "pg8000>=1.30.3",
                "google-cloud-sql-connector>=1.10.0",
                "requests>=2.31.0",
                "beautifulsoup4>=4.12.2",
                "google-cloud-secret-manager>=2.18.0",
                "google-cloud-logging>=3.8.0",
                "pydantic>=2.5.0",
                "python-multipart>=0.0.6",
                "python-dotenv>=1.0.0",
                "python-dateutil>=2.8.2"
            ]
        )
        
        print("⏳ Deployment in progress... (this may take several minutes)")
        print(f"🎉 Successfully deployed TradeSage AI!")
        print(f"📝 Agent Resource Name: {remote_app.resource_name}")
        
        # Test remote deployment
        print("🧪 Testing remote deployment...")
        remote_session = remote_app.create_session(user_id="deployment_test")
        print(f"   Remote session created: {remote_session['id']}")
        
        # Test remote query
        remote_events = list(remote_app.stream_query(
            user_id="deployment_test",
            session_id=remote_session["id"],
            message="Test Tesla hypothesis"
        ))
        print(f"   ✅ Remote test completed with {len(remote_events)} events")
        
        print()
        print("🎉 Deployment Complete!")
        print("=" * 50)
        print(f"🔗 Agent Resource Name: {remote_app.resource_name}")
        print(f"📍 Region: {location}")
        print(f"📊 Project: {project_id}")
        print()
        print("💡 Next Steps:")
        print("1. Visit Google Cloud Console > Vertex AI > Agent Engine")
        print("2. Find your deployed agent in the list")
        print("3. Use the Agent Engine UI to monitor and manage")
        print("4. Integrate with your applications using the resource name")
        
        # Save deployment info
        deployment_info = {
            "resource_name": remote_app.resource_name,
            "project_id": project_id,
            "location": location,
            "status": "deployed"
        }
        
        with open("deployment_info.json", "w") as f:
            import json
            json.dump(deployment_info, f, indent=2)
        
        print(f"💾 Deployment info saved to deployment_info.json")
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def create_main_agent_file():
    """Create the Agent Engine wrapper file in root directory (not in app/adk)"""
    
    agent_code = '''# main_agent.py - Agent Engine wrapper for TradeSage AI (Root Level)
# NOTE: This file is in the root directory for proper import by Agent Engine

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Now import from app modules
from google.adk.agents import Agent
import asyncio
import json

# Import TradeSage orchestrator
try:
    from app.adk.orchestrator import orchestrator
    from app.adk.tools import market_data_search, news_search
except ImportError as e:
    print(f"Import error: {e}")
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path)
    raise

async def process_trading_hypothesis(hypothesis: str, mode: str = "analyze") -> dict:
    """
    Agent Engine wrapper for processing trading hypotheses.
    This wraps your existing orchestrator for cloud deployment.
    
    Args:
        hypothesis: The trading hypothesis to analyze
        mode: Processing mode (analyze, generate, refine)
        
    Returns:
        dict: Complete analysis results from your orchestrator
    """
    try:
        # Call your existing orchestrator (unchanged)
        result = await orchestrator.process_hypothesis({
            "hypothesis": hypothesis,
            "mode": mode
        })
        
        # Format response for Agent Engine
        if result.get("status") == "success":
            return {
                "status": "success",
                "hypothesis": result.get("processed_hypothesis", hypothesis),
                "confidence": result.get("confidence_score", 0.5),
                "contradictions_count": len(result.get("contradictions", [])),
                "confirmations_count": len(result.get("confirmations", [])),
                "alerts_count": len(result.get("alerts", [])),
                "analysis": result.get("synthesis", ""),
                "recommendations": result.get("recommendations", ""),
                "method": result.get("method", "adk"),
                "research_summary": result.get("research_data", {}).get("summary", "")[:500],
                "full_result": result  # Include complete result for advanced users
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "hypothesis": hypothesis
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "hypothesis": hypothesis
        }

# Create the Agent Engine-compatible agent
tradesage_agent = Agent(
    name="tradesage_ai_agent",
    model="gemini-2.0-flash",
    description="Advanced AI agent for trading hypothesis analysis and market research",
    instruction="""
    You are TradeSage AI, an advanced trading hypothesis analysis agent. 
    
    Your capabilities:
    - Analyze trading hypotheses for stocks, crypto, commodities
    - Extract structured information (asset, price targets, timeframes)
    - Conduct market research using real-time data and news
    - Identify risks and contradictions to investment thesis
    - Generate confirmations and supporting evidence
    - Calculate confidence scores based on evidence
    - Provide actionable alerts and recommendations
    
    When users provide trading hypotheses:
    1. Process and structure the hypothesis
    2. Conduct comprehensive research
    3. Analyze both supporting and contradictory evidence
    4. Provide balanced, data-driven analysis
    5. Generate specific, actionable recommendations
    
    Always be thorough, objective, and provide quantitative analysis where possible.
    """,
    tools=[process_trading_hypothesis, market_data_search, news_search]
)

# For testing this wrapper locally
if __name__ == "__main__":
    print("🤖 TradeSage AI Agent Engine Wrapper loaded successfully")
    print(f"   Agent Name: {tradesage_agent.name}")
    print(f"   Model: {tradesage_agent.model}")
    print(f"   Tools: {len(tradesage_agent.tools)}")
    print("   NOTE: This wraps your existing orchestrator system")
'''
    
    # Write the agent wrapper file in root directory
    with open("main_agent.py", "w") as f:
        f.write(agent_code)
    
    print("✅ Created main_agent.py in root directory (for Agent Engine import)")

if __name__ == "__main__":
    main()

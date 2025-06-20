# manage_agent.py - Simple management script for deployed TradeSage AI

import os
import sys
import json
from pathlib import Path
import argparse

def load_deployment_info():
    """Load deployment information from file"""
    if not Path("deployment_info.json").exists():
        print("❌ No deployment info found. Please deploy first.")
        sys.exit(1)
    
    with open("deployment_info.json", "r") as f:
        return json.load(f)

def setup_vertex_ai():
    """Setup Vertex AI with deployment info"""
    deployment_info = load_deployment_info()
    
    import vertexai
    from vertexai import agent_engines
    
    vertexai.init(
        project=deployment_info["project_id"],
        location=deployment_info["location"]
    )
    
    return agent_engines.get(deployment_info["resource_name"]), deployment_info

def test_agent(message=None):
    """Test the deployed agent"""
    print("🧪 Testing deployed TradeSage AI agent...")
    
    remote_app, info = setup_vertex_ai()
    
    # Use provided message or default
    test_message = message or "Apple stock will reach $250 by end of 2025"
    
    print(f"📨 Test message: {test_message}")
    print("⏳ Processing...")
    
    try:
        # Create test session
        session = remote_app.create_session(user_id="test_user")
        print(f"✅ Session created: {session['id']}")
        
        # Send query and collect results
        events = list(remote_app.stream_query(
            user_id="test_user",
            session_id=session["id"],
            message=test_message
        ))
        
        print(f"✅ Received {len(events)} events")
        
        # Show the final response
        for event in events:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print("📊 Agent Response:")
                            print("-" * 40)
                            print(part.text)
                            print("-" * 40)
        
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def get_agent_info():
    """Get information about the deployed agent"""
    print("📋 Agent Information")
    print("=" * 30)
    
    deployment_info = load_deployment_info()
    remote_app, info = setup_vertex_ai()
    
    print(f"🤖 Resource Name: {info['resource_name']}")
    print(f"📍 Project: {info['project_id']}")
    print(f"🌍 Region: {info['location']}")
    print(f"📅 Status: {info['status']}")
    
    try:
        # Try to get more info about the agent
        print("\n🔍 Agent Details:")
        print(f"   - Type: ADK Multi-Agent System")
        print(f"   - Purpose: Trading Hypothesis Analysis")
        print(f"   - Capabilities: Market Research, Risk Analysis, Recommendations")
        
    except Exception as e:
        print(f"⚠️ Could not fetch additional details: {str(e)}")

def list_sessions():
    """List recent sessions"""
    print("📝 Recent Sessions")
    print("=" * 20)
    
    remote_app, info = setup_vertex_ai()
    
    try:
        # This would list sessions if the API supports it
        print("ℹ️ Session listing not implemented in current Agent Engine API")
        print("💡 Visit the Agent Engine UI in Google Cloud Console to view sessions")
        print(f"🔗 https://console.cloud.google.com/vertex-ai/agent-engine?project={info['project_id']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def delete_agent():
    """Delete the deployed agent"""
    deployment_info = load_deployment_info()
    
    print("⚠️  WARNING: This will delete your deployed TradeSage AI agent!")
    print(f"🤖 Resource: {deployment_info['resource_name']}")
    
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("❌ Deletion cancelled")
        return
    
    try:
        remote_app, info = setup_vertex_ai()
        
        print("🗑️ Deleting agent...")
        remote_app.delete(force=True)
        
        print("✅ Agent deleted successfully")
        
        # Remove deployment info file
        if Path("deployment_info.json").exists():
            os.remove("deployment_info.json")
            print("✅ Deployment info file removed")
            
    except Exception as e:
        print(f"❌ Deletion failed: {str(e)}")

def main():
    """Main management interface"""
    parser = argparse.ArgumentParser(description="Manage TradeSage AI Agent on Agent Engine")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test the deployed agent")
    test_parser.add_argument("--message", "-m", help="Custom test message")
    
    # Info command
    subparsers.add_parser("info", help="Show agent information")
    
    # Sessions command
    subparsers.add_parser("sessions", help="List recent sessions")
    
    # Delete command
    subparsers.add_parser("delete", help="Delete the deployed agent")
    
    # Status command
    subparsers.add_parser("status", help="Check agent status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Install required packages if needed
    try:
        import vertexai
        from vertexai import agent_engines
    except ImportError:
        print("📦 Installing required packages...")
        os.system("pip install google-cloud-aiplatform[adk,agent_engines]")
        import vertexai
        from vertexai import agent_engines
    
    # Execute commands
    if args.command == "test":
        test_agent(args.message)
    elif args.command == "info" or args.command == "status":
        get_agent_info()
    elif args.command == "sessions":
        list_sessions()
    elif args.command == "delete":
        delete_agent()

if __name__ == "__main__":
    main()

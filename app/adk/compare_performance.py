# app/adk/compare_performance.py
import asyncio
import time
import requests
from app.adk.orchestrator import orchestrator

async def compare_langgraph_vs_adk():
    """Compare LangGraph and ADK performance."""
    
    test_hypothesis = "Tesla will reach $300 by Q3 2025"
    
    print("🔄 Performance Comparison: LangGraph vs ADK")
    print("="*50)
    
    # Test ADK Version
    print("\n🚀 Testing ADK Version...")
    start_time = time.time()
    
    try:
        adk_result = await orchestrator.process_hypothesis({
            "hypothesis": test_hypothesis,
            "mode": "analyze"
        })
        adk_time = time.time() - start_time
        adk_success = adk_result.get("status") == "success"
        
        print(f"✅ ADK Processing time: {adk_time:.2f} seconds")
        print(f"📊 ADK Status: {adk_result.get('status')}")
        print(f"🎯 ADK Confidence: {adk_result.get('confidence_score', 0):.2f}")
        
    except Exception as e:
        adk_time = time.time() - start_time
        adk_success = False
        print(f"❌ ADK failed in {adk_time:.2f} seconds: {str(e)}")
    
    # Test LangGraph Version (if running)
    print("\n📊 Testing LangGraph Version...")
    start_time = time.time()
    
    try:
        langgraph_response = requests.post(
            "http://localhost:8000/process",  # Original port
            json={"hypothesis": test_hypothesis},
            timeout=60
        )
        langgraph_time = time.time() - start_time
        
        if langgraph_response.status_code == 200:
            langgraph_result = langgraph_response.json()
            langgraph_success = True
            print(f"✅ LangGraph Processing time: {langgraph_time:.2f} seconds")
            print(f"📊 LangGraph Status: {langgraph_result.get('status')}")
        else:
            langgraph_success = False
            print(f"❌ LangGraph failed: HTTP {langgraph_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        langgraph_time = 0
        langgraph_success = False
        print("❌ LangGraph service not available (expected if not running)")
    except Exception as e:
        langgraph_time = time.time() - start_time  
        langgraph_success = False
        print(f"❌ LangGraph failed in {langgraph_time:.2f} seconds: {str(e)}")
    
    # Comparison Summary
    print("\n" + "="*50)
    print("📈 PERFORMANCE SUMMARY")
    print("="*50)
    
    if adk_success and langgraph_success:
        speedup = langgraph_time / adk_time if adk_time > 0 else 0
        print(f"🚀 ADK Time: {adk_time:.2f}s")
        print(f"📊 LangGraph Time: {langgraph_time:.2f}s") 
        print(f"⚡ Speedup: {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}")
    else:
        print(f"🚀 ADK: {'✅ Success' if adk_success else '❌ Failed'}")
        print(f"📊 LangGraph: {'✅ Success' if langgraph_success else '❌ Failed'}")

if __name__ == "__main__":
    asyncio.run(compare_langgraph_vs_adk())

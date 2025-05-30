# test_hybrid_system.py
"""
Test script for the TradeSage Hybrid System
Tests both the hybrid RAG service and the enhanced agents
"""

import asyncio
import json
from datetime import datetime

def test_hybrid_rag_service():
    """Test the hybrid RAG service independently"""
    print("🔧 Testing Hybrid RAG Service")
    print("=" * 50)
    
    try:
        from app.services.hybrid_rag_service import get_hybrid_rag_service
        
        # Initialize service
        service = get_hybrid_rag_service()
        
        # Test with Bitcoin hypothesis
        test_hypothesis = "Bitcoin will reach $100,000 USD by end of Q2 2025"
        
        print(f"Testing hypothesis: {test_hypothesis}")
        
        # Run hybrid research
        result = asyncio.run(service.hybrid_research(test_hypothesis))
        
        print(f"\n📊 Results:")
        print(f"Research method: {result.get('research_data', {}).get('research_method', 'unknown')}")
        
        data_sources = result.get('research_data', {}).get('data_sources', {})
        print(f"Data sources:")
        print(f"  - RAG database: {data_sources.get('rag_database', 0)} insights")
        print(f"  - Real-time market: {data_sources.get('real_time_market', 0)} sources")
        print(f"  - Real-time news: {data_sources.get('real_time_news', 0)} articles")
        
        confidence = result.get('research_data', {}).get('confidence_score', 0)
        print(f"Confidence score: {confidence:.2f}")
        
        print("✅ Hybrid RAG Service test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Hybrid RAG Service test failed: {str(e)}")
        return False

def test_hybrid_agents():
    """Test the hybrid agents individually"""
    print("\n🤖 Testing Hybrid Agents")
    print("=" * 50)
    
    # Test Research Agent
    try:
        print("Testing Hybrid Research Agent...")
        from app.agents.research_agent.agent_hybrid import create as create_hybrid_research_agent
        
        research_agent = create_hybrid_research_agent()
        
        test_input = {
            "hypothesis": "Bitcoin will reach $100,000 USD by end of Q2 2025",
            "processed_hypothesis": "Bitcoin will reach $100,000 USD by end of Q2 2025"
        }
        
        result = research_agent.process(test_input)
        
        if result.get("status") == "success":
            research_data = result.get("research_data", {})
            method = research_data.get("research_method", "unknown")
            print(f"   ✅ Research Agent: Using {method} method")
            
            data_sources = research_data.get("data_sources", {})
            print(f"      - RAG insights: {data_sources.get('rag_database', 0)}")
            print(f"      - Market data: {data_sources.get('real_time_market', 0)}")
            print(f"      - News articles: {data_sources.get('real_time_news', 0)}")
        else:
            print(f"   ❌ Research Agent failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Research Agent test failed: {str(e)}")
        return False
    
    # Test Contradiction Agent
    try:
        print("\nTesting Hybrid Contradiction Agent...")
        from app.agents.contradiction_agent.agent_hybrid import create as create_hybrid_contradiction_agent
        
        contradiction_agent = create_hybrid_contradiction_agent()
        
        test_input = {
            "hypothesis": "Bitcoin will reach $100,000 USD by end of Q2 2025",
            "processed_hypothesis": "Bitcoin will reach $100,000 USD by end of Q2 2025",
            "research_data": {
                "market_data": {"BTC-USD": {"data": {"info": {"currentPrice": 45000}}}},
                "news_data": {"articles": [{"title": "Bitcoin market analysis"}]}
            }
        }
        
        result = contradiction_agent.process(test_input)
        
        if result.get("status") in ["success", "error_fallback"]:
            contradictions = result.get("contradictions", [])
            evidence_sources = result.get("evidence_sources", {})
            
            print(f"   ✅ Contradiction Agent: Found {len(contradictions)} contradictions")
            print(f"      - From RAG: {evidence_sources.get('rag_database', 0)}")
            print(f"      - AI generated: {evidence_sources.get('ai_generated', 0)}")
            
            # Show first contradiction as example
            if contradictions:
                first = contradictions[0]
                print(f"      - Example: \"{first.get('quote', '')[:60]}...\"")
                print(f"        Strength: {first.get('strength', 'Unknown')}")
        else:
            print(f"   ❌ Contradiction Agent failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Contradiction Agent test failed: {str(e)}")
        return False
    
    print("✅ Hybrid Agents test completed successfully")
    return True

def test_full_workflow():
    """Test the complete hybrid workflow"""
    print("\n🔄 Testing Complete Hybrid Workflow")
    print("=" * 50)
    
    try:
        from app.graph_hybrid import create_hybrid_graph
        
        # Create the hybrid graph
        workflow = create_hybrid_graph()
        
        # Test with Bitcoin hypothesis
        initial_state = {
            "input": "Bitcoin will reach $100,000 USD by end of Q2 2025",
            "mode": "analyze",
            "hypothesis": "Bitcoin will reach $100,000 USD by end of Q2 2025",
            "processed_hypothesis": "",
            "research_data": {},
            "contradictions": [],
            "confirmations": [],
            "synthesis": "",
            "alerts": [],
            "final_response": "",
            "error": "",
            "data_sources": {},
            "confidence_score": 0.0,
            "research_method": ""
        }
        
        print(f"Testing hypothesis: {initial_state['hypothesis']}")
        print("Running through complete workflow...")
        
        # Execute the workflow
        result = workflow.invoke(initial_state)
        
        # Check for errors
        if result.get("error"):
            print(f"❌ Workflow error: {result['error']}")
            return False
        
        # Print results summary
        print(f"\n📊 Workflow Results:")
        print(f"Research method: {result.get('research_method', 'unknown')}")
        print(f"Confidence score: {result.get('confidence_score', 0):.2f}")
        
        contradictions = result.get('contradictions', [])
        confirmations = result.get('confirmations', [])
        alerts = result.get('alerts', [])
        
        print(f"Contradictions found: {len(contradictions)}")
        print(f"Confirmations found: {len(confirmations)}")
        print(f"Alerts generated: {len(alerts)}")
        
        data_sources = result.get('data_sources', {})
        if data_sources:
            print(f"Data sources used:")
            for source, count in data_sources.items():
                print(f"  - {source}: {count}")
        
        # Show sample outputs
        if contradictions:
            print(f"\nSample contradiction:")
            first_contradiction = contradictions[0]
            print(f"  \"{first_contradiction.get('quote', '')[:80]}...\"")
        
        if alerts:
            print(f"\nSample alert:")
            first_alert = alerts[0]
            print(f"  {first_alert.get('message', '')[:80]}...")
        
        synthesis = result.get('synthesis', '')
        if synthesis:
            print(f"\nSynthesis preview:")
            print(f"  {synthesis[:150]}...")
        
        print("✅ Complete workflow test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_cloud_sql_connection():
    """Test Cloud SQL vector database connection"""
    print("\n💾 Testing Cloud SQL Vector Database Connection")
    print("=" * 50)
    
    try:
        from app.services.hybrid_rag_service import HybridRAGService
        
        # Create a temporary service to test connection
        service = HybridRAGService()
        
        if service.connection:
            print("✅ Successfully connected to Cloud SQL database")
            
            # Test a simple query
            cursor = service.connection.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM documents;")
                doc_count = cursor.fetchone()[0]
                print(f"   Database contains {doc_count} documents")
                
                cursor.execute("""
                    SELECT DISTINCT instrument, COUNT(*) 
                    FROM documents 
                    GROUP BY instrument 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 5;
                """)
                top_instruments = cursor.fetchall()
                
                print("   Top instruments by document count:")
                for instrument, count in top_instruments:
                    print(f"     - {instrument}: {count} documents")
                
            finally:
                cursor.close()
            
            service.close()
            print("✅ Cloud SQL test completed successfully")
            return True
        else:
            print("❌ Failed to connect to Cloud SQL database")
            return False
            
    except Exception as e:
        print(f"❌ Cloud SQL test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("🧪 TradeSage Hybrid System Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Cloud SQL Connection", test_cloud_sql_connection),
        ("Hybrid RAG Service", test_hybrid_rag_service),
        ("Hybrid Agents", test_hybrid_agents),
        ("Complete Workflow", test_full_workflow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'🟦' * 3} {test_name} {'🟦' * 3}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:25} | {status}")
        if passed_test:
            passed += 1
    
    print("=" * 60)
    print(f"🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Hybrid system is working correctly.")
    elif passed > total / 2:
        print("⚠️  Most tests passed. Some components may need attention.")
    else:
        print("❌ Multiple test failures. System needs debugging.")
    
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    # Run individual tests or complete suite
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "rag":
            test_hybrid_rag_service()
        elif test_name == "agents":
            test_hybrid_agents()
        elif test_name == "workflow":
            test_full_workflow()
        elif test_name == "db":
            test_cloud_sql_connection()
        else:
            print("Available tests: rag, agents, workflow, db")
    else:
        # Run complete test suite
        run_all_tests()

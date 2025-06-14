# app/adk/test_adk.py
import asyncio
import json
from app.adk.orchestrator import orchestrator

async def test_adk_workflow():
    """Test the ADK workflow with sample data."""
    
    test_cases = [
        {
            "name": "Stock Analysis",
            "hypothesis": "Apple will reach $250 by Q3 2025",
            "expected_asset": "AAPL"
        },
        {
            "name": "Crypto Analysis", 
            "hypothesis": "Bitcoin will appreciate to $120,000 by year-end",
            "expected_asset": "BTC-USD"
        },
        {
            "name": "Commodity Analysis",
            "hypothesis": "Oil prices will exceed $95 per barrel by summer 2025",
            "expected_asset": "CL=F"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test_case['name']}")
        print(f"Hypothesis: {test_case['hypothesis']}")
        print(f"{'='*60}")
        
        try:
            result = await orchestrator.process_hypothesis({
                "hypothesis": test_case["hypothesis"],
                "mode": "analyze"
            })
            
            print(f"✅ Status: {result.get('status')}")
            print(f"📊 Processed: {result.get('processed_hypothesis', '')[:100]}...")
            print(f"🎯 Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"⚠️  Contradictions: {len(result.get('contradictions', []))}")
            print(f"✅ Confirmations: {len(result.get('confirmations', []))}")
            print(f"🚨 Alerts: {len(result.get('alerts', []))}")
            
            # Check context extraction
            context = result.get('context', {})
            asset_info = context.get('asset_info', {})
            extracted_symbol = asset_info.get('primary_symbol', 'Unknown')
            
            print(f"🔍 Extracted Symbol: {extracted_symbol}")
            
            if test_case['expected_asset'] in extracted_symbol:
                print("✅ Asset extraction: PASSED")
            else:
                print(f"❌ Asset extraction: FAILED (expected {test_case['expected_asset']}, got {extracted_symbol})")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_adk_workflow())

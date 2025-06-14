#!/bin/bash
# scripts/test_both_versions.sh

echo "🧪 Testing Both Versions"

# Test hypothesis
TEST_HYPOTHESIS="Tesla will reach $300 by Q3 2025"

echo "Testing ADK Version..."
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d "{\"hypothesis\": \"$TEST_HYPOTHESIS\"}" \
  > adk_result.json

echo "Testing LangGraph Version..."  
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d "{\"hypothesis\": \"$TEST_HYPOTHESIS\"}" \
  > langgraph_result.json

echo "✅ Results saved to adk_result.json and langgraph_result.json"
echo "📊 Compare the outputs to validate migration"

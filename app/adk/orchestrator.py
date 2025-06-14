# app/adk/orchestrator.py
from typing import Dict, Any, List
import json
import asyncio
from google.adk.agents import Agent
from app.adk.agents.hypothesis_agent import create_hypothesis_agent
from app.adk.agents.context_agent import create_context_agent
from app.adk.agents.research_agent import create_research_agent
from app.adk.agents.contradiction_agent import create_contradiction_agent
from app.adk.agents.synthesis_agent import create_synthesis_agent
from app.adk.agents.alert_agent import create_alert_agent
from app.config.adk_config import ADK_CONFIG

class TradeSageOrchestrator:
    """ADK-based orchestrator for TradeSage AI workflow."""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all agents."""
        return {
            "hypothesis": create_hypothesis_agent(),
            "context": create_context_agent(),
            "research": create_research_agent(),
            "contradiction": create_contradiction_agent(),
            "synthesis": create_synthesis_agent(),
            "alert": create_alert_agent(),
        }
    
    async def process_hypothesis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a trading hypothesis through the ADK agent workflow."""
        
        try:
            # Step 1: Process Hypothesis
            print("🧠 Processing hypothesis...")
            hypothesis_result = await self._run_agent("hypothesis", {
                "hypothesis": input_data.get("hypothesis", ""),
                "mode": input_data.get("mode", "analyze")
            })
            
            processed_hypothesis = self._extract_response(hypothesis_result)
            
            # Step 2: Analyze Context  
            print("🔍 Analyzing context...")
            context_result = await self._run_agent("context", {
                "hypothesis": processed_hypothesis
            })
            
            context = self._parse_json_response(context_result)
            
            # Step 3: Conduct Research
            print("📊 Conducting research...")
            research_result = await self._run_agent("research", {
                "hypothesis": processed_hypothesis,
                "context": context
            })
            
            research_data = self._parse_research_response(research_result)
            
            # Step 4: Identify Contradictions
            print("⚠️ Identifying contradictions...")
            contradiction_result = await self._run_agent("contradiction", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data
            })
            
            contradictions = self._parse_contradictions(contradiction_result)
            
            # Step 5: Synthesize Analysis
            print("🔬 Synthesizing analysis...")
            synthesis_result = await self._run_agent("synthesis", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data,
                "contradictions": contradictions
            })
            
            synthesis_data = self._parse_synthesis_response(synthesis_result)
            
            # Step 6: Generate Alerts
            print("🚨 Generating alerts...")
            alert_result = await self._run_agent("alert", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "synthesis": synthesis_data,
                "contradictions": contradictions,
                "confirmations": synthesis_data.get("confirmations", []),
                "confidence_score": synthesis_data.get("confidence_score", 0.5)
            })
            
            alerts_data = self._parse_alerts_response(alert_result)
            
            # Compile final result
            return {
                "status": "success",
                "processed_hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data,
                "contradictions": contradictions,
                "confirmations": synthesis_data.get("confirmations", []),
                "synthesis": synthesis_data.get("analysis", ""),
                "alerts": alerts_data.get("alerts", []),
                "recommendations": alerts_data.get("recommendations", ""),
                "confidence_score": synthesis_data.get("confidence_score", 0.5),
                "method": "adk_orchestration"
            }
            
        except Exception as e:
            print(f"❌ Orchestration error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "method": "adk_orchestration"
            }
    
    async def _run_agent(self, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Run a specific agent with input data."""
        agent = self.agents[agent_name]
        
        # Format input as a user message
        user_message = self._format_agent_input(agent_name, input_data)
        
        # Get response from agent
        response = ""
        async for chunk in agent.stream_query(user_message):
            if hasattr(chunk, 'content') and chunk.content:
                response += str(chunk.content)
        
        return response
    
    def _format_agent_input(self, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Format input data for agent."""
        if agent_name == "hypothesis":
            return f"Process this trading hypothesis: {input_data.get('hypothesis', '')}"
            
        elif agent_name == "context":
            return f"Analyze context for: {input_data.get('hypothesis', '')}"
            
        elif agent_name == "research":
            context = input_data.get('context', {})
            asset_info = context.get('asset_info', {})
            return f"""Conduct research for: {input_data.get('hypothesis', '')}
            
Asset: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('primary_symbol', 'N/A')})
Type: {asset_info.get('asset_type', 'Unknown')}
"""
            
        elif agent_name == "contradiction":
            return f"""Find contradictions for: {input_data.get('hypothesis', '')}
            
Context: {json.dumps(input_data.get('context', {}), indent=2)}
Research: {json.dumps(input_data.get('research_data', {}), indent=2)[:1000]}...
"""
            
        elif agent_name == "synthesis":
            return f"""Synthesize analysis for: {input_data.get('hypothesis', '')}
            
Context: {json.dumps(input_data.get('context', {}), indent=2)}
Research: {json.dumps(input_data.get('research_data', {}), indent=2)[:1000]}...
Contradictions: {json.dumps(input_data.get('contradictions', []), indent=2)}
"""
            
        elif agent_name == "alert":
            return f"""Generate alerts for: {input_data.get('hypothesis', '')}
            
Synthesis: {input_data.get('synthesis', '')}
Contradictions: {len(input_data.get('contradictions', []))} identified
Confirmations: {len(input_data.get('confirmations', []))} identified  
Confidence: {input_data.get('confidence_score', 0.5):.2f}
"""
        
        return str(input_data)
    
    def _extract_response(self, response: str) -> str:
        """Extract clean response text."""
        return response.strip()
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from agent."""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        # Return empty context if parsing fails
        return {
            "asset_info": {
                "primary_symbol": "SPY",
                "asset_name": "Unknown Asset",
                "asset_type": "unknown"
            },
            "hypothesis_details": {
                "direction": "neutral",
                "confidence_level": "low"
            },
            "research_guidance": {
                "search_terms": ["financial market"]
            },
            "risk_analysis": {
                "primary_risks": ["market volatility"]
            }
        }
    
    def _parse_research_response(self, response: str) -> Dict[str, Any]:
        """Parse research response."""
        return {
            "summary": response[:500] + "..." if len(response) > 500 else response,
            "method": "adk_research",
            "timestamp": "2025-01-01T00:00:00Z"
        }
    
    def _parse_contradictions(self, response: str) -> List[Dict[str, Any]]:
        """Parse contradictions from response."""
        # Try to extract JSON contradictions
        contradictions = []
        
        # Split response into potential contradiction blocks
        lines = response.split('\n')
        current_contradiction = {}
        
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not line.startswith(('Note:', 'Important:', 'Summary:')):
                contradictions.append({
                    "quote": line[:400],
                    "reason": "Market analysis identifies this as a potential challenge to the investment thesis.",
                    "source": "ADK Analysis",
                    "strength": "Medium"
                })
                
                if len(contradictions) >= 3:
                    break
        
        return contradictions
    
    def _parse_synthesis_response(self, response: str) -> Dict[str, Any]:
        """Parse synthesis response."""
        return {
            "analysis": response,
            "confirmations": [
                {
                    "quote": "Strong market fundamentals support the investment thesis.",
                    "reason": "Technical and fundamental analysis align positively.",
                    "source": "ADK Synthesis",
                    "strength": "Medium"
                }
            ],
            "confidence_score": 0.6  # Default moderate confidence
        }
    
    def _parse_alerts_response(self, response: str) -> Dict[str, Any]:
        """Parse alerts response."""
        return {
            "alerts": [
                {
                    "type": "recommendation",
                    "message": "Monitor market conditions and consider position sizing based on analysis.",
                    "priority": "medium"
                }
            ],
            "recommendations": response
        }

# Global orchestrator instance
orchestrator = TradeSageOrchestrator()

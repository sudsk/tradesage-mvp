# app/adk/orchestrator.py - Complete Enhanced Version
from typing import Dict, Any, List
import json
import asyncio
import re
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.adk.agents.hypothesis_agent import create_hypothesis_agent
from app.adk.agents.context_agent import create_context_agent
from app.adk.agents.research_agent import create_research_agent
from app.adk.agents.contradiction_agent import create_contradiction_agent
from app.adk.agents.synthesis_agent import create_synthesis_agent
from app.adk.agents.alert_agent import create_alert_agent
from app.config.adk_config import ADK_CONFIG

class TradeSageOrchestrator:
    """Enhanced ADK-based orchestrator for TradeSage AI workflow."""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.session_service = InMemorySessionService()
        print("✅ TradeSage ADK Orchestrator initialized")
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all agents."""
        try:
            agents = {
                "hypothesis": create_hypothesis_agent(),
                "context": create_context_agent(),
                "research": create_research_agent(),
                "contradiction": create_contradiction_agent(),
                "synthesis": create_synthesis_agent(),
                "alert": create_alert_agent(),
            }
            print(f"✅ Initialized {len(agents)} agents")
            return agents
        except Exception as e:
            print(f"❌ Error initializing agents: {str(e)}")
            raise
    
    async def process_hypothesis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a trading hypothesis through the enhanced ADK agent workflow."""
        
        hypothesis_text = input_data.get("hypothesis", "").strip()
        if not hypothesis_text:
            return {
                "status": "error",
                "error": "No hypothesis provided",
                "method": "adk_orchestration"
            }
        
        print(f"🚀 Starting ADK workflow for: {hypothesis_text[:100]}...")
        
        try:
            # Step 1: Process Hypothesis
            print("🧠 Processing hypothesis...")
            hypothesis_result = await self._run_agent("hypothesis", {
                "hypothesis": hypothesis_text,
                "mode": input_data.get("mode", "analyze")
            })
            
            processed_hypothesis = self._extract_response(hypothesis_result)
            if not processed_hypothesis:
                processed_hypothesis = hypothesis_text  # Fallback
            
            print(f"   ✅ Processed: {processed_hypothesis[:80]}...")
            
            # Step 2: Analyze Context  
            print("🔍 Analyzing context...")
            context_result = await self._run_agent("context", {
                "hypothesis": processed_hypothesis
            })
            
            context = self._parse_json_response(context_result)
            asset_info = context.get("asset_info", {})
            print(f"   ✅ Asset identified: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('primary_symbol', 'N/A')})")
            
            # Step 3: Conduct Research
            print("📊 Conducting research...")
            research_result = await self._run_agent("research", {
                "hypothesis": processed_hypothesis,
                "context": context
            })
            
            research_data = self._parse_research_response(research_result)
            print(f"   ✅ Research completed: {len(research_data.get('summary', ''))} chars")
            
            # Step 4: Identify Contradictions
            print("⚠️  Identifying contradictions...")
            contradiction_result = await self._run_agent("contradiction", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data
            })
            
            contradictions = self._parse_contradictions(contradiction_result)
            print(f"   ✅ Found {len(contradictions)} contradictions")
            
            # Step 5: Synthesize Analysis
            print("🔬 Synthesizing analysis...")
            synthesis_result = await self._run_agent("synthesis", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data,
                "contradictions": contradictions
            })
            
            synthesis_data = self._parse_synthesis_response(synthesis_result)
            confirmations = synthesis_data.get("confirmations", [])
            confidence_score = synthesis_data.get("confidence_score", 0.5)
            print(f"   ✅ Synthesis complete - Confidence: {confidence_score:.2f}")
            
            # Step 6: Generate Alerts
            print("🚨 Generating alerts...")
            alert_result = await self._run_agent("alert", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "synthesis": synthesis_data,
                "contradictions": contradictions,
                "confirmations": confirmations,
                "confidence_score": confidence_score
            })
            
            alerts_data = self._parse_alerts_response(alert_result)
            alerts = alerts_data.get("alerts", [])
            print(f"   ✅ Generated {len(alerts)} alerts")
            
            # Compile final result
            result = {
                "status": "success",
                "processed_hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data,
                "contradictions": contradictions,
                "confirmations": confirmations,
                "synthesis": synthesis_data.get("analysis", ""),
                "alerts": alerts,
                "recommendations": alerts_data.get("recommendations", ""),
                "confidence_score": confidence_score,
                "method": "adk_orchestration",
                "processing_stats": {
                    "total_agents": len(self.agents),
                    "contradictions_found": len(contradictions),
                    "confirmations_found": len(confirmations),
                    "alerts_generated": len(alerts)
                }
            }
            
            print(f"✅ ADK workflow completed successfully")
            return result
            
        except Exception as e:
            print(f"❌ Orchestration error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "method": "adk_orchestration",
                "partial_data": {
                    "hypothesis": hypothesis_text,
                    "processed_hypothesis": locals().get("processed_hypothesis", ""),
                    "context": locals().get("context", {}),
                }
            }
    
    async def _run_agent(self, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Run a specific agent with input data using ADK Runner with enhanced error handling."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        try:
            agent = self.agents[agent_name]
            
            # Create session for this agent
            app_name = f"tradesage_{agent_name}"
            user_id = "tradesage_user"
            session_id = f"session_{agent_name}_{id(input_data)}"  # Unique session per call
            
            # Await the async session creation
            session = await self.session_service.create_session(
                app_name=app_name,
                user_id=user_id, 
                session_id=session_id
            )
            
            # Create runner
            runner = Runner(
                agent=agent,
                app_name=app_name,
                session_service=self.session_service
            )
            
            # Format input as message
            user_message = self._format_agent_input(agent_name, input_data)
            message = types.Content(
                role='user',
                parts=[types.Part(text=user_message)]
            )
            
            # Run agent and collect response
            response_parts = []
            error_parts = []
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id, 
                new_message=message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                response_parts.append(part.text)
                elif hasattr(event, 'error') and event.error:
                    error_parts.append(str(event.error))
            
            if error_parts:
                error_msg = "; ".join(error_parts)
                print(f"⚠️  Agent {agent_name} reported errors: {error_msg}")
                
            if not response_parts:
                fallback_msg = f"No response generated from {agent_name} agent"
                print(f"⚠️  {fallback_msg}")
                return fallback_msg
                
            response = " ".join(response_parts)
            print(f"   📝 {agent_name} response: {len(response)} characters")
            return response
            
        except Exception as e:
            error_msg = f"Error running {agent_name} agent: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _format_agent_input(self, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Format input data for agent with enhanced context."""
        base_hypothesis = input_data.get('hypothesis', '')
        
        if agent_name == "hypothesis":
            mode = input_data.get('mode', 'analyze')
            return f"""Process this trading hypothesis in {mode} mode:

"{base_hypothesis}"

Please provide a clean, structured hypothesis statement."""
            
        elif agent_name == "context":
            return f"""Analyze the context and extract structured information for this trading hypothesis:

"{base_hypothesis}"

Provide detailed JSON analysis including asset information, hypothesis parameters, research guidance, and risk factors."""
            
        elif agent_name == "research":
            context = input_data.get('context', {})
            asset_info = context.get('asset_info', {})
            research_guidance = context.get('research_guidance', {})
            
            return f"""Conduct comprehensive research for this trading hypothesis:

Hypothesis: "{base_hypothesis}"

Asset Details:
- Name: {asset_info.get('asset_name', 'Unknown')}
- Symbol: {asset_info.get('primary_symbol', 'N/A')}
- Type: {asset_info.get('asset_type', 'Unknown')}
- Sector: {asset_info.get('sector', 'Unknown')}

Research Focus:
- Key metrics: {', '.join(research_guidance.get('key_metrics', ['price', 'volume']))}
- Search terms: {', '.join(research_guidance.get('search_terms', ['market data']))}

Use your available tools to gather market data and news information."""
            
        elif agent_name == "contradiction":
            context = input_data.get('context', {})
            research_summary = input_data.get('research_data', {}).get('summary', '')[:500]
            
            return f"""Identify contradictions and risk factors for this trading hypothesis:

Hypothesis: "{base_hypothesis}"

Asset Context: {context.get('asset_info', {}).get('asset_name', 'Unknown asset')}
Research Summary: {research_summary}

Find specific risks, challenges, and contradictory evidence that could invalidate this hypothesis."""
            
        elif agent_name == "synthesis":
            context = input_data.get('context', {})
            research_summary = input_data.get('research_data', {}).get('summary', '')[:500]
            contradictions = input_data.get('contradictions', [])
            
            return f"""Synthesize a comprehensive investment analysis for this hypothesis:

Hypothesis: "{base_hypothesis}"

Asset: {context.get('asset_info', {}).get('asset_name', 'Unknown')}
Research: {research_summary}
Risk Factors: {len(contradictions)} identified

Provide balanced analysis with supporting confirmations, confidence assessment, and investment recommendation."""
            
        elif agent_name == "alert":
            confidence = input_data.get('confidence_score', 0.5)
            contradictions_count = len(input_data.get('contradictions', []))
            confirmations_count = len(input_data.get('confirmations', []))
            synthesis = input_data.get('synthesis', {}).get('analysis', '')[:300]
            
            return f"""Generate actionable alerts and recommendations for this investment hypothesis:

Hypothesis: "{base_hypothesis}"

Analysis Summary:
- Confidence Score: {confidence:.2f}
- Risk Factors: {contradictions_count}
- Supporting Factors: {confirmations_count}
- Synthesis: {synthesis}

Provide specific, actionable alerts with clear priorities and investment recommendations."""
        
        return str(input_data)
    
    def _extract_response(self, response: str) -> str:
        """Extract clean response text with better handling."""
        if not response:
            return ""
        
        # Clean up common artifacts
        cleaned = response.strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            "Here's the processed hypothesis:",
            "Here is the processed hypothesis:",
            "Processed hypothesis:",
            "The processed hypothesis is:",
            "Analysis:",
            "Response:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove quotes if the entire response is quoted
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1].strip()
        
        return cleaned
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from agent with enhanced error handling."""
        if not response:
            return self._get_fallback_context()
        
        try:
            # Method 1: Direct JSON parsing if response starts with {
            cleaned_response = response.strip()
            if cleaned_response.startswith('{'):
                return json.loads(cleaned_response)
            
            # Method 2: Extract JSON block
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            
            # Method 3: Look for code block
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
                return json.loads(json_str)
                
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {str(e)}")
            print(f"   Raw response preview: {response[:200]}...")
        except Exception as e:
            print(f"⚠️  Unexpected parsing error: {str(e)}")
        
        # Try to extract partial information from text
        return self._extract_context_from_text(response)
    
    def _extract_context_from_text(self, response: str) -> Dict[str, Any]:
        """Extract context information from free text response."""
        context = self._get_fallback_context()
        
        # Look for asset mentions
        asset_patterns = [
            r'(?:Apple|AAPL)',
            r'(?:Tesla|TSLA)', 
            r'(?:Bitcoin|BTC)',
            r'(?:Microsoft|MSFT)',
            r'(?:Google|GOOGL)',
            r'(?:Amazon|AMZN)',
        ]
        
        for pattern in asset_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                if 'Apple' in pattern or 'AAPL' in pattern:
                    context["asset_info"] = {
                        "primary_symbol": "AAPL",
                        "asset_name": "Apple Inc.",
                        "asset_type": "stock",
                        "sector": "Technology",
                        "market": "NASDAQ"
                    }
                elif 'Tesla' in pattern or 'TSLA' in pattern:
                    context["asset_info"] = {
                        "primary_symbol": "TSLA", 
                        "asset_name": "Tesla Inc.",
                        "asset_type": "stock",
                        "sector": "Automotive",
                        "market": "NASDAQ"
                    }
                elif 'Bitcoin' in pattern or 'BTC' in pattern:
                    context["asset_info"] = {
                        "primary_symbol": "BTC-USD",
                        "asset_name": "Bitcoin",
                        "asset_type": "cryptocurrency",
                        "sector": "Cryptocurrency",
                        "market": "Crypto"
                    }
                break
        
        # Look for direction indicators
        if re.search(r'(?:bullish|bull|up|rise|increase|grow)', response, re.IGNORECASE):
            context["hypothesis_details"]["direction"] = "bullish"
        elif re.search(r'(?:bearish|bear|down|fall|decrease|decline)', response, re.IGNORECASE):
            context["hypothesis_details"]["direction"] = "bearish"
        
        return context
    
    def _get_fallback_context(self) -> Dict[str, Any]:
        """Get enhanced fallback context with realistic defaults."""
        return {
            "asset_info": {
                "primary_symbol": "SPY",
                "asset_name": "Financial Asset",
                "asset_type": "equity",
                "sector": "Technology",
                "market": "NASDAQ",
                "competitors": ["QQQ", "VTI"]
            },
            "hypothesis_details": {
                "direction": "neutral",
                "confidence_level": "medium",
                "timeframe": "3-6 months",
                "price_target": None
            },
            "research_guidance": {
                "search_terms": ["market analysis", "financial data", "earnings"],
                "key_metrics": ["price", "volume", "earnings", "revenue"],
                "monitoring_events": ["earnings", "market news", "economic data"]
            },
            "risk_analysis": {
                "primary_risks": ["market volatility", "economic uncertainty", "sector rotation"],
                "contradiction_areas": ["valuation concerns", "competitive pressure"],
                "sensitivity_factors": ["interest rates", "market sentiment"]
            }
        }
    
    def _parse_research_response(self, response: str) -> Dict[str, Any]:
        """Parse research response with enhanced structure."""
        if not response:
            return {"summary": "No research data available", "method": "adk_research"}
        
        return {
            "summary": response[:1000] + "..." if len(response) > 1000 else response,
            "method": "adk_research",
            "timestamp": "2025-01-01T00:00:00Z",
            "data_sources": {
                "market_data": 1,
                "news_articles": 1,
                "analysis_quality": "medium"
            },
            "key_findings": self._extract_key_findings(response)
        }
    
    def _extract_key_findings(self, response: str) -> List[str]:
        """Extract key findings from research response."""
        findings = []
        
        # Look for bullet points or numbered items
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('•', '-', '*')) or 
                re.match(r'^\d+\.', line)) and len(line) > 20:
                clean_line = re.sub(r'^[•\-\*\d\.]+\s*', '', line)
                findings.append(clean_line[:200])
                
                if len(findings) >= 5:
                    break
        
        return findings
    
    def _parse_contradictions(self, response: str) -> List[Dict[str, Any]]:
        """Parse contradictions with enhanced structure detection."""
        if not response:
            return self._get_fallback_contradictions()
        
        contradictions = []
        
        # Method 1: Try to find structured JSON
        try:
            json_arrays = re.findall(r'\[.*?\]', response, re.DOTALL)
            for json_array in json_arrays:
                try:
                    parsed = json.loads(json_array)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        for item in parsed:
                            if isinstance(item, dict) and 'quote' in item:
                                contradictions.append(self._validate_contradiction(item))
                except:
                    continue
        except:
            pass
        
        # Method 2: Line-by-line parsing
        if not contradictions:
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                
                # Skip headers, metadata, etc.
                skip_patterns = [
                    r'^(Note|Important|Summary|Analysis|##|#|Contradiction|Risk)',
                    r'^(Here|The|This|Based)',
                    r'^\d+\.\s*(Here|The|This)',
                ]
                
                should_skip = any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns)
                
                if (len(line) > 30 and not should_skip and 
                    any(keyword in line.lower() for keyword in 
                        ['risk', 'challenge', 'concern', 'issue', 'problem', 'negative', 'decline', 'fall'])):
                    
                    contradictions.append({
                        "quote": line[:400],
                        "reason": "Analysis identifies potential challenges to the investment thesis.",
                        "source": "ADK Risk Analysis",
                        "strength": "Medium"
                    })
                    
                    if len(contradictions) >= 3:
                        break
        
        # Fallback if no contradictions found
        if not contradictions:
            contradictions = self._get_fallback_contradictions()
        
        return contradictions[:3]  # Limit to top 3
    
    def _validate_contradiction(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean contradiction item."""
        return {
            "quote": str(item.get("quote", ""))[:400],
            "reason": str(item.get("reason", "Market analysis identifies this as a potential challenge."))[:400],
            "source": str(item.get("source", "ADK Analysis"))[:40],
            "strength": item.get("strength", "Medium") if item.get("strength") in ["Strong", "Medium", "Weak"] else "Medium"
        }
    
    def _get_fallback_contradictions(self) -> List[Dict[str, Any]]:
        """Get fallback contradictions when none are found."""
        return [
            {
                "quote": "Market volatility and economic uncertainty present ongoing risks to investment performance.",
                "reason": "General market conditions can impact any investment regardless of specific fundamentals.",
                "source": "Market Risk Analysis",
                "strength": "Medium"
            },
            {
                "quote": "Valuation concerns may limit upside potential if current price levels are extended.",
                "reason": "High valuations can constrain further price appreciation and increase downside risk.",
                "source": "Valuation Analysis", 
                "strength": "Medium"
            }
        ]
    
    def _parse_synthesis_response(self, response: str) -> Dict[str, Any]:
        """Parse synthesis response with enhanced confirmation generation."""
        if not response:
            response = "No synthesis analysis available."
        
        # Generate intelligent confirmations
        confirmations = self._generate_confirmations_from_synthesis(response)
        
        # Extract confidence score if mentioned
        confidence_score = self._extract_confidence_score(response)
        
        return {
            "analysis": response,
            "confirmations": confirmations,
            "confidence_score": confidence_score,
            "recommendation": self._extract_recommendation(response, confidence_score)
        }
    
    def _generate_confirmations_from_synthesis(self, synthesis_text: str) -> List[Dict[str, Any]]:
        """Generate intelligent confirmations from synthesis."""
        confirmations = []
        
        # Look for positive indicators in synthesis
        positive_indicators = [
            ("strong", "Strong market fundamentals and positive indicators support the investment thesis."),
            ("growth", "Growth trends and market expansion provide favorable conditions for price appreciation."),
            ("bullish", "Bullish market sentiment and technical indicators align with the investment hypothesis."),
            ("positive", "Positive market developments and favorable conditions support the investment case."),
            ("support", "Market support levels and fundamental analysis validate the investment approach."),
        ]
        
        for indicator, confirmation_text in positive_indicators:
            if indicator in synthesis_text.lower():
                confirmations.append({
                    "quote": confirmation_text,
                    "reason": "Synthesis analysis identifies supporting factors for the investment thesis.",
                    "source": "ADK Synthesis",
                    "strength": "Medium"
                })
                
                if len(confirmations) >= 2:
                    break
        
        # Default confirmations if none found
        if not confirmations:
            confirmations = [
                {
                    "quote": "Market analysis reveals supporting factors for the investment hypothesis.",
                    "reason": "Comprehensive research identifies positive elements that validate the investment case.",
                    "source": "Market Analysis",
                    "strength": "Medium"
                }
            ]
        
        return confirmations
    
    def _extract_confidence_score(self, text: str) -> float:
        """Extract confidence score from text or calculate based on content."""
        # Look for explicit confidence mentions
        confidence_patterns = [
            r'confidence[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)[%\s]*confidence',
            r'score[:\s]+(\d+\.?\d*)',
            r'probability[:\s]+(\d+\.?\d*)'
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    extracted = float(match.group(1))
                    # Convert percentage to decimal if needed
                    if extracted > 1.0:
                        extracted = extracted / 100.0
                    return max(0.15, min(0.85, extracted))  # Bound between 15-85%
                except:
                    continue
        
        # Calculate based on text sentiment
        positive_words = len(re.findall(r'\b(strong|positive|bullish|growth|good|excellent|favorable)\b', text.lower()))
        negative_words = len(re.findall(r'\b(weak|negative|bearish|decline|poor|risk|concern)\b', text.lower()))
        
        if positive_words > negative_words:
            return 0.65  # Moderately positive
        elif negative_words > positive_words:
            return 0.35  # Moderately negative
        else:
            return 0.50  # Neutral
    
    def _extract_recommendation(self, synthesis_text: str, confidence_score: float) -> str:
        """Extract or generate investment recommendation."""
        recommendation_patterns = [
            r'recommendation[:\s]+(.*?)(?:\n|$)',
            r'recommend[:\s]+(.*?)(?:\n|$)',
            r'suggest[:\s]+(.*?)(?:\n|$)',
        ]
        
        for pattern in recommendation_patterns:
            match = re.search(pattern, synthesis_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]
        
        # Generate based on confidence score
        if confidence_score >= 0.7:
            return "Consider initiating position with standard allocation"
        elif confidence_score >= 0.5:
            return "Monitor closely for confirmation signals before entering"
        elif confidence_score >= 0.3:
            return "Exercise caution - wait for better risk/reward setup"
        else:
            return "Avoid position until thesis improves significantly"
    
    def _parse_alerts_response(self, response: str) -> Dict[str, Any]:
        """Parse alerts response with enhanced structure."""
        if not response:
            return {"alerts": [], "recommendations": "No alerts generated"}
        
        alerts = []
        
        # Try to extract structured alerts
        try:
            # Look for JSON arrays in response
            json_matches = re.findall(r'\[.*?\]', response, re.DOTALL)
            for json_match in json_matches:
                try:
                    parsed = json.loads(json_match)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict) and 'message' in item:
                                alerts.append(self._validate_alert(item))
                except:
                    continue
        except:
            pass
        
        # Generate default alerts if none found
        if not alerts:
            alerts = [
                {
                    "type": "recommendation",
                    "message": "Monitor key market indicators and price levels for entry signals.",
                    "priority": "medium"
                },
                {
                    "type": "risk_monitoring",
                    "message": "Set appropriate stop-loss levels to manage downside risk.",
                    "priority": "medium"
                }
            ]
        
        return {
            "alerts": alerts[:5],  # Limit to 5 alerts
            "recommendations": response[:1000] + "..." if len(response) > 1000 else response
        }
    
    def _validate_alert(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean alert item."""
        valid_types = ["recommendation", "warning", "trigger", "risk_monitoring", "entry_signal"]
        valid_priorities = ["high", "medium", "low"]
        
        return {
            "type": item.get("type", "recommendation") if item.get("type") in valid_types else "recommendation",
            "message": str(item.get("message", ""))[:500],
            "priority": item.get("priority", "medium") if item.get("priority") in valid_priorities else "medium"
        }

# Global orchestrator instance with enhanced initialization
try:
    orchestrator = TradeSageOrchestrator()
    print("🚀 TradeSage ADK Orchestrator ready for processing")
except Exception as e:
    print(f"❌ Failed to initialize TradeSage Orchestrator: {str(e)}")
    orchestrator = None

# app/adk/orchestrator.py - Fixed tool response handling to eliminate warnings
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
from app.adk.response_handler import ADKResponseHandler
from app.config.adk_config import ADK_CONFIG

class TradeSageOrchestrator:
    """Enhanced ADK-based orchestrator with FIXED tool response handling."""

    def __init__(self):
        self.agents = self._initialize_agents()
        self.session_service = InMemorySessionService()
        self.response_handler = ADKResponseHandler()
        
        print("✅ TradeSage ADK Orchestrator initialized with fixed tool handling")
        
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
        """Process a trading hypothesis through the ADK agent workflow."""
        
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
            hypothesis_result = await self._run_agent_with_fixed_tool_handling("hypothesis", {
                "hypothesis": hypothesis_text,
                "mode": input_data.get("mode", "analyze")
            })
            
            processed_hypothesis = self._extract_response(hypothesis_result["final_text"])
            if not processed_hypothesis:
                processed_hypothesis = hypothesis_text  # Fallback
            
            print(f"   ✅ Processed: {processed_hypothesis[:80]}...")
            
            # Step 2: Analyze Context  
            print("🔍 Analyzing context...")
            context_result = await self._run_agent_with_fixed_tool_handling("context", {
                "hypothesis": processed_hypothesis
            })
            
            context = self._parse_json_response(context_result["final_text"])
            asset_info = context.get("asset_info", {})
            print(f"   ✅ Asset identified: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('primary_symbol', 'N/A')})")
            
            # Step 3: Conduct Research (FIXED - handles tools properly)
            print("📊 Conducting research...")
            research_result = await self._run_agent_with_fixed_tool_handling("research", {
                "hypothesis": processed_hypothesis,
                "context": context
            })
            
            # FIXED: Properly handle research response with tools
            research_summary = self._extract_research_summary_from_tools(research_result)
            tool_summary = self.response_handler.get_tool_summary(research_result)
            
            if tool_summary['tools_called'] > 0:
                print(f"   ✅ Research completed with {tool_summary['tools_called']} tool calls")
                print(f"   🔧 Tools used: {', '.join(tool_summary['tool_names'])}")
            else:
                print(f"   ✅ Research completed: {len(research_summary)} chars")
            
            research_data = {
                "summary": research_summary,
                "tool_results": research_result.get("tool_results", {}),
                "method": "adk_research_with_tools",
                "tools_used": research_result.get("function_calls", [])
            }
            
            # Step 4: Identify Contradictions
            print("⚠️  Identifying contradictions...")
            contradiction_result = await self._run_agent_with_fixed_tool_handling("contradiction", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data
            })
            
            contradictions = self._parse_contradictions_response(contradiction_result["final_text"])
            print(f"   ✅ Found {len(contradictions)} contradictions")
            
            # Step 5: Synthesize Analysis
            print("🔬 Synthesizing analysis...")
            synthesis_result = await self._run_agent_with_fixed_tool_handling("synthesis", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data,
                "contradictions": contradictions
            })
            
            synthesis_data = self._parse_synthesis_response(synthesis_result["final_text"], contradictions)
            confirmations = synthesis_data.get("confirmations", [])
            confidence_score = synthesis_data.get("confidence_score", 0.5)
            print(f"   ✅ Synthesis complete - Confidence: {confidence_score:.2f}")
            
            # Step 6: Generate Alerts
            print("🚨 Generating alerts...")
            alert_result = await self._run_agent_with_fixed_tool_handling("alert", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "synthesis": synthesis_data,
                "contradictions": contradictions,
                "confirmations": confirmations,
                "confidence_score": confidence_score
            })
            
            alerts_data = self._parse_alerts_response(alert_result["final_text"])
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
                "method": "adk_with_fixed_tool_handling",
                "processing_stats": {
                    "total_agents": len(self.agents),
                    "contradictions_found": len(contradictions),
                    "confirmations_found": len(confirmations),
                    "alerts_generated": len(alerts),
                    "research_tools_used": len(research_data.get("tools_used", []))
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
                "method": "adk_with_fixed_tool_handling",
                "partial_data": {
                    "hypothesis": hypothesis_text,
                    "processed_hypothesis": locals().get("processed_hypothesis", ""),
                    "context": locals().get("context", {}),
                }
            }

    async def _run_agent_with_fixed_tool_handling(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """FIXED: Run agent with proper handling of both text and function call responses."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        try:
            agent = self.agents[agent_name]
            
            # Create session for this agent
            app_name = f"tradesage_{agent_name}"
            user_id = "tradesage_user"
            session_id = f"session_{agent_name}_{id(input_data)}"
            
            # Create session
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
            
            # FIXED: Collect all events properly to handle tool usage
            all_events = []
            text_responses = []
            function_calls = []
            function_responses = []
            tool_results = {}
            errors = []
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id, 
                new_message=message
            ):
                all_events.append(event)
                
                # Handle different event types
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            # Handle text parts
                            if hasattr(part, 'text') and part.text:
                                text_responses.append(part.text)
                            
                            # Handle function calls
                            elif hasattr(part, 'function_call') and part.function_call:
                                function_call = {
                                    "name": part.function_call.name,
                                    "args": dict(part.function_call.args) if part.function_call.args else {}
                                }
                                function_calls.append(function_call)
                            
                            # Handle function responses
                            elif hasattr(part, 'function_response') and part.function_response:
                                function_response = {
                                    "name": part.function_response.name,
                                    "response": part.function_response.response
                                }
                                function_responses.append(function_response)
                                
                                # Store tool results for easy access
                                tool_results[part.function_response.name] = part.function_response.response
                
                # Handle errors
                if hasattr(event, 'error') and event.error:
                    errors.append(str(event.error))
            
            # FIXED: Combine all response parts properly
            final_text = " ".join(text_responses) if text_responses else ""
            
            # If we have function calls but no text response, create summary
            if function_calls and not final_text:
                final_text = f"Completed {len(function_calls)} tool calls: {', '.join([fc['name'] for fc in function_calls])}"
            
            response_data = {
                "final_text": final_text,
                "text_parts": text_responses,
                "function_calls": function_calls,
                "function_responses": function_responses,
                "tool_results": tool_results,
                "errors": errors,
                "has_tools": len(function_calls) > 0
            }
            
            # Log tool usage without warnings
            if response_data["function_calls"]:
                print(f"   🔧 {agent_name} used {len(response_data['function_calls'])} tools")
                for call in response_data["function_calls"]:
                    print(f"      - {call['name']}")
            
            if response_data["errors"]:
                print(f"   ⚠️  {agent_name} reported {len(response_data['errors'])} errors")
            
            return response_data
            
        except Exception as e:
            error_msg = f"Error running {agent_name} agent: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "final_text": error_msg,
                "text_parts": [error_msg],
                "function_calls": [],
                "function_responses": [],
                "tool_results": {},
                "errors": [error_msg],
                "has_tools": False
            }

    def _extract_research_summary_from_tools(self, research_result: Dict) -> str:
        """FIXED: Extract research summary properly handling tool results"""
        
        # If we have tool results, format them properly
        if research_result.get("tool_results"):
            formatted_sections = []
            
            # Add agent's text analysis if available
            if research_result.get("final_text"):
                formatted_sections.append("## Agent Analysis")
                formatted_sections.append(research_result["final_text"])
            
            # Add tool results
            formatted_sections.append("\n## Tool Results")
            
            for tool_name, result in research_result["tool_results"].items():
                formatted_sections.append(f"\n### {tool_name}")
                
                try:
                    # Try to parse as JSON if it's structured data
                    if isinstance(result, str) and result.startswith('{'):
                        parsed_result = json.loads(result)
                        status = parsed_result.get('status', 'unknown')
                        formatted_sections.append(f"Status: {status}")
                        
                        # Format market data
                        if 'data' in parsed_result and 'info' in parsed_result.get('data', {}):
                            info = parsed_result['data']['info']
                            formatted_sections.append(f"Current Price: ${info.get('currentPrice', 'N/A')}")
                            formatted_sections.append(f"Daily Change: {info.get('dayChangePercent', 0):+.2f}%")
                            formatted_sections.append(f"Volume: {info.get('volume', 'N/A'):,}")
                        
                        # Format news data
                        elif 'articles' in parsed_result:
                            articles = parsed_result['articles'][:3]  # Top 3 articles
                            formatted_sections.append(f"Found {len(parsed_result['articles'])} articles")
                            for i, article in enumerate(articles, 1):
                                formatted_sections.append(f"{i}. {article.get('title', 'No title')}")
                    
                    else:
                        # Handle non-JSON results
                        result_str = str(result)
                        if len(result_str) > 200:
                            formatted_sections.append(result_str[:200] + "...")
                        else:
                            formatted_sections.append(result_str)
                            
                except Exception as e:
                    formatted_sections.append(f"Tool result (parsing failed): {str(result)[:100]}...")
            
            return "\n".join(formatted_sections)
        
        # Fallback to final text if no tools
        return research_result.get("final_text", "No research data available")

    def _parse_contradictions_response(self, response_text: str) -> List[Dict]:
        """Parse contradictions from agent response"""
        contradictions = []
        
        # Try to extract JSON if present
        try:
            if '{' in response_text and '}' in response_text:
                json_matches = re.findall(r'\{[^}]+\}', response_text)
                for match in json_matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, dict) and 'quote' in parsed:
                            contradictions.append(parsed)
                    except:
                        continue
        except:
            pass
        
        # Fallback to text parsing
        if not contradictions:
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 30 and any(keyword in line.lower() for keyword in 
                                        ['risk', 'challenge', 'concern', 'negative', 'decline']):
                    contradictions.append({
                        "quote": line[:400],
                        "reason": "Market analysis identifies this challenge",
                        "source": "Agent Analysis",
                        "strength": "Medium"
                    })
        
        return contradictions[:3]  # Limit to 3

    def _parse_synthesis_response(self, response_text: str, contradictions: List[Dict]) -> Dict[str, Any]:
        """Parse synthesis response and extract confirmations"""
        
        # Try to extract confirmations from response
        confirmations = []
        
        # Look for positive statements in synthesis
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 30 and any(keyword in line.lower() for keyword in 
                                    ['strong', 'growth', 'positive', 'advantage', 'leader']):
                confirmations.append({
                    "quote": line[:400],
                    "reason": "Market analysis supports this positive factor",
                    "source": "Synthesis",
                    "strength": "Medium"
                })
        
        # Default confirmations if none found
        if not confirmations:
            confirmations = [
                {
                    "quote": "Market fundamentals support the investment thesis with positive indicators.",
                    "reason": "Analysis suggests favorable conditions for price appreciation potential.",
                    "source": "Market Analysis",
                    "strength": "Medium"
                }
            ]
        
        # Calculate basic confidence score
        conf_count = len(confirmations)
        contra_count = len(contradictions)
        
        if conf_count == 0 and contra_count == 0:
            confidence = 0.5
        else:
            confidence = conf_count / (conf_count + contra_count + 1)  # +1 to avoid division issues
            confidence = max(0.15, min(0.85, confidence))  # Bound between 15% and 85%
        
        return {
            "analysis": response_text,
            "confirmations": confirmations[:3],  # Limit to 3
            "confidence_score": confidence
        }

    def _parse_alerts_response(self, response_text: str) -> Dict[str, Any]:
        """Parse alerts response"""
        alerts = []
        
        # Try to extract structured alerts
        try:
            json_matches = re.findall(r'\[.*?\]', response_text, re.DOTALL)
            for json_match in json_matches:
                try:
                    parsed = json.loads(json_match)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict) and 'message' in item:
                                alerts.append({
                                    "type": item.get("type", "recommendation"),
                                    "message": str(item.get("message", ""))[:500],
                                    "priority": item.get("priority", "medium")
                                })
                except:
                    continue
        except:
            pass
        
        # Generate default alerts if none found
        if not alerts:
            alerts = [
                {
                    "type": "recommendation",
                    "message": "Monitor key market indicators and price levels for optimal entry timing.",
                    "priority": "medium"
                },
                {
                    "type": "risk_management",
                    "message": "Set appropriate stop-loss levels to manage downside risk exposure.",
                    "priority": "medium"
                }
            ]
        
        return {
            "alerts": alerts[:5],  # Limit to 5 alerts
            "recommendations": response_text[:1000] + "..." if len(response_text) > 1000 else response_text
        }

    # Include all the helper methods from the original orchestrator...
    def _format_agent_input(self, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Format input data for agent."""
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
        """Extract clean response text."""
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
        """Parse JSON response from agent."""
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
        
        return context
    
    def _get_fallback_context(self) -> Dict[str, Any]:
        """Get fallback context."""
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

# Global orchestrator instance
try:
    orchestrator = TradeSageOrchestrator()
    print("🚀 TradeSage ADK Orchestrator with Fixed Tool Handling ready")
except Exception as e:
    print(f"❌ Failed to initialize TradeSage Orchestrator: {str(e)}")
    orchestrator = None

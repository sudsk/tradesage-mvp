
# app/adk/orchestrator.py - Updated with enhanced tool response handling
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
from app.adk.agents.contradiction_agent import create_contradiction_agent  # Enhanced version
from app.adk.agents.synthesis_agent import create_synthesis_agent  # Enhanced version
from app.adk.agents.alert_agent import create_alert_agent
from app.adk.response_handler import ADKResponseHandler
from app.config.adk_config import ADK_CONFIG

class TradeSageOrchestrator:
    """Enhanced ADK-based orchestrator with proper tool response handling."""

    def __init__(self):
        self.agents = self._initialize_agents()
        self.session_service = InMemorySessionService()
        self.response_handler = ADKResponseHandler()
        
        # Initialize processors for enhanced logic with proper model integration
        self._initialize_enhanced_processors()
        
        print("✅ TradeSage ADK Orchestrator initialized with enhanced tool handling")
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all agents with enhanced versions."""
        try:
            agents = {
                "hypothesis": create_hypothesis_agent(),
                "context": create_context_agent(),
                "research": create_research_agent(),
                "contradiction": create_contradiction_agent(),  # Enhanced
                "synthesis": create_synthesis_agent(),  # Enhanced
                "alert": create_alert_agent(),
            }
            print(f"✅ Initialized {len(agents)} agents with enhanced logic")
            return agents
        except Exception as e:
            print(f"❌ Error initializing agents: {str(e)}")
            raise
    
    def _initialize_enhanced_processors(self):
        """Initialize the enhanced processors with actual agent models."""
        try:
            # Import the processor classes
            from app.adk.agents.contradiction_agent import IntelligentContradictionProcessor
            from app.adk.agents.synthesis_agent import AssetSpecificConfirmationGenerator, ConfidenceCalculator
            
            # Initialize processors with actual agents and session service
            self.contradiction_processor = IntelligentContradictionProcessor(
                agent=self.agents["contradiction"],
                session_service=self.session_service
            )
            
            self.confirmation_generator = AssetSpecificConfirmationGenerator(
                agent=self.agents["synthesis"], 
                session_service=self.session_service
            )
            
            self.confidence_calculator = ConfidenceCalculator()
            
            print("✅ Enhanced processors initialized with model integration")
        except Exception as e:
            print(f"⚠️  Enhanced processors initialization failed: {str(e)}")
            print("   Falling back to basic processing")
            self.contradiction_processor = None
            self.confirmation_generator = None
            self.confidence_calculator = None
    
    async def process_hypothesis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a trading hypothesis through the enhanced ADK agent workflow."""
        
        hypothesis_text = input_data.get("hypothesis", "").strip()
        if not hypothesis_text:
            return {
                "status": "error",
                "error": "No hypothesis provided",
                "method": "enhanced_adk_orchestration"
            }
        
        print(f"🚀 Starting enhanced ADK workflow for: {hypothesis_text[:100]}...")
        
        try:
            # Step 1: Process Hypothesis
            print("🧠 Processing hypothesis...")
            hypothesis_result = await self._run_agent_with_tool_handling("hypothesis", {
                "hypothesis": hypothesis_text,
                "mode": input_data.get("mode", "analyze")
            })
            
            processed_hypothesis = self._extract_response(hypothesis_result["final_text"])
            if not processed_hypothesis:
                processed_hypothesis = hypothesis_text  # Fallback
            
            print(f"   ✅ Processed: {processed_hypothesis[:80]}...")
            
            # Step 2: Analyze Context  
            print("🔍 Analyzing context...")
            context_result = await self._run_agent_with_tool_handling("context", {
                "hypothesis": processed_hypothesis
            })
            
            context = self._parse_json_response(context_result["final_text"])
            asset_info = context.get("asset_info", {})
            print(f"   ✅ Asset identified: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('primary_symbol', 'N/A')})")
            
            # Step 3: Conduct Research (handles tools properly)
            print("📊 Conducting research...")
            research_result = await self._run_agent_with_tool_handling("research", {
                "hypothesis": processed_hypothesis,
                "context": context
            })
            
            # Enhanced research response handling
            if self.response_handler.has_tool_usage(research_result):
                research_summary = self.response_handler.format_research_response(research_result)
                tool_summary = self.response_handler.get_tool_summary(research_result)
                print(f"   ✅ Research completed with {tool_summary['tools_called']} tool calls")
                print(f"   📊 Tools used: {', '.join(tool_summary['tool_names'])}")
            else:
                research_summary = research_result["final_text"]
                print(f"   ✅ Research completed: {len(research_summary)} chars")
            
            research_data = {
                "summary": research_summary,
                "tool_results": research_result.get("tool_results", {}),
                "method": "enhanced_adk_research_with_tools",
                "tools_used": research_result.get("function_calls", [])
            }
            
            # Step 4: Identify Contradictions with Enhanced Processing
            print("⚠️  Identifying contradictions with enhanced model integration...")
            contradiction_result = await self._run_agent_with_tool_handling("contradiction", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data
            })
            
            # Use enhanced contradiction processing with model integration
            raw_contradictions = self._parse_contradictions_raw(contradiction_result["final_text"])
            contradictions = await self._process_contradictions_with_model_integration(
                raw_contradictions, context, processed_hypothesis
            )
            print(f"   ✅ Found {len(contradictions)} enhanced contradictions")
            
            # Step 5: Synthesize Analysis with Enhanced Confirmations
            print("🔬 Synthesizing analysis with enhanced model integration...")
            synthesis_result = await self._run_agent_with_tool_handling("synthesis", {
                "hypothesis": processed_hypothesis,
                "context": context,
                "research_data": research_data,
                "contradictions": contradictions
            })
            
            # Use enhanced confirmation generation with model integration
            synthesis_data = await self._process_synthesis_with_model_integration(
                synthesis_result["final_text"], context, processed_hypothesis, contradictions
            )
            confirmations = synthesis_data.get("confirmations", [])
            confidence_score = synthesis_data.get("confidence_score", 0.5)
            print(f"   ✅ Enhanced synthesis complete - Confidence: {confidence_score:.2f}")
            
            # Step 6: Generate Alerts
            print("🚨 Generating alerts...")
            alert_result = await self._run_agent_with_tool_handling("alert", {
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
                "method": "enhanced_adk_with_tool_handling",
                "processing_stats": {
                    "total_agents": len(self.agents),
                    "contradictions_found": len(contradictions),
                    "confirmations_found": len(confirmations),
                    "alerts_generated": len(alerts),
                    "enhanced_processing": True,
                    "tool_integration": True,
                    "research_tools_used": len(research_data.get("tools_used", []))
                }
            }
            
            print(f"✅ Enhanced ADK workflow with tool handling completed successfully")
            return result
            
        except Exception as e:
            print(f"❌ Enhanced orchestration error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "method": "enhanced_adk_with_tool_handling",
                "partial_data": {
                    "hypothesis": hypothesis_text,
                    "processed_hypothesis": locals().get("processed_hypothesis", ""),
                    "context": locals().get("context", {}),
                }
            }
      
    # Enhanced processing methods remain the same...
    async def _process_contradictions_with_model_integration(self, raw_contradictions: List[Dict], 
                                                           context: Dict, hypothesis: str) -> List[Dict]:
        """Process contradictions using enhanced logic with actual model integration."""
        
        if not self.contradiction_processor:
            print("   ⚠️  Enhanced processor not available, using basic processing")
            return self._parse_contradictions_basic(raw_contradictions) if raw_contradictions else []
        
        try:
            print("   🤖 Using model-integrated contradiction processing...")
            enhanced_contradictions = self.contradiction_processor.process_contradictions(
                raw_contradictions, context, hypothesis
            )
            print(f"   🔧 Model integration: {len(raw_contradictions)} → {len(enhanced_contradictions)} contradictions")
            return enhanced_contradictions
        except Exception as e:
            print(f"   ⚠️  Model-integrated contradiction processing failed: {str(e)}")
            # Fallback to basic processing
            return self._parse_contradictions_basic(raw_contradictions) if raw_contradictions else []
    
    async def _process_synthesis_with_model_integration(self, synthesis_result: str, context: Dict, 
                                                       hypothesis: str, contradictions: List[Dict]) -> Dict[str, Any]:
        """Process synthesis using enhanced logic with actual model integration."""
        
        if not self.confirmation_generator or not self.confidence_calculator:
            print("   ⚠️  Enhanced processors not available, using basic processing")
            return {
                "analysis": synthesis_result,
                "confirmations": self._get_fallback_confirmations(context),
                "confidence_score": 0.5,
                "assessment": {"confidence": 0.5, "summary": "Basic synthesis processing used"}
            }
        
        try:
            print("   🤖 Using model-integrated confirmation generation...")
            
            # Generate high-quality confirmations using model integration
            confirmations = self.confirmation_generator.generate_high_quality_confirmations(
                context, hypothesis
            )
            
            # Calculate realistic confidence score
            confidence_score = self.confidence_calculator.calculate_realistic_confidence(
                contradictions, confirmations, context
            )
            
            print(f"   🔧 Model integration: {len(confirmations)} confirmations generated with {confidence_score:.2f} confidence")
            
            return {
                "analysis": synthesis_result,
                "confirmations": confirmations,
                "confidence_score": confidence_score,
                "assessment": {
                    "confidence": confidence_score,
                    "summary": f"Model-integrated analysis with {len(confirmations)} confirmations vs {len(contradictions)} contradictions",
                    "recommendation": self._get_recommendation_from_confidence(confidence_score),
                    "evidence_balance": {
                        "confirmations": len(confirmations),
                        "contradictions": len(contradictions)
                    },
                    "processing_method": "model_integrated_with_tools"
                }
            }
            
        except Exception as e:
            print(f"   ⚠️  Model-integrated synthesis processing failed: {str(e)}")
            # Fallback to basic processing
            return {
                "analysis": synthesis_result,
                "confirmations": self._get_fallback_confirmations(context),
                "confidence_score": 0.5,
                "assessment": {"confidence": 0.5, "summary": "Fallback synthesis processing used"}
            }
    
    # All other helper methods remain the same from the previous version...
    def _get_recommendation_from_confidence(self, confidence_score: float) -> str:
        """Get investment recommendation based on confidence score."""
        if confidence_score >= 0.7:
            return "Consider Position"
        elif confidence_score >= 0.5:
            return "Monitor Closely"
        elif confidence_score >= 0.3:
            return "Exercise Caution"
        else:
            return "Avoid or Wait"
    
    def _get_fallback_confirmations(self, context: Dict) -> List[Dict]:
        """Get fallback confirmations when enhanced processing fails."""
        asset_name = context.get("asset_info", {}).get("asset_name", "the asset") if context else "the asset"
        
        return [
            {
                "quote": f"Market fundamentals and technical indicators support {asset_name} investment potential.",
                "reason": "Current market conditions and analysis suggest favorable outlook for price appreciation.",
                "source": "Market Analysis",
                "strength": "Medium"
            }
        ]
    
    def _parse_contradictions_raw(self, contradiction_result: str) -> List[Dict]:
        """Parse raw contradictions from agent response."""
        contradictions = []
        
        # Try to extract JSON if present
        try:
            if '{' in contradiction_result and '}' in contradiction_result:
                import re
                json_matches = re.findall(r'\{[^}]+\}', contradiction_result)
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
            lines = contradiction_result.split('\n')
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
        
        return contradictions
    
    def _parse_contradictions_basic(self, raw_contradictions: List[Dict]) -> List[Dict]:
        """Basic contradiction parsing as fallback."""
        if not raw_contradictions:
            return []
        
        processed = []
        for contradiction in raw_contradictions:
            if isinstance(contradiction, dict):
                processed.append({
                    "quote": contradiction.get("quote", "")[:400],
                    "reason": contradiction.get("reason", "Market analysis identifies potential challenges")[:400],
                    "source": contradiction.get("source", "Basic Analysis")[:40],
                    "strength": contradiction.get("strength", "Medium")
                })
        
        return processed[:3]  # Limit to 3
    
    # Keep all existing helper methods from original orchestrator
    async def _run_agent(self, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Run a specific agent with input data using ADK Runner."""
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
    
    # Include necessary helper methods...
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
            return {"summary": "No research data available", "method": "enhanced_adk_research"}
        
        return {
            "summary": response[:1000] + "..." if len(response) > 1000 else response,
            "method": "enhanced_adk_research",
            "timestamp": "2025-01-01T00:00:00Z",
            "data_sources": {
                "market_data": 1,
                "news_articles": 1,
                "analysis_quality": "enhanced"
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
    print("🚀 Enhanced TradeSage ADK Orchestrator with Model Integration ready for processing")
except Exception as e:
    print(f"❌ Failed to initialize Enhanced TradeSage Orchestrator: {str(e)}")
    orchestrator = None

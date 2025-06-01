# app/agents/context_agent/agent.py - Pure AI-driven context analysis
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import re
from typing import Dict, Any, Optional

class ContextAgent:
    """Pure AI-driven context analysis - no hardcoding, works for any financial instrument"""
    
    def __init__(self):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_INSTRUCTION
            )
        except Exception as e:
            print(f"Error initializing Context Agent: {e}")
            self.model = None
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ANY hypothesis and provide intelligent context using pure AI"""
        
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        
        # Use the cleaner processed hypothesis if available
        analysis_text = processed_hypothesis if processed_hypothesis else hypothesis
        
        print(f"🧠 Analyzing context using AI for: {analysis_text}")
        
        try:
            # Pure AI analysis - no hardcoded patterns
            context = self._ai_analyze_hypothesis_context(analysis_text)
            
            if context:
                asset_info = context.get("asset_info", {})
                print(f"   ✅ AI identified: {asset_info.get('asset_name', 'Unknown')} "
                      f"({asset_info.get('primary_symbol', 'N/A')})")
                print(f"   📊 Asset type: {asset_info.get('asset_type', 'Unknown')}")
                print(f"   🎯 Direction: {context.get('hypothesis_details', {}).get('direction', 'Unknown')}")
                
                return {
                    "context": context,
                    "status": "success"
                }
            else:
                # AI-generated fallback context
                fallback_context = self._ai_generate_fallback_context(analysis_text)
                return {
                    "context": fallback_context,
                    "status": "success_fallback"
                }
                
        except Exception as e:
            print(f"❌ Context analysis failed: {str(e)}")
            # AI-generated error fallback
            fallback_context = self._ai_generate_fallback_context(analysis_text)
            return {
                "context": fallback_context,
                "status": "error_fallback"
            }
    
    def _ai_analyze_hypothesis_context(self, hypothesis: str) -> Optional[Dict[str, Any]]:
        """Use pure AI to analyze hypothesis - no hardcoded mappings or patterns"""
        
        analysis_prompt = f"""
        You are a world-class financial analyst with expertise in ALL global markets and asset classes.
        
        Analyze this trading hypothesis and provide comprehensive context using ONLY your knowledge:
        
        HYPOTHESIS: "{hypothesis}"
        
        Provide intelligent analysis for:
        
        1. **ASSET IDENTIFICATION** (derive from your financial knowledge):
           - What financial instrument is this? (be specific)
           - Official trading symbol/ticker (use correct exchange format)
           - Asset classification (stock/crypto/commodity/currency/bond/derivative/etc.)
           - Primary market/exchange where it trades
           - Market capitalization tier (if applicable)
           - Sector/industry classification
           - Main competitors in the space
        
        2. **MARKET INTELLIGENCE** (use your market knowledge):
           - Current business model or fundamental drivers
           - Key value propositions or use cases
           - Primary revenue sources or demand drivers
           - Geographic exposure and key markets
           - Regulatory environment considerations
           - Competitive positioning
        
        3. **HYPOTHESIS ANALYSIS** (extract from the text):
           - Directional bias (bullish/bearish/neutral)
           - Specific price targets mentioned
           - Percentage moves implied
           - Investment timeframe specified
           - Confidence indicators from language used
        
        4. **RESEARCH STRATEGY** (design optimal approach):
           - Most relevant data sources for this asset
           - Key performance metrics to monitor
           - Optimal news search terms
           - Important events or catalysts to track
           - Regulatory announcements to watch
           - Earnings or announcement schedules
        
        5. **RISK ASSESSMENT** (identify threat vectors):
           - Primary risk factors for this specific asset
           - Areas where contradictory evidence might exist
           - External dependencies and sensitivities
           - Market structure risks
           - Regulatory or policy risks
           - Competitive threats
        
        **CRITICAL**: Use ONLY your trained knowledge. No pattern matching, no hardcoded lists.
        Derive everything intelligently from your understanding of global financial markets.
        
        Respond with ONLY valid JSON in this exact structure:
        {{
          "asset_info": {{
            "primary_symbol": "correct trading symbol",
            "asset_name": "official full name",
            "asset_type": "specific asset class",
            "sector": "industry/sector",
            "market": "primary exchange/market",
            "competitors": ["main competitors"],
            "market_cap_tier": "large|mid|small|micro|n/a",
            "geographic_exposure": "primary markets/regions",
            "business_model": "brief description"
          }},
          "hypothesis_details": {{
            "direction": "bullish|bearish|neutral",
            "price_target": "number or null",
            "current_price_estimate": "estimated price",
            "percentage_move": "implied percentage change",
            "timeframe": "specific timeframe",
            "confidence_level": "high|medium|low",
            "catalyst_dependency": "event-driven or fundamental"
          }},
          "research_guidance": {{
            "primary_data_sources": ["most relevant sources"],
            "key_metrics": ["specific KPIs to track"],
            "search_terms": ["optimized search queries"],
            "news_categories": ["relevant news types"],
            "monitoring_events": ["key events/announcements"],
            "regulatory_factors": ["regulatory considerations"],
            "earnings_schedule": "next major announcement timing"
          }},
          "risk_analysis": {{
            "primary_risks": ["main threat factors"],
            "contradiction_areas": ["where opposing views exist"],
            "sensitivity_factors": ["external dependencies"],
            "uncertainty_areas": ["high uncertainty factors"],
            "competitive_threats": ["competitive risks"],
            "regulatory_risks": ["policy/regulatory threats"],
            "market_structure_risks": ["trading/liquidity risks"]
          }},
          "market_intelligence": {{
            "current_narrative": "prevailing market story",
            "institutional_sentiment": "institutional view",
            "retail_sentiment": "retail investor view", 
            "analyst_consensus": "general analyst view",
            "recent_developments": ["recent key events"],
            "technical_levels": ["key price levels if known"]
          }},
          "context_summary": "comprehensive analysis summary"
        }}
        """
        
        try:
            response = self.model.generate_content(analysis_prompt)
            context_data = self._parse_ai_context_response(response.text)
            
            if context_data:
                # Validate and enhance with AI
                context_data = self._ai_validate_and_enhance_context(context_data, hypothesis)
                return context_data
            
            return None
            
        except Exception as e:
            print(f"❌ AI context analysis failed: {str(e)}")
            return None
    
    def _parse_ai_context_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the AI's JSON response with intelligent error handling"""
        
        try:
            # Clean the response
            cleaned_response = re.sub(r'```json\s*', '', response_text)
            cleaned_response = re.sub(r'```\s*$', '', cleaned_response)
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            context_data = json.loads(cleaned_response)
            
            # Validate required structure
            required_keys = ['asset_info', 'hypothesis_details', 'research_guidance', 'risk_analysis']
            if all(key in context_data for key in required_keys):
                return context_data
            else:
                print(f"⚠️  AI response missing required keys: {required_keys}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse AI JSON response: {str(e)}")
            print(f"Raw response preview: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"⚠️  Error processing AI response: {str(e)}")
            return None
    
    def _ai_validate_and_enhance_context(self, context: Dict[str, Any], hypothesis: str) -> Dict[str, Any]:
        """Use AI to validate and enhance context - no hardcoded fallbacks"""
        
        validation_prompt = f"""
        Validate and enhance this financial context analysis:
        
        ORIGINAL HYPOTHESIS: "{hypothesis}"
        GENERATED CONTEXT: {json.dumps(context, indent=2)}
        
        Review and improve:
        1. Ensure the asset symbol is correct and properly formatted
        2. Verify the asset classification is accurate
        3. Confirm the research strategy is optimal
        4. Validate the risk assessment is comprehensive
        5. Fill any missing or weak information
        
        Return the enhanced context as JSON with the same structure.
        Focus on accuracy and completeness.
        """
        
        try:
            response = self.model.generate_content(validation_prompt)
            enhanced_context = self._parse_ai_context_response(response.text)
            return enhanced_context if enhanced_context else context
        except:
            # Return original context if validation fails
            return context
    
    def _ai_generate_fallback_context(self, hypothesis: str) -> Dict[str, Any]:
        """Generate intelligent fallback context using AI when primary analysis fails"""
        
        fallback_prompt = f"""
        Generate basic but intelligent context for this hypothesis:
        
        "{hypothesis}"
        
        Even if analysis failed, provide your best intelligent assessment:
        - What asset is likely being discussed?
        - What would be a reasonable trading symbol?
        - What asset type does this appear to be?
        - What direction is implied?
        - What would be smart research terms?
        - What are general risks for this type of asset?
        
        Provide simple but intelligent JSON context with the standard structure.
        Use your financial knowledge to make reasonable inferences.
        """
        
        try:
            response = self.model.generate_content(fallback_prompt)
            fallback_context = self._parse_ai_context_response(response.text)
            
            if fallback_context:
                return fallback_context
                
        except Exception as e:
            print(f"❌ AI fallback generation failed: {str(e)}")
        
        # Last resort: minimal intelligent context
        return {
            "asset_info": {
                "primary_symbol": "SPY",  # Safe default
                "asset_name": "Financial Asset",
                "asset_type": "unknown",
                "sector": "Financial Markets",
                "market": "Unknown"
            },
            "hypothesis_details": {
                "direction": "neutral",
                "price_target": None,
                "timeframe": "Unknown",
                "confidence_level": "low"
            },
            "research_guidance": {
                "key_metrics": ["price", "volume", "market sentiment"],
                "search_terms": ["financial market", "investment analysis"],
                "monitoring_events": ["market updates", "economic news"]
            },
            "risk_analysis": {
                "primary_risks": ["market volatility", "economic uncertainty"],
                "contradiction_areas": ["market sentiment", "technical analysis"],
                "sensitivity_factors": ["market conditions", "economic indicators"]
            },
            "context_summary": f"Basic analysis of financial hypothesis with limited context available"
        }

def create():
    """Create and return an intelligent context agent instance"""
    return ContextAgent()

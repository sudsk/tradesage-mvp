# app/agents/context_agent/agent.py
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import re
from typing import Dict, Any, Optional

class ContextAgent:
    """Intelligent context analysis agent that eliminates hardcoding across the system"""
    
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
        """Analyze hypothesis and provide intelligent context for all other agents"""
        
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        
        # Use the cleaner processed hypothesis if available, fallback to original
        analysis_text = processed_hypothesis if processed_hypothesis else hypothesis
        
        print(f"🧠 Analyzing context for: {analysis_text}")
        
        try:
            # Generate comprehensive context analysis
            context = self._analyze_hypothesis_context(analysis_text)
            
            if context:
                print(f"   ✅ Identified: {context.get('asset_info', {}).get('asset_name', 'Unknown')} "
                      f"({context.get('asset_info', {}).get('primary_symbol', 'N/A')})")
                print(f"   📊 Asset type: {context.get('asset_info', {}).get('asset_type', 'Unknown')}")
                print(f"   🎯 Direction: {context.get('hypothesis_details', {}).get('direction', 'Unknown')}")
                
                return {
                    "context": context,
                    "status": "success"
                }
            else:
                # Provide fallback context if AI analysis fails
                fallback_context = self._generate_fallback_context(analysis_text)
                return {
                    "context": fallback_context,
                    "status": "success_fallback"
                }
                
        except Exception as e:
            print(f"❌ Context analysis failed: {str(e)}")
            fallback_context = self._generate_fallback_context(analysis_text)
            return {
                "context": fallback_context,
                "status": "error_fallback"
            }
    
    def _analyze_hypothesis_context(self, hypothesis: str) -> Optional[Dict[str, Any]]:
        """Use AI to analyze hypothesis and extract structured context"""
        
        analysis_prompt = f"""
        Analyze this trading hypothesis and provide comprehensive context:
        
        HYPOTHESIS: "{hypothesis}"
        
        Provide a complete analysis following the structured JSON format specified in your instructions.
        Focus on being specific and actionable rather than generic.
        
        Ensure you identify:
        1. The exact financial instrument and its symbol
        2. The market sector and competitive landscape
        3. Specific price targets and timeframes mentioned
        4. Key risk factors and areas where contradictions might be found
        5. Relevant search terms and data sources for research
        
        Respond with valid JSON only.
        """
        
        try:
            response = self.model.generate_content(analysis_prompt)
            context_data = self._parse_ai_context_response(response.text)
            
            # Validate and enhance the context
            if context_data:
                context_data = self._validate_and_enhance_context(context_data, hypothesis)
                return context_data
            
            return None
            
        except Exception as e:
            print(f"❌ AI context analysis failed: {str(e)}")
            return None
    
    def _parse_ai_context_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the AI's JSON response and validate structure"""
        
        try:
            # Clean the response - remove any markdown code blocks
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
                print(f"⚠️  Missing required keys in AI response: {required_keys}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse AI JSON response: {str(e)}")
            print(f"Raw response: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"⚠️  Error processing AI response: {str(e)}")
            return None
    
    def _validate_and_enhance_context(self, context: Dict[str, Any], hypothesis: str) -> Dict[str, Any]:
        """Validate and enhance the context data with fallbacks"""
        
        # Ensure asset_info has required fields
        asset_info = context.get('asset_info', {})
        if not asset_info.get('primary_symbol'):
            asset_info['primary_symbol'] = self._extract_symbol_fallback(hypothesis)
        if not asset_info.get('asset_name'):
            asset_info['asset_name'] = asset_info.get('primary_symbol', 'Financial Asset')
        if not asset_info.get('asset_type'):
            asset_info['asset_type'] = self._determine_asset_type_fallback(hypothesis)
        
        # Ensure hypothesis_details has direction
        hypothesis_details = context.get('hypothesis_details', {})
        if not hypothesis_details.get('direction'):
            hypothesis_details['direction'] = self._determine_direction_fallback(hypothesis)
        
        # Ensure arrays are not empty
        research_guidance = context.get('research_guidance', {})
        if not research_guidance.get('search_terms'):
            research_guidance['search_terms'] = [asset_info.get('asset_name', ''), 'market analysis', 'price movement']
        
        risk_analysis = context.get('risk_analysis', {})
        if not risk_analysis.get('primary_risks'):
            risk_analysis['primary_risks'] = ['market volatility', 'economic uncertainty', 'regulatory changes']
        
        # Add context summary if missing
        if not context.get('context_summary'):
            context['context_summary'] = f"Analysis of {asset_info.get('asset_name', 'financial instrument')} hypothesis with {hypothesis_details.get('direction', 'directional')} outlook"
        
        return context
    
    def _extract_symbol_fallback(self, hypothesis: str) -> str:
        """Fallback method to extract symbol using simple patterns"""
        
        # Look for common patterns
        patterns = [
            r'\(([A-Z]{2,5})\)',  # (AAPL)
            r'\$([A-Z]{2,5})',    # $AAPL
            r'\b([A-Z]{2,5})\b'   # AAPL
        ]
        
        for pattern in patterns:
            match = re.search(pattern, hypothesis)
            if match and match.group(1) not in ['USD', 'THE', 'AND', 'FOR']:
                return match.group(1)
        
        # Check for common names
        name_to_symbol = {
            'apple': 'AAPL',
            'microsoft': 'MSFT', 
            'bitcoin': 'BTC-USD',
            'oil': 'CL=F',
            'gold': 'GLD'
        }
        
        hypothesis_lower = hypothesis.lower()
        for name, symbol in name_to_symbol.items():
            if name in hypothesis_lower:
                return symbol
        
        return 'SPY'  # Default fallback
    
    def _determine_asset_type_fallback(self, hypothesis: str) -> str:
        """Fallback method to determine asset type"""
        
        hypothesis_lower = hypothesis.lower()
        
        if any(term in hypothesis_lower for term in ['bitcoin', 'ethereum', 'crypto', 'btc', 'eth']):
            return 'crypto'
        elif any(term in hypothesis_lower for term in ['oil', 'crude', 'gold', 'silver']):
            return 'commodity'
        elif any(term in hypothesis_lower for term in ['s&p', 'nasdaq', 'dow', 'index']):
            return 'index'
        else:
            return 'stock'
    
    def _determine_direction_fallback(self, hypothesis: str) -> str:
        """Fallback method to determine direction"""
        
        hypothesis_lower = hypothesis.lower()
        
        bullish_terms = ['reach', 'rise', 'increase', 'up', 'bull', 'gain']
        bearish_terms = ['fall', 'decline', 'drop', 'down', 'bear', 'crash']
        
        if any(term in hypothesis_lower for term in bullish_terms):
            return 'bullish'
        elif any(term in hypothesis_lower for term in bearish_terms):
            return 'bearish'
        else:
            return 'neutral'
    
    def _generate_fallback_context(self, hypothesis: str) -> Dict[str, Any]:
        """Generate basic context if AI analysis completely fails"""
        
        symbol = self._extract_symbol_fallback(hypothesis)
        asset_type = self._determine_asset_type_fallback(hypothesis)
        direction = self._determine_direction_fallback(hypothesis)
        
        return {
            "asset_info": {
                "primary_symbol": symbol,
                "asset_name": symbol,
                "asset_type": asset_type,
                "sector": "Unknown",
                "market": "Unknown"
            },
            "hypothesis_details": {
                "direction": direction,
                "price_target": None,
                "current_price_estimate": None,
                "timeframe": "Unknown",
                "confidence_level": "medium"
            },
            "research_guidance": {
                "key_metrics": ["price", "volume", "market sentiment"],
                "data_sources": ["market data", "news", "analyst reports"],
                "search_terms": [symbol, "market analysis", "price movement"],
                "monitoring_events": ["earnings", "market updates", "regulatory news"]
            },
            "risk_analysis": {
                "primary_risks": ["market volatility", "economic uncertainty"],
                "contradiction_areas": ["market sentiment", "technical analysis"],
                "sensitivity_factors": ["market conditions", "economic indicators"]
            },
            "context_summary": f"Basic analysis of {symbol} with {direction} outlook"
        }

def create():
    """Create and return a context agent instance"""
    return ContextAgent()

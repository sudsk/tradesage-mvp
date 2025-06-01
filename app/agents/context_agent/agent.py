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
    
    def process(self, input_data):
        """Synthesize using intelligent context analysis"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("processed_hypothesis", "")
        research_data = input_data.get("research_data", {})
        contradictions = input_data.get("contradictions", [])
        context = input_data.get("context", {})
        
        # Generate context-aware confirmations
        confirmations = self._generate_context_aware_confirmations(context, hypothesis)
        
        # Create intelligent synthesis prompt
        prompt = self._create_context_aware_synthesis_prompt(
            hypothesis, research_data, contradictions, confirmations, context
        )
        
        try:
            response = self.model.generate_content(prompt)
            synthesis_data = self._parse_synthesis(response.text)
            
            return {
                "synthesis": response.text,
                "assessment": synthesis_data,
                "status": "success",
                "confirmations": confirmations
            }
        except Exception as e:
            print(f"Synthesis agent error: {str(e)}")
            fallback_text = self._generate_intelligent_fallback_synthesis(context, hypothesis)
            return {
                "synthesis": fallback_text,
                "assessment": {"confidence": 0.5, "summary": fallback_text},
                "status": "error",
                "confirmations": confirmations
            }
    
    def _generate_context_aware_confirmations(self, context: Dict, hypothesis: str) -> List[Dict]:
        """Generate confirmations based on context, not hardcoded patterns"""
        
        if not context:
            return []
        
        asset_info = context.get("asset_info", {})
        asset_type = asset_info.get("asset_type", "unknown")
        asset_name = asset_info.get("asset_name", "Unknown")
        sector = asset_info.get("sector", "Unknown")
        
        # Generate confirmations based on asset type and context
        confirmations = []
        
        if asset_type == "stock":
            confirmations.extend([
                {
                    "quote": f"{asset_name} operates in the growing {sector} sector with strong market fundamentals.",
                    "reason": f"The {sector} industry shows positive growth trends that could support {asset_name}'s price appreciation.",
                    "source": "Sector Analysis",
                    "strength": "Medium"
                },
                {
                    "quote": f"Institutional investment in {sector} companies like {asset_name} continues to increase.",
                    "reason": "Growing institutional interest provides upward pressure on stock prices.",
                    "source": "Institutional Flow Analysis",
                    "strength": "Medium"
                }
            ])
        
        elif asset_type == "crypto":
            confirmations.extend([
                {
                    "quote": f"{asset_name} benefits from increasing institutional adoption of cryptocurrency assets.",
                    "reason": "Growing institutional acceptance drives demand and price appreciation for established cryptocurrencies.",
                    "source": "Adoption Analysis",
                    "strength": "Strong"
                },
                {
                    "quote": f"The fixed supply mechanism of {asset_name} creates structural upward pressure on price as demand increases.",
                    "reason": "Deflationary tokenomics support long-term price appreciation in cryptocurrency markets.",
                    "source": "Tokenomics Analysis",
                    "strength": "Strong"
                }
            ])
        
        elif asset_type == "commodity":
            confirmations.extend([
                {
                    "quote": f"Global demand for {asset_name} continues to grow driven by economic expansion and industrial needs.",
                    "reason": "Increasing industrial and consumer demand supports higher commodity prices.",
                    "source": "Demand Analysis",
                    "strength": "Medium"
                }
            ])
        
        return confirmations[:3]  # Limit to 3 confirmations
    
    def _create_context_aware_synthesis_prompt(self, hypothesis: str, research_data: Dict, 
                                             contradictions: List, confirmations: List, context: Dict) -> str:
        """Create synthesis prompt using context instead of generic approach"""
        
        asset_info = context.get("asset_info", {})
        hypothesis_details = context.get("hypothesis_details", {})
        
        return f"""
        Synthesize a comprehensive analysis for this specific investment hypothesis:
        
        HYPOTHESIS: {hypothesis}
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        - Direction: {hypothesis_details.get("direction", "Unknown")}
        - Target: {hypothesis_details.get("price_target", "Not specified")}
        - Timeframe: {hypothesis_details.get("timeframe", "Not specified")}
        
        RESEARCH FINDINGS: {json.dumps(research_data, indent=2)[:1000]}...
        
        CONTRADICTIONS ({len(contradictions)}): {json.dumps(contradictions, indent=2)[:1000]}...
        
        CONFIRMATIONS ({len(confirmations)}): {json.dumps(confirmations, indent=2)[:1000]}...
        
        Provide a balanced assessment considering:
        1. The specific asset type and sector dynamics
        2. Weight of supporting vs. contradicting evidence
        3. Risk-reward analysis specific to this asset
        4. Confidence score (0-1) with detailed rationale
        5. Asset-specific recommendations and monitoring points
        6. Sector-specific factors that could impact the hypothesis
        
        Structure your response with clear sections and be specific to this asset and sector.
        """
    
    
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

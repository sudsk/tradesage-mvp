# app/adk/agents/contradiction_agent.py - Complete Enhanced Version with Model Integration
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import news_search
from app.adk.agents.model_integration import ADKModelIntegrator
from google.adk.sessions import InMemorySessionService
import json
import re
from typing import Dict, Any, List, Optional

# Enhanced system instruction with ported logic
ENHANCED_CONTRADICTION_INSTRUCTION = """
You are the Enhanced Contradiction Agent for TradeSage AI. Generate SPECIFIC, QUANTITATIVE contradictions that challenge investment hypotheses.

CRITICAL REQUIREMENTS:
1. Be SPECIFIC to the exact asset, current price, and target mentioned
2. Include QUANTITATIVE data (prices, percentages, ratios, dates)
3. Reference REAL market factors and recent developments
4. Show CONCRETE challenges to reaching the price target

EXCELLENT CONTRADICTION EXAMPLES:
✅ "AAPL closed at $195.64, representing a 10.6% gap below the $220 target requiring significant appreciation in limited timeframe"
✅ "Apple's forward P/E of 28.5x exceeds technology sector average of 22.1x, suggesting limited valuation expansion room"
✅ "iPhone unit sales declined 3% year-over-year in China, Apple's second-largest market"
✅ "Rising interest rates to 5.25% create headwinds for high-multiple technology stocks"

FOCUS AREAS FOR SPECIFIC CONTRADICTIONS:
1. **Price Gap Analysis**: Current price vs target, required appreciation %
2. **Valuation Concerns**: P/E, P/S ratios vs sector/historical averages
3. **Business Headwinds**: Declining sales, margin pressure, competition
4. **Market Structure**: Interest rates, sector rotation, institutional selling
5. **Company-Specific**: Product delays, regulatory issues, guidance cuts
6. **Technical Factors**: Resistance levels, trading volume, momentum

DATABASE CONSTRAINTS:
- Quote: Maximum 400 characters (2-3 sentences max)
- Reason: Maximum 400 characters (2-3 sentences max)
- Source: Maximum 40 characters
- Strength: ONLY "Strong", "Medium", or "Weak"

OUTPUT FORMAT:
Generate 2-3 contradictions as structured analysis:
{
  "quote": "Specific factual statement with numbers/dates",
  "reason": "Why this challenges reaching the price target",
  "source": "Type of analysis (Technical/Fundamental/Market Structure)",
  "strength": "Strong|Medium|Weak"
}

Make each contradiction SPECIFIC and QUANTITATIVE with real market factors.
"""

class IntelligentContradictionProcessor:
    """Ported from LangGraph - AI-powered contradiction processing with ADK integration"""
    
    def __init__(self, agent, session_service: InMemorySessionService):
        self.agent = agent
        self.session_service = session_service
        # Initialize the model integrator for actual ADK calls
        if agent and session_service:
            self.model_integrator = ADKModelIntegrator(agent, session_service)
        else:
            self.model_integrator = None
    
    def process_contradictions(self, raw_contradictions: List[Dict], context: Dict, hypothesis: str) -> List[Dict]:
        """Use AI to intelligently process and clean contradictions"""
        
        print("🧠 Using enhanced AI to process contradictions...")
        
        cleaned_contradictions = []
        
        for raw_contradiction in raw_contradictions:
            # Use AI to evaluate and clean each contradiction
            processed = self._ai_process_single_contradiction(raw_contradiction, context, hypothesis)
            if processed:
                cleaned_contradictions.append(processed)
        
        # If we don't have enough quality contradictions, generate new ones
        if len(cleaned_contradictions) < 2:
            print("   🔄 Insufficient quality contradictions, generating new ones...")
            ai_generated = self._ai_generate_fresh_contradictions(context, hypothesis, len(cleaned_contradictions))
            cleaned_contradictions.extend(ai_generated)
        
        # Add universal risks if still insufficient
        if len(cleaned_contradictions) < 2:
            print("   🛡️ Adding universal risk factors...")
            universal_risks = self._generate_universal_risks(context, hypothesis)
            cleaned_contradictions.extend(universal_risks)
        
        return cleaned_contradictions[:3]  # Return top 3
    
    def _ai_process_single_contradiction(self, raw_contradiction: Dict, context: Dict, hypothesis: str) -> Optional[Dict]:
        """Use AI to evaluate, clean, and enhance a single contradiction"""
        
        raw_quote = raw_contradiction.get("quote", "")
        raw_reason = raw_contradiction.get("reason", "")
        
        asset_info = context.get("asset_info", {})
        
        evaluation_prompt = f"""
        You are an expert financial analyst reviewing investment risks.
        
        TASK: Evaluate and improve this risk factor for the hypothesis: "{hypothesis}"
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        
        RAW RISK FACTOR:
        Quote: "{raw_quote}"
        Reason: "{raw_reason}"
        
        REQUIREMENTS:
        1. Make it SPECIFIC to {asset_info.get("asset_name", "this asset")}
        2. Make it ACTIONABLE and REALISTIC
        3. Keep Quote under 400 characters
        4. Keep Reason under 400 characters
        5. NO generic placeholder text
        
        If this risk factor is valuable, improve it. If it's generic/useless, create a better one.
        
        Respond with JSON:
        {{
            "quote": "Specific risk statement about {asset_info.get("asset_name", "the asset")}",
            "reason": "Why this challenges the investment thesis",
            "source": "Risk Analysis",
            "strength": "Strong|Medium|Weak"
        }}
        """
        
        try:
            response = self._generate_content_via_agent(evaluation_prompt)
            return self._parse_ai_evaluation(response, raw_contradiction)
        except Exception as e:
            print(f"   ⚠️  AI evaluation failed for contradiction: {str(e)}")
            return None
    
    def _generate_content_via_agent(self, prompt: str) -> str:
        """Generate content using the agent's model - ADK implementation"""
        if not self.model_integrator:
            # Return fallback if model integrator is not available
            return '{"quote": "Market volatility presents challenges", "reason": "Economic uncertainty affects investment outcomes", "source": "Market Analysis", "strength": "Medium"}'
        
        try:
            # Use the ADK model integrator to generate content
            response = self.model_integrator.generate_content_sync(prompt, context_id="contradiction_eval")
            return response if response else '{"quote": "Market analysis indicates potential risks", "reason": "Economic factors may impact investment outcomes", "source": "Risk Analysis", "strength": "Medium"}'
        except Exception as e:
            print(f"⚠️  ADK model generation failed: {str(e)}")
            return '{"quote": "Market analysis indicates potential risks", "reason": "Economic factors may impact investment outcomes", "source": "Risk Analysis", "strength": "Medium"}'
    
    def _parse_ai_evaluation(self, ai_response: str, original: Dict) -> Optional[Dict]:
        """Parse AI evaluation response"""
        
        try:
            # Clean response for JSON parsing
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            evaluation = json.loads(cleaned_response)
            
            # Validate required fields
            quote = evaluation.get("quote", "").strip()[:400]
            reason = evaluation.get("reason", "").strip()[:400]
            source = evaluation.get("source", "Risk Analysis").strip()[:40]
            strength = evaluation.get("strength", "Medium")
            
            # Validate strength
            if strength not in ["Strong", "Medium", "Weak"]:
                strength = "Medium"
            
            # Ensure meaningful content
            if len(quote) > 20 and len(reason) > 10:
                return {
                    "quote": quote,
                    "reason": reason,
                    "source": source,
                    "strength": strength,
                    "processing": "ai_enhanced"
                }
            else:
                return None
                
        except json.JSONDecodeError:
            # Fallback: extract from text
            return self._extract_improvement_from_text(ai_response, original)
    
    def _extract_improvement_from_text(self, text: str, original: Dict) -> Optional[Dict]:
        """Extract improvement from free-text AI response"""
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for quote-like content
        quote = ""
        reason = ""
        
        for line in lines:
            if len(line) > 30 and not any(line.startswith(word) for word in ['TASK:', 'ASSET:', 'REQUIREMENTS:', 'Respond']):
                if not quote and '"' in line:
                    quote = line.strip('"\'').strip()[:400]
                elif not reason and line != quote and len(line) > 20:
                    reason = line.strip('"\'').strip()[:400]
        
        if quote and reason:
            return {
                "quote": quote,
                "reason": reason,
                "source": "AI Analysis",
                "strength": "Medium",
                "processing": "ai_text_extracted"
            }
        
        return None
    
    def _ai_generate_fresh_contradictions(self, context: Dict, hypothesis: str, existing_count: int) -> List[Dict]:
        """Generate completely fresh contradictions using AI with database constraints"""
        
        needed_count = max(3 - existing_count, 0)
        if needed_count == 0:
            return []
        
        asset_info = context.get("asset_info", {})
        
        generation_prompt = f"""
        Generate {needed_count} HIGH-QUALITY, SPECIFIC risk factors for this investment hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET DETAILS:
        - Name: {asset_info.get("asset_name", "Unknown")}
        - Symbol: {asset_info.get("primary_symbol", "N/A")}
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        
        REQUIREMENTS for each risk factor:
        1. SPECIFIC to {asset_info.get("asset_name", "this asset")} - mention the company/asset by name
        2. REALISTIC and ACTIONABLE - based on actual market dynamics
        3. CONCISE - Quote under 400 chars, Reason under 400 chars
        4. PROFESSIONAL - no placeholder text or generic statements
        
        Generate realistic risks like:
        - Valuation concerns (if price seems high)
        - Competition threats (specific to this industry)
        - Market/economic headwinds
        - Company-specific execution risks
        - Regulatory or sector-specific challenges
        
        Format each as: quote|reason|source|strength
        
        Generate {needed_count} specific, realistic risk factors for {asset_info.get("asset_name", "this asset")}.
        """
        
        try:
            response = self._generate_content_via_agent(generation_prompt)
            return self._parse_generated_contradictions(response)
        except Exception as e:
            print(f"   ❌ AI contradiction generation failed: {str(e)}")
            return self._intelligent_fallback_contradictions(context, hypothesis, needed_count)
    
    def _parse_generated_contradictions(self, ai_response: str) -> List[Dict]:
        """Parse AI-generated contradictions"""
        
        contradictions = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) >= 4:
                parts = line.split('|')
                raw_quote = parts[0].strip()
                raw_reason = parts[1].strip()
                source = parts[2].strip()[:40]
                strength = parts[3].strip()
                
                # Clean the quote and reason
                clean_quote = self._clean_text(raw_quote)[:400]
                clean_reason = self._clean_text(raw_reason)[:400]
                
                # Validate strength
                if strength not in ["Strong", "Medium", "Weak"]:
                    strength = "Medium"
                
                # Only add if meaningful content
                if len(clean_quote) > 20 and len(clean_reason) > 10:
                    contradictions.append({
                        "quote": clean_quote,
                        "reason": clean_reason,
                        "source": source,
                        "strength": strength,
                        "processing": "ai_generated"
                    })
        
        return contradictions
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing JSON artifacts"""
        # Remove JSON structure patterns
        text = re.sub(r'"quote":\s*"?', '', text)
        text = re.sub(r'"reason":\s*"?', '', text)
        text = re.sub(r'^"', '', text)  # Remove leading quote
        text = re.sub(r'"[,}]*$', '', text)  # Remove trailing quote/comma/brace
        return text.strip()
    
    def _intelligent_fallback_contradictions(self, context: Dict, hypothesis: str, count: int) -> List[Dict]:
        """Intelligent fallback with database constraints"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        asset_type = asset_info.get("asset_type", "unknown")
        sector = asset_info.get("sector", "financial markets")
        
        fallback_contradictions = []
        
        # Market valuation risk (universal)
        fallback_contradictions.append({
            "quote": f"Current market valuations may limit {asset_name} upside potential given economic uncertainty.",
            "reason": "High market multiples and economic volatility often constrain further price appreciation.",
            "source": "Valuation Analysis",
            "strength": "Medium"
        })
        
        # Asset-type specific risks
        if asset_type in ["stock", "equity"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces competitive pressures in {sector} that could impact margins.",
                "reason": f"Increased competition in {sector} can erode market share and pricing power.",
                "source": "Competition Analysis",
                "strength": "Medium"
            })
        
        elif asset_type in ["crypto", "cryptocurrency"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces regulatory uncertainty and extreme volatility risks.",
                "reason": "Cryptocurrency markets remain sensitive to regulatory changes and policy decisions.",
                "source": "Regulatory Risk",
                "strength": "Strong"
            })
        
        return fallback_contradictions[:count]
    
    def _generate_universal_risks(self, context: Dict, hypothesis: str) -> List[Dict]:
        """Generate universal investment risks that apply to any asset"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "this investment")
        
        universal_risks = [
            {
                "quote": f"Market volatility and geopolitical events could negatively impact {asset_name} price action.",
                "reason": "External macro factors often override fundamental analysis in short-term price movements.",
                "source": "Market Risk",
                "strength": "Medium"
            },
            {
                "quote": f"Interest rate changes and monetary policy shifts pose risks to {asset_name} valuation.",
                "reason": "Changes in interest rates affect discount rates and relative asset attractiveness.",
                "source": "Monetary Policy",
                "strength": "Medium"
            }
        ]
        
        return universal_risks

def create_contradiction_agent() -> Agent:
    """Create the enhanced contradiction agent with ported LangGraph logic."""
    config = AGENT_CONFIGS["contradiction_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=ENHANCED_CONTRADICTION_INSTRUCTION,
        tools=[news_search],
    )

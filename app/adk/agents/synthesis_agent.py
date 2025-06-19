# app/adk/agents/synthesis_agent.py - Complete Enhanced Version with Model Integration
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.agents.model_integration import ADKModelIntegrator
from google.adk.sessions import InMemorySessionService
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Enhanced system instruction with ported logic
ENHANCED_SYNTHESIS_INSTRUCTION = """
You are the Enhanced Synthesis Agent for TradeSage AI. Create comprehensive investment analysis with SPECIFIC confirmations and quantitative insights.

CRITICAL: Generate confirmations that are:
1. SPECIFIC to the company's competitive advantages and market position
2. Include QUANTITATIVE business metrics (growth rates, margins, market share)
3. Reference REAL business strengths and institutional support
4. Avoid generic "market analysis" statements

EXCELLENT CONFIRMATION EXAMPLES:
✅ "Apple Inc. maintains dominant 52% smartphone market share in premium segment with iOS ecosystem lock-in effects"
✅ "Services revenue growing 13% annually now represents 22% of total revenue, providing recurring income diversification"
✅ "Institutional ownership at 65% with 1,847 funds holding positions indicates strong professional investor confidence"
✅ "Apple's gross margin of 44.1% significantly exceeds technology hardware average of 31.2%"
✅ "Brand loyalty score of 92% ranks highest in consumer electronics, supporting premium pricing power"

CONFIRMATION FOCUS AREAS:
1. **Competitive Advantages**: Market share, brand strength, ecosystem effects
2. **Financial Strength**: Margins, cash flow, balance sheet metrics
3. **Growth Drivers**: Revenue growth rates, new products, market expansion
4. **Institutional Support**: Ownership %, analyst coverage, recent additions
5. **Business Model**: Recurring revenue, diversification, pricing power
6. **Market Position**: Leadership in key segments, defensive characteristics

DATABASE CONSTRAINTS:
- Quote: Maximum 400 characters (2-3 sentences max)
- Reason: Maximum 400 characters (2-3 sentences max)
- Source: Maximum 40 characters
- Strength: ONLY "Strong", "Medium", or "Weak"

CONFIDENCE SCORING (0.15-0.85 range):
- 0.70+: Strong confirmations outweigh risks, clear path to target
- 0.50-0.69: Balanced evidence, moderate confidence
- 0.30-0.49: Risks outweigh positives, challenging environment
- <0.30: Significant concerns, avoid or wait

OUTPUT: Provide detailed synthesis with specific confirmations containing quantitative business metrics and competitive advantages.
"""

class AssetSpecificConfirmationGenerator:
    """Ported from LangGraph - Generate asset-specific confirmations with ADK integration"""
    
    def __init__(self, agent, session_service: InMemorySessionService):
        self.agent = agent
        self.session_service = session_service
        # Initialize the model integrator for actual ADK calls
        if agent and session_service:
            self.model_integrator = ADKModelIntegrator(agent, session_service)
        else:
            self.model_integrator = None
    
    def generate_high_quality_confirmations(self, context: Dict, hypothesis: str) -> List[Dict]:
        """Generate high-quality confirmations with validation - ported from LangGraph"""
        
        if not context:
            return self._ai_generate_generic_confirmations(hypothesis)
        
        asset_info = context.get("asset_info", {})
        asset_type = asset_info.get("asset_type", "unknown")
        asset_name = asset_info.get("asset_name", "Unknown")
        sector = asset_info.get("sector", "Unknown")
        business_model = asset_info.get("business_model", "")
        current_price = asset_info.get("current_price", "N/A")
        
        print(f"   📈 Generating high-quality confirmations for {asset_type} in {sector}")
        
        # Generate confirmations using enhanced AI prompts
        confirmations = self._ai_generate_specific_confirmations(
            asset_info, asset_type, asset_name, sector, business_model, hypothesis, current_price
        )
        
        # Validate and filter quality
        validated_confirmations = self._validate_confirmation_quality(confirmations, asset_name)
        
        # If insufficient quality, generate fallbacks
        if len(validated_confirmations) < 3:
            print("   🔄 Generating additional high-quality confirmations...")
            additional_confirmations = self._generate_enhanced_fallbacks(asset_info, hypothesis)
            validated_confirmations.extend(additional_confirmations)
        
        return validated_confirmations[:3]  # Limit to 3 most relevant confirmations
    
    def _ai_generate_specific_confirmations(self, asset_info: Dict, asset_type: str, 
                                          asset_name: str, sector: str, business_model: str, 
                                          hypothesis: str, current_price: Any) -> List[Dict]:
        """Generate specific, high-quality confirmations using enhanced prompts"""
        
        prompt = f"""
        You are a senior financial analyst. Generate 3 SPECIFIC, HIGH-QUALITY confirmations that support this investment hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET DETAILS:
        - Company/Asset: {asset_name}
        - Symbol: {asset_info.get("primary_symbol", "N/A")}
        - Type: {asset_type}
        - Sector: {sector}
        - Current Price: {current_price}
        - Business Model: {business_model}
        
        CRITICAL REQUIREMENTS:
        1. Be SPECIFIC to {asset_name} - mention the company/asset by name
        2. Use QUANTITATIVE data when possible (revenue, growth rates, margins, market share)
        3. Reference RECENT/RELEVANT factors (2024-2025 timeframe)
        4. Be ACTIONABLE - investors can verify this information
        5. NO generic placeholder text or "analysis shows" statements
        
        Database Constraints:
        - Quote: Maximum 400 characters (2-3 sentences max)
        - Reason: Maximum 400 characters (2-3 sentences max)
        - Source: Maximum 40 characters (e.g., "Earnings Report")
        - Strength: ONLY "Strong", "Medium", or "Weak"
        
        Generate confirmations that could include:
        - Financial performance metrics (revenue growth, margin expansion)
        - Market position advantages (market share, competitive moats)
        - Product/service momentum (new launches, adoption rates)
        - Industry trends favoring this asset
        - Institutional/analyst support
        
        Format each as exactly: quote|reason|source|strength
        
        Example for Apple:
        Apple Services revenue reached $85.2B in 2024, growing 13% with 70% gross margins|High-margin Services provide recurring revenue and reduce iPhone dependency|Q4 2024 Earnings|Strong
        
        Generate 3 specific, factual confirmations for {asset_name}. NO placeholder content.
        """
        
        try:
            response = self._generate_content_via_agent(prompt)
            return self._parse_context_confirmations(response, asset_name)
        except Exception as e:
            print(f"❌ Specific confirmation generation failed: {str(e)}")
            return self._generate_enhanced_fallbacks(asset_info, hypothesis)
    
    def _generate_content_via_agent(self, prompt: str) -> str:
        """Generate content using the agent's model - ADK implementation"""
        if not self.model_integrator:
            # Return fallback if model integrator is not available
            return "Strong market fundamentals support investment thesis|Market conditions favor price appreciation|Market Analysis|Strong"
        
        try:
            # Use the ADK model integrator to generate content
            response = self.model_integrator.generate_content_sync(prompt, context_id="confirmation_gen")
            return response if response else "Market fundamentals support investment outlook|Current conditions favor positive performance|Market Analysis|Medium"
        except Exception as e:
            print(f"⚠️  ADK model generation failed: {str(e)}")
            return "Market fundamentals support investment outlook|Current conditions favor positive performance|Market Analysis|Medium"
    
    def _parse_context_confirmations(self, response_text: str, asset_name: str) -> List[Dict]:
        """Parse AI-generated confirmations with strict validation"""
        confirmations = []
        
        # Try structured format first
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) >= 4:
                parts = line.split('|')
                quote = parts[0].strip()[:400]  # Enforce 400 char limit
                reason = parts[1].strip()[:400]  # Enforce 400 char limit  
                source = parts[2].strip()[:40]   # Enforce 40 char limit
                strength = parts[3].strip()
                
                # Validate strength
                if strength not in ["Strong", "Medium", "Weak"]:
                    strength = "Medium"
                
                # Only add if meaningful content
                if len(quote) > 25 and len(reason) > 15:
                    confirmations.append({
                        "quote": quote,
                        "reason": reason,
                        "source": source,
                        "strength": strength
                    })
        
        # Fallback parsing if structured format fails
        if not confirmations:
            sections = response_text.split('\n\n') if '\n\n' in response_text else response_text.split('\n')
            for section in sections:
                section = section.strip()
                if len(section) > 40 and not section.startswith(('HYPOTHESIS:', 'ASSET:', 'CRITICAL:', 'Example:')):
                    # Clean section
                    section = section.replace('1.', '').replace('2.', '').replace('3.', '').replace('-', '').strip()
                    
                    if len(section) > 30:
                        quote = section[:350] + "..." if len(section) > 350 else section
                        confirmations.append({
                            "quote": quote,
                            "reason": f"This factor supports {asset_name} positive investment outlook and price appreciation potential.",
                            "source": "Market Analysis",
                            "strength": "Medium"
                        })
                        if len(confirmations) >= 3:
                            break
        
        return confirmations
    
    def _validate_confirmation_quality(self, confirmations: List[Dict], asset_name: str) -> List[Dict]:
        """Validate confirmation quality and filter out poor content - ported from LangGraph"""
        
        validated = []
        
        for conf in confirmations:
            quote = conf.get("quote", "").lower()
            
            # Reject generic/placeholder content
            if any(phrase in quote for phrase in [
                "here are", "supporting the hypothesis", "analysis shows", "market analysis provides",
                "quote", "confirmation", "supports the", "this factor", "evidence suggests"
            ]):
                print(f"   🗑️ Rejected generic confirmation: {quote[:50]}...")
                continue
            
            # Require asset name mention (with some flexibility)
            asset_keywords = asset_name.lower().split()
            if not any(keyword in quote for keyword in asset_keywords):
                print(f"   ⚠️ Confirmation doesn't mention asset: {quote[:50]}...")
                continue
                
            # Require minimum length for substance
            if len(quote) < 40:
                print(f"   ⚠️ Confirmation too short: {quote}")
                continue
                
            validated.append(conf)
        
        return validated
    
    def _generate_enhanced_fallbacks(self, asset_info: Dict, hypothesis: str) -> List[Dict]:
        """Generate enhanced, intelligent fallback confirmations - ported from LangGraph"""
        
        asset_type = asset_info.get("asset_type", "unknown")
        asset_name = asset_info.get("asset_name", "Unknown")
        sector = asset_info.get("sector", "Unknown")
        current_year = datetime.now().year
        
        fallbacks = []
        
        if asset_type == "stock":
            fallbacks.extend([
                {
                    "quote": f"{asset_name} maintains strong market position in {sector} with competitive advantages and brand recognition.",
                    "reason": f"Market leadership in {sector} provides pricing power and defensive characteristics supporting valuation.",
                    "source": "Competitive Analysis",
                    "strength": "Medium"
                },
                {
                    "quote": f"Institutional ownership and analyst coverage support continued investor interest in {asset_name} shares.",
                    "reason": "Professional investor backing provides liquidity and validates investment thesis fundamentals.",
                    "source": "Institutional Data",
                    "strength": "Medium"
                },
                {
                    "quote": f"{asset_name} benefits from {sector} sector tailwinds and digital transformation trends in {current_year}.",
                    "reason": f"Secular growth trends in {sector} create multiple expansion opportunities for established players.",
                    "source": "Sector Trends",
                    "strength": "Medium"
                }
            ])
        
        elif asset_type in ["crypto", "cryptocurrency"]:
            fallbacks.extend([
                {
                    "quote": f"{asset_name} gains from increasing institutional adoption and mainstream cryptocurrency acceptance.",
                    "reason": "Growing institutional allocation to crypto assets drives demand and reduces volatility over time.",
                    "source": "Adoption Trends",
                    "strength": "Strong"
                },
                {
                    "quote": f"Limited supply characteristics and network effects support {asset_name} long-term value proposition.",
                    "reason": "Scarcity economics combined with growing utility create fundamental demand-supply imbalance.",
                    "source": "Fundamental Analysis",
                    "strength": "Medium"
                }
            ])
        
        elif asset_type == "commodity":
            fallbacks.extend([
                {
                    "quote": f"Global economic recovery and industrial demand support {asset_name} price fundamentals.",
                    "reason": "Economic growth drives industrial consumption and infrastructure investment increasing commodity demand.",
                    "source": "Economic Analysis",
                    "strength": "Medium"
                }
            ])
        
        else:
            # Generic but asset-specific fallbacks
            fallbacks.extend([
                {
                    "quote": f"Market fundamentals and technical indicators align to support {asset_name} price appreciation potential.",
                    "reason": f"Convergence of fundamental and technical factors creates favorable risk-reward profile for {asset_type} investment.",
                    "source": "Technical Analysis",
                    "strength": "Medium"
                }
            ])
        
        return fallbacks
    
    def _ai_generate_generic_confirmations(self, hypothesis: str) -> List[Dict]:
        """Enhanced AI fallback when no context is available"""
        
        prompt = f"""
        Generate 3 realistic confirmations that support this investment hypothesis:
        
        "{hypothesis}"
        
        Requirements:
        - Be specific to the asset mentioned in the hypothesis
        - Use realistic market factors
        - Keep Quote under 400 characters
        - Keep Reason under 400 characters
        - Source under 40 characters
        
        Format each as: quote|reason|source|strength
        
        Focus on factors like:
        - Market trends
        - Economic conditions  
        - Industry dynamics
        - Technical factors
        """
        
        try:
            response = self._generate_content_via_agent(prompt)
            return self._parse_context_confirmations(response, "the asset")
        except Exception as e:
            print(f"❌ Generic confirmation generation failed: {str(e)}")
            return [{
                "quote": "Market fundamentals and economic conditions support positive investment outlook.",
                "reason": "Current market environment creates opportunities for price appreciation in selected assets.",
                "source": "Market Analysis",
                "strength": "Medium"
            }]

class ConfidenceCalculator:
    """Ported realistic confidence scoring from LangGraph"""
    
    @staticmethod
    def calculate_realistic_confidence(contradictions: List[Dict], confirmations: List[Dict], context: Dict) -> float:
        """Calculate realistic confidence score based on evidence quality - ported from LangGraph"""
        
        # Base score from evidence balance
        conf_count = len(confirmations)
        contra_count = len(contradictions)
        
        if conf_count == 0 and contra_count == 0:
            base_score = 0.3  # Low confidence for no evidence
        elif contra_count == 0:
            # Having no contradictions is unrealistic - cap confidence
            base_score = 0.65  # Cap at 65% when no risks identified
        elif conf_count == 0:
            base_score = 0.25  # Very low when only risks identified  
        else:
            # Balanced scoring based on evidence ratio
            ratio = conf_count / (conf_count + contra_count)
            base_score = 0.25 + (ratio * 0.5)  # Range: 0.25 to 0.75
        
        # Adjust for evidence strength
        conf_strength_bonus = 0
        for conf in confirmations:
            strength = conf.get("strength", "Medium").lower()
            if strength == "strong":
                conf_strength_bonus += 0.05
            elif strength == "medium":
                conf_strength_bonus += 0.02
        
        contra_strength_penalty = 0
        for contra in contradictions:
            strength = contra.get("strength", "Medium").lower()
            if strength == "strong":
                contra_strength_penalty += 0.08
            elif strength == "medium":
                contra_strength_penalty += 0.03
        
        # Context quality bonus
        context_bonus = 0
        if context and context.get("asset_info", {}).get("asset_type") != "unknown":
            context_bonus = 0.05
        
        # Final calculation
        final_score = base_score + conf_strength_bonus - contra_strength_penalty + context_bonus
        
        # Realistic bounds (15% minimum, 85% maximum)
        return max(0.15, min(0.85, final_score))

def create_synthesis_agent() -> Agent:
    """Create the synthesis agent with ported LangGraph logic."""
    config = AGENT_CONFIGS["synthesis_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=ENHANCED_SYNTHESIS_INSTRUCTION,
        tools=[],
    )

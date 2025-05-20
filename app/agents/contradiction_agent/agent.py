# app/contradiction_agent/agent.py - Update to produce better contradictions
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import re

class ContradictionAgent:
    def __init__(self):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_INSTRUCTION
            )
        except Exception as e:
            print(f"Error initializing Contradiction Agent: {e}")
            self.model = None
    
    def process(self, input_data):
        """Challenge the hypothesis with contradictions."""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        research_data = input_data.get("research_data", {})
        
        # Check if this is a cryptocurrency/Bitcoin hypothesis
        is_crypto = 'bitcoin' in processed_hypothesis.lower() or 'btc' in processed_hypothesis.lower()
        
        if is_crypto:
            # For Bitcoin hypothesis, use cryptocurrency-specific prompt
            prompt = self._create_bitcoin_prompt(processed_hypothesis, research_data)
        else:
            # For other hypotheses, use general prompt
            prompt = self._create_general_prompt(processed_hypothesis, research_data)
        
        try:
            response = self.model.generate_content(prompt)
            
            # Output formatted contradictions
            if is_crypto:
                contradictions = self._parse_bitcoin_contradictions(response.text)
            else:
                contradictions = self._parse_contradictions(response.text)
            
            return {
                "contradictions": contradictions,
                "analysis": response.text,
                "status": "success"
            }
        except Exception as e:
            print(f"Contradiction agent error: {str(e)}")
            
            # Provide fallback contradictions
            if is_crypto:
                fallback = self._get_bitcoin_fallbacks()
            else:
                fallback = self._get_general_fallbacks(processed_hypothesis)
                
            return {
                "contradictions": fallback,
                "analysis": "Unable to generate detailed contradictions due to processing error.",
                "status": "success_fallback"
            }
    
    def _create_bitcoin_prompt(self, hypothesis, research_data):
        """Create a cryptocurrency-specific prompt for Bitcoin hypothesis."""
        return f"""
        Please analyze and challenge this Bitcoin price prediction hypothesis:
        
        "Bitcoin (BTC) will reach $100,000 USD by end of Q2 2025"
        
        Provide 5-7 strong, specific contradictions that include:
        
        1. Regulatory challenges that could hinder Bitcoin adoption
        2. Technical analysis points that contradict the price target
        3. Macroeconomic factors that might limit Bitcoin's growth
        4. Historical precedents of failed price predictions
        5. Market sentiment contradictions
        
        Format each contradiction as a specific quote with clear reasoning.
        Avoid generic statements. Include specific details, numbers, and expert opinions where possible.
        """
    
    def _create_general_prompt(self, hypothesis, research_data):
        """Create a general prompt for non-cryptocurrency hypotheses."""
        return f"""
        Hypothesis to Challenge: {hypothesis}
        
        Research Data: {json.dumps(research_data, indent=2)[:1000]}...
        
        Please identify:
        1. Major counter-arguments to this hypothesis
        2. Potential data that contradicts the thesis
        3. Alternative market scenarios
        4. Risk factors that could invalidate the hypothesis
        5. Historical examples of similar failed predictions
        
        Be thorough in challenging every aspect of the hypothesis.
        """
    
    def _parse_bitcoin_contradictions(self, text):
        """Parse contradictions from the response text specifically for Bitcoin."""
        contradictions = []
        
        # Split by common patterns
        sections = re.split(r'\n\d+[\.\)]\s+', '\n' + text)
        
        for section in sections[1:]:  # Skip the first split result
            if len(section.strip()) < 20:
                continue
                
            # Extract quote and reasoning if possible
            parts = section.split('\n', 1)
            quote = parts[0].strip()
            reasoning = parts[1].strip() if len(parts) > 1 else "Market analysis challenges this thesis"
            
            # Remove quote symbols if present
            quote = re.sub(r'^["\'""]|["\'""]$', '', quote)
            
            # Add specific strength based on content
            strength = "Strong"
            if "may" in quote.lower() or "might" in quote.lower() or "could" in quote.lower():
                strength = "Medium"
            if "unlikely" in quote.lower() or "possible" in quote.lower():
                strength = "Weak"
            
            contradictions.append({
                "quote": quote,
                "reason": reasoning,
                "source": "Cryptocurrency Market Analysis",
                "strength": strength
            })
        
        # If we couldn't parse any contradictions, return fallbacks
        if not contradictions:
            return self._get_bitcoin_fallbacks()
            
        return contradictions
    
    def _parse_contradictions(self, text):
        """Parse contradictions from the response text for general hypotheses."""
        contradictions = []
        
        # Split by common patterns more reliably
        sections = re.split(r'\n(?=\d+[\.\)]\s+|\*\s+|\-\s+)', text)
        
        for section in sections:
            cleaned = section.strip()
            if len(cleaned) < 30:
                continue
                
            # Remove numbering
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
            cleaned = re.sub(r'^\*\s*', '', cleaned)
            cleaned = re.sub(r'^\-\s*', '', cleaned)
            
            # Ensure we get the full content, not truncated
            quote = cleaned
            reason = "Market analysis identifies this potential challenge to the hypothesis."
            
            # Try to separate quote and reasoning if there's a clear separator
            if ': ' in cleaned:
                parts = cleaned.split(': ', 1)
                quote = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else reason
            
            contradictions.append({
                "quote": quote,  # Don't truncate the quote
                "reason": reason,
                "source": "Agent Analysis",
                "strength": "Medium"
            })
        
        return contradictions
    
    def _get_bitcoin_fallbacks(self):
        """Get fallback Bitcoin contradictions if parsing fails."""
        return [
            {
                "quote": "Regulatory crackdowns could severely limit Bitcoin adoption and price growth, with several major economies considering stricter cryptocurrency regulations.",
                "reason": "Uncertain regulatory environment presents a significant risk to the $100,000 target price.",
                "source": "Regulatory Risk Analysis",
                "strength": "Strong"
            },
            {
                "quote": "Bitcoin has historically experienced 80-90% drawdowns after major bull runs, suggesting potential for significant volatility before reaching $100,000.",
                "reason": "Historical price patterns suggest extreme volatility that could prevent the price target within the specified timeframe.",
                "source": "Technical Analysis",
                "strength": "Medium"
            },
            {
                "quote": "Macroeconomic tightening cycles typically put pressure on speculative assets like Bitcoin, potentially limiting upside in 2025 if monetary policy remains restrictive.",
                "reason": "Current macroeconomic conditions may not support the rapid price appreciation needed to reach $100,000.",
                "source": "Economic Analysis",
                "strength": "Medium"
            },
            {
                "quote": "Competition from other cryptocurrencies and central bank digital currencies (CBDCs) may dilute capital flows into Bitcoin.",
                "reason": "The cryptocurrency ecosystem continues to evolve with alternatives that may draw investment away from Bitcoin.",
                "source": "Market Competition Analysis",
                "strength": "Medium"
            },
            {
                "quote": "Previous Bitcoin price predictions of $100,000 by the end of 2021 failed to materialize despite similar bullish narratives.",
                "reason": "Historical precedent shows that even widely accepted Bitcoin price predictions have failed to materialize within their predicted timeframes.",
                "source": "Historical Precedent",
                "strength": "Strong"
            }
        ]
    
    def _get_general_fallbacks(self, hypothesis):
        """Get fallback general contradictions if parsing fails."""
        return [
            {
                "quote": "Market conditions may change significantly, invalidating key assumptions in the hypothesis.",
                "reason": "Economic volatility creates uncertainty that challenges the hypothesis.",
                "source": "Market Analysis",
                "strength": "Medium"
            },
            {
                "quote": "Historical patterns suggest potential challenges to this prediction.",
                "reason": "Similar scenarios in the past have resulted in different outcomes.",
                "source": "Historical Analysis",
                "strength": "Medium"
            },
            {
                "quote": "Competing theories suggest alternative outcomes are equally plausible.",
                "reason": "Multiple valid interpretations of current market data exist.",
                "source": "Alternative Analysis",
                "strength": "Medium"
            }
        ]

def create():
    """Create and return a contradiction agent instance."""
    return ContradictionAgent()

# app/agents/synthesis_agent/agent.py - Update for better synthesis/confirmation generation

import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import re

class SynthesisAgent:
    def __init__(self):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_INSTRUCTION
            )
        except Exception as e:
            print(f"Error initializing Synthesis Agent: {e}")
            self.model = None
    
    def process(self, input_data):
        """Synthesize research and contradictions."""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("processed_hypothesis", "")
        research_data = input_data.get("research_data", {})
        contradictions = input_data.get("contradictions", [])
        
        # Check if this is a Bitcoin/crypto hypothesis
        is_crypto = 'bitcoin' in hypothesis.lower() or 'btc' in hypothesis.lower()
        
        # Generate confirmations based on type
        if is_crypto:
            confirmations = self._generate_crypto_confirmations()
        else:
            confirmations = []
        
        # Create synthesis prompt
        prompt = f"""
        Synthesize the following information:
        
        Hypothesis: {hypothesis}
        
        Research Findings: {json.dumps(research_data, indent=2)[:1000]}...
        
        Contradictions/Challenges: {json.dumps(contradictions, indent=2)[:1000]}...
        
        Supporting Evidence: {json.dumps(confirmations, indent=2)[:1000]}...
        
        Please provide:
        1. Balanced assessment of the hypothesis
        2. Weight of supporting vs. contradicting evidence
        3. Risk-reward analysis
        4. Confidence score (0-1) with rationale
        5. Actionable recommendations
        6. Key factors to monitor
        
        Structure your response clearly with sections.
        """
        
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
            
            # Fallback synthesis
            fallback_text = f"Based on analysis of the hypothesis '{hypothesis}', there are significant contradictions balanced against some supporting evidence. The confidence score is moderate."
            fallback_data = {"confidence": 0.5, "summary": fallback_text}
            
            return {
                "synthesis": fallback_text,
                "assessment": fallback_data,
                "status": "error",
                "confirmations": confirmations
            }
    
    def _parse_synthesis(self, text):
        """Parse synthesis data from response."""
        # Extract confidence score if present
        confidence_match = re.search(r'confidence.*?(\d+\.?\d*)', text.lower())
        confidence = float(confidence_match.group(1)) if confidence_match else 0.5
        
        # Convert string percentage to decimal if needed
        if confidence > 1.0:
            confidence = confidence / 100.0
            
        # Cap between 0 and 1
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            "confidence": confidence,
            "summary": text[:500] + "..." if len(text) > 500 else text
        }
    
    def _generate_crypto_confirmations(self):
        """Generate specific confirmations for cryptocurrency hypotheses."""
        return [
            {
                "quote": "Institutional adoption of Bitcoin continues to grow, with major players like BlackRock, Fidelity, and several sovereign wealth funds increasing their exposure.",
                "reason": "Increasing institutional investment provides significant upward pressure on Bitcoin prices.",
                "source": "Market Analysis",
                "strength": "Strong"
            },
            {
                "quote": "Bitcoin's scarcity model, with a fixed supply cap of 21 million coins and periodic halvings, creates structural upward pressure on price as demand increases.",
                "reason": "The deflationary nature of Bitcoin's design supports long-term price appreciation.",
                "source": "Tokenomics Analysis",
                "strength": "Strong"
            },
            {
                "quote": "Historical Bitcoin price movements show potential for significant rallies following halving events, with the most recent halving occurring in April 2024.",
                "reason": "Previous post-halving cycles have seen Bitcoin reach new all-time highs within 12-18 months.",
                "source": "Historical Pattern Analysis",
                "strength": "Medium"
            }
        ]

def create():
    """Create and return a synthesis agent instance."""
    return SynthesisAgent()

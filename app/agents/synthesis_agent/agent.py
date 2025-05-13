# app/agents/synthesis_agent/agent.py
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
        
        prompt = f"""
        Synthesize the following information:
        
        Hypothesis: {hypothesis}
        
        Research Findings: {json.dumps(research_data, indent=2)}
        
        Contradictions/Challenges: {json.dumps(contradictions, indent=2)}
        
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
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _parse_synthesis(self, text):
        """Parse synthesis data from response."""
        # Extract confidence score if present
        confidence_match = re.search(r'confidence.*?(\d+\.?\d*)', text.lower())
        confidence = float(confidence_match.group(1)) if confidence_match else 0.5
        
        return {
            "confidence": confidence,
            "summary": text[:500] + "..." if len(text) > 500 else text
        }

def create():
    """Create and return a synthesis agent instance."""
    return SynthesisAgent()

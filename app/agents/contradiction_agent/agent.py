# app/agents/contradiction_agent/agent.py
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json

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
        
        hypothesis = input_data.get("processed_hypothesis", "")
        research_data = input_data.get("research_data", {})
        
        prompt = f"""
        Hypothesis to Challenge: {hypothesis}
        
        Research Data: {json.dumps(research_data, indent=2)}
        
        Please identify:
        1. Major counter-arguments to this hypothesis
        2. Potential data that contradicts the thesis
        3. Alternative market scenarios
        4. Risk factors that could invalidate the hypothesis
        5. Historical examples of similar failed predictions
        
        Be thorough in challenging every aspect of the hypothesis.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract contradictions from response
            contradictions = self._parse_contradictions(response.text)
            
            return {
                "contradictions": contradictions,
                "analysis": response.text,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _parse_contradictions(self, text):
        """Parse contradictions from the response text."""
        # Simple parsing - in production, you might want more sophisticated extraction
        sections = text.split('\n\n')
        contradictions = []
        
        for i, section in enumerate(sections):
            if section.strip():
                contradictions.append({
                    "id": i + 1,
                    "content": section.strip(),
                    "type": "challenge"
                })
        
        return contradictions

def create():
    """Create and return a contradiction agent instance."""
    return ContradictionAgent()


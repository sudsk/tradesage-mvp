# app/agents/alert_agent/agent.py
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
from datetime import datetime, timedelta

class AlertAgent:
    def __init__(self):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_INSTRUCTION
            )
        except Exception as e:
            print(f"Error initializing Alert Agent: {e}")
            self.model = None
    
    def process(self, input_data):
        """Generate alerts and recommendations."""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("processed_hypothesis", "")
        synthesis = input_data.get("synthesis", "")
        research_data = input_data.get("research_data", {})
        
        prompt = f"""
        Based on the following analysis, generate specific alerts and recommendations:
        
        Hypothesis: {hypothesis}
        
        Synthesis: {synthesis}
        
        Research Data: {json.dumps(research_data, indent=2)}
        
        Please provide:
        1. Immediate actionable alerts
        2. Entry/exit criteria
        3. Price targets and stop-losses
        4. Timeline for monitoring
        5. Key events to watch
        6. Risk management recommendations
        
        Make alerts specific and implementable.
        """
        
        try:
            response = self.model.generate_content(prompt)
            alerts = self._parse_alerts(response.text)
            
            return {
                "alerts": alerts,
                "recommendations": response.text,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _parse_alerts(self, text):
        """Parse alerts from response text."""
        alerts = []
        lines = text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['alert:', 'watch:', 'trigger:', 'recommendation:']):
                alerts.append({
                    "id": len(alerts) + 1,
                    "type": "alert",
                    "message": line.strip(),
                    "timestamp": datetime.now().isoformat(),
                    "priority": "medium"
                })
        
        return alerts

def create():
    """Create and return an alert agent instance."""
    return AlertAgent()
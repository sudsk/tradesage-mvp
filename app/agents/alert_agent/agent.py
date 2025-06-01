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
        """Generate context-aware alerts and recommendations"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("processed_hypothesis", "")
        synthesis = input_data.get("synthesis", "")
        research_data = input_data.get("research_data", {})
        context = input_data.get("context", {})
        contradictions = input_data.get("contradictions", [])
        confidence_score = input_data.get("confidence_score", 0.5)
        
        # Generate context-aware alerts
        alerts = self._generate_context_aware_alerts(
            context, hypothesis, contradictions, confidence_score
        )
        
        # Generate intelligent recommendations
        recommendations = self._generate_context_aware_recommendations(
            context, hypothesis, synthesis, research_data
        )
        
        return {
            "alerts": alerts,
            "recommendations": recommendations,
            "status": "success"
        }
    
    def _generate_context_aware_alerts(self, context: Dict, hypothesis: str, 
                                     contradictions: List, confidence_score: float) -> List[Dict]:
        """Generate alerts specific to the asset and context"""
        
        alerts = []
        asset_info = context.get("asset_info", {})
        hypothesis_details = context.get("hypothesis_details", {})
        risk_analysis = context.get("risk_analysis", {})
        
        asset_name = asset_info.get("asset_name", "Asset")
        asset_type = asset_info.get("asset_type", "unknown")
        price_target = hypothesis_details.get("price_target")
        timeframe = hypothesis_details.get("timeframe", "unspecified timeframe")
        primary_risks = risk_analysis.get("primary_risks", [])
        
        # Entry alert based on confidence
        if confidence_score > 0.7:
            alerts.append({
                "id": 1,
                "type": "entry_signal",
                "message": f"High confidence signal: Consider initiating position in {asset_name} targeting {price_target} by {timeframe}",
                "priority": "high",
                "timestamp": datetime.now().isoformat(),
                "action": "consider_entry"
            })
        elif confidence_score > 0.5:
            alerts.append({
                "id": 1,
                "type": "watch_signal", 
                "message": f"Medium confidence: Monitor {asset_name} for confirmation before entering position",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "monitor"
            })
        else:
            alerts.append({
                "id": 1,
                "type": "caution_signal",
                "message": f"Low confidence: Exercise caution with {asset_name} position due to significant contradictions",
                "priority": "high",
                "timestamp": datetime.now().isoformat(),
                "action": "avoid_or_wait"
            })
        
        # Risk-specific alerts
        for i, risk in enumerate(primary_risks[:2]):
            alerts.append({
                "id": i + 2,
                "type": "risk_alert",
                "message": f"Monitor {risk} as key risk factor for {asset_name}",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "monitor_risk"
            })
        
        # Contradiction alerts
        strong_contradictions = [c for c in contradictions if c.get("strength", "").lower() == "strong"]
        if len(strong_contradictions) >= 2:
            alerts.append({
                "id": len(alerts) + 1,
                "type": "contradiction_alert",
                "message": f"Multiple strong contradictions identified for {asset_name} - consider position sizing carefully",
                "priority": "high", 
                "timestamp": datetime.now().isoformat(),
                "action": "reduce_position_size"
            })
        
        return alerts
    
    def _generate_context_aware_recommendations(self, context: Dict, hypothesis: str,
                                              synthesis: str, research_data: Dict) -> str:
        """Generate specific recommendations based on context"""
        
        asset_info = context.get("asset_info", {})
        hypothesis_details = context.get("hypothesis_details", {})
        research_guidance = context.get("research_guidance", {})
        
        prompt = f"""
        Generate specific, actionable recommendations for this investment hypothesis:
        
        HYPOTHESIS: {hypothesis}
        
        ASSET: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        TYPE: {asset_info.get("asset_type", "Unknown")}
        SECTOR: {asset_info.get("sector", "Unknown")}
        TARGET: {hypothesis_details.get("price_target", "Not specified")}
        TIMEFRAME: {hypothesis_details.get("timeframe", "Not specified")}
        
        KEY METRICS TO MONITOR: {research_guidance.get("key_metrics", [])}
        EVENTS TO WATCH: {research_guidance.get("monitoring_events", [])}
        
        SYNTHESIS: {synthesis[:500]}...
        
        Provide specific recommendations including:
        1. Entry/exit criteria specific to this asset
        2. Position sizing recommendations
        3. Stop-loss levels appropriate for this asset type
        4. Key monitoring points and triggers
        5. Timeline for reassessment
        6. Asset-specific risk management
        
        Make all recommendations specific to this asset and sector, not generic advice.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Intelligent recommendation generation failed. Monitor {asset_info.get('asset_name', 'asset')} closely and manage risk appropriately for {asset_info.get('asset_type', 'this asset type')}."
    
def create():
    """Create and return an alert agent instance."""
    return AlertAgent()

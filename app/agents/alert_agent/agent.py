# app/agents/alert_agent/agent.py - Intelligent, context-driven alerts
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class AlertAgent:
    """Intelligent Alert Agent using context - no hardcoded recommendations"""
    
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
        """Generate intelligent, context-aware alerts and recommendations"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("processed_hypothesis", "")
        synthesis = input_data.get("synthesis", "")
        research_data = input_data.get("research_data", {})
        context = input_data.get("context", {})
        contradictions = input_data.get("contradictions", [])
        confirmations = input_data.get("confirmations", [])
        confidence_score = input_data.get("confidence_score", 0.5)
        
        print(f"🚨 Generating intelligent alerts for: {hypothesis}")
        
        # Log context usage
        if context:
            self._log_context_usage(context)
        
        # Generate context-aware alerts
        alerts = self._generate_intelligent_alerts(
            context, hypothesis, contradictions, confirmations, confidence_score
        )
        
        # Generate context-aware recommendations
        recommendations = self._generate_intelligent_recommendations(
            context, hypothesis, synthesis, research_data, confidence_score
        )
        
        print(f"   ✅ Generated {len(alerts)} context-aware alerts")
        
        return {
            "alerts": alerts,
            "recommendations": recommendations,
            "status": "success"
        }
    
    def _log_context_usage(self, context: Dict) -> None:
        """Log how context is being used"""
        asset_info = context.get("asset_info", {})
        hypothesis_details = context.get("hypothesis_details", {})
        
        print(f"🔧 Using context: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('asset_type', 'Unknown')})")
        print(f"   🎯 Direction: {hypothesis_details.get('direction', 'Unknown')}")
        print(f"   💰 Target: {hypothesis_details.get('price_target', 'Not specified')}")
    
    def _generate_intelligent_alerts(self, context: Dict, hypothesis: str, 
                                   contradictions: List, confirmations: List, 
                                   confidence_score: float) -> List[Dict]:
        """Generate alerts specific to the asset and context - no hardcoding"""
        
        alerts = []
        
        if not context:
            return self._generate_generic_alerts(hypothesis, confidence_score)
        
        asset_info = context.get("asset_info", {})
        hypothesis_details = context.get("hypothesis_details", {})
        risk_analysis = context.get("risk_analysis", {})
        research_guidance = context.get("research_guidance", {})
        
        asset_name = asset_info.get("asset_name", "Asset")
        asset_type = asset_info.get("asset_type", "unknown")
        primary_symbol = asset_info.get("primary_symbol", "N/A")
        price_target = hypothesis_details.get("price_target")
        timeframe = hypothesis_details.get("timeframe", "unspecified timeframe")
        direction = hypothesis_details.get("direction", "neutral")
        primary_risks = risk_analysis.get("primary_risks", [])
        monitoring_events = research_guidance.get("monitoring_events", [])
        
        alert_id = 1
        
        # 1. Entry/Position Signal based on confidence and context
        entry_alert = self._create_entry_alert(
            alert_id, asset_name, asset_type, primary_symbol, price_target, 
            timeframe, direction, confidence_score
        )
        alerts.append(entry_alert)
        alert_id += 1
        
        # 2. Risk-specific alerts based on context
        for risk in primary_risks[:2]:  # Top 2 risks
            risk_alert = {
                "id": alert_id,
                "type": "risk_monitoring",
                "message": f"Monitor {risk} as key risk factor for {asset_name} ({primary_symbol})",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "monitor_risk_factor",
                "risk_factor": risk,
                "asset_specific": True
            }
            alerts.append(risk_alert)
            alert_id += 1
        
        # 3. Event monitoring alerts based on context
        for event in monitoring_events[:2]:  # Top 2 events
            event_alert = {
                "id": alert_id,
                "type": "event_monitoring",
                "message": f"Watch for {event} related to {asset_name} as potential catalyst",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "monitor_event",
                "event_type": event,
                "asset_specific": True
            }
            alerts.append(event_alert)
            alert_id += 1
        
        # 4. Contradiction-based alerts
        strong_contradictions = [c for c in contradictions if c.get("strength", "").lower() == "strong"]
        if len(strong_contradictions) >= 2:
            contradiction_alert = {
                "id": alert_id,
                "type": "contradiction_warning",
                "message": f"Multiple strong contradictions identified for {asset_name} - consider position sizing carefully",
                "priority": "high",
                "timestamp": datetime.now().isoformat(),
                "action": "reduce_position_size",
                "contradiction_count": len(strong_contradictions),
                "asset_specific": True
            }
            alerts.append(contradiction_alert)
            alert_id += 1
        
        # 5. Asset-type specific alerts
        type_specific_alert = self._create_asset_type_alert(
            alert_id, asset_type, asset_name, primary_symbol
        )
        if type_specific_alert:
            alerts.append(type_specific_alert)
        
        return alerts
    
    def _create_entry_alert(self, alert_id: int, asset_name: str, asset_type: str, 
                          primary_symbol: str, price_target: Any, timeframe: str, 
                          direction: str, confidence_score: float) -> Dict:
        """Create intelligent entry alert based on confidence and context"""
        
        target_text = f"${price_target}" if price_target else "target level"
        direction_text = f"{direction} move to " if direction != "neutral" else "move to "
        
        if confidence_score > 0.7:
            return {
                "id": alert_id,
                "type": "high_confidence_signal",
                "message": f"High confidence signal: Consider initiating {direction} position in {asset_name} ({primary_symbol}) targeting {target_text} by {timeframe}",
                "priority": "high",
                "timestamp": datetime.now().isoformat(),
                "action": "consider_entry",
                "confidence_level": "high",
                "asset_specific": True
            }
        elif confidence_score > 0.5:
            return {
                "id": alert_id,
                "type": "medium_confidence_signal",
                "message": f"Medium confidence: Monitor {asset_name} ({primary_symbol}) for confirmation signals before entering {direction} position",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "monitor_for_entry",
                "confidence_level": "medium",
                "asset_specific": True
            }
        else:
            return {
                "id": alert_id,
                "type": "low_confidence_warning",
                "message": f"Low confidence: Exercise caution with {asset_name} ({primary_symbol}) due to mixed signals and significant contradictions",
                "priority": "high",
                "timestamp": datetime.now().isoformat(),
                "action": "avoid_or_wait",
                "confidence_level": "low",
                "asset_specific": True
            }
    
    def _create_asset_type_alert(self, alert_id: int, asset_type: str, 
                               asset_name: str, primary_symbol: str) -> Dict:
        """Create asset-type specific alerts using context intelligence"""
        
        if asset_type in ["crypto", "cryptocurrency"]:
            return {
                "id": alert_id,
                "type": "crypto_volatility_warning",
                "message": f"Cryptocurrency volatility: Set appropriate stop-losses for {asset_name} ({primary_symbol}) due to high volatility nature",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "set_wide_stops",
                "asset_type_specific": True
            }
        elif asset_type == "stock":
            return {
                "id": alert_id,
                "type": "earnings_monitoring",
                "message": f"Monitor upcoming earnings announcements for {asset_name} ({primary_symbol}) as potential volatility catalyst",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "monitor_earnings",
                "asset_type_specific": True
            }
        elif asset_type == "commodity":
            return {
                "id": alert_id,
                "type": "supply_demand_monitoring",
                "message": f"Monitor supply/demand dynamics and geopolitical factors affecting {asset_name} prices",
                "priority": "medium",
                "timestamp": datetime.now().isoformat(),
                "action": "monitor_fundamentals",
                "asset_type_specific": True
            }
        
        return None
    
    def _generate_generic_alerts(self, hypothesis: str, confidence_score: float) -> List[Dict]:
        """Generate generic alerts when context is not available"""
        return [
            {
                "id": 1,
                "type": "generic_signal",
                "message": f"Analysis complete for hypothesis - confidence level: {confidence_score:.1f}",
                "priority": "medium" if confidence_score > 0.5 else "low",
                "timestamp": datetime.now().isoformat(),
                "action": "review_analysis",
                "asset_specific": False
            }
        ]
    
    def _generate_intelligent_recommendations(self, context: Dict, hypothesis: str,
                                            synthesis: str, research_data: Dict, 
                                            confidence_score: float) -> str:
        """Generate specific recommendations using context intelligence"""
        
        if not context:
            return self._generate_generic_recommendations(hypothesis, confidence_score)
        
        asset_info = context.get("asset_info", {})
        hypothesis_details = context.get("hypothesis_details", {})
        research_guidance = context.get("research_guidance", {})
        risk_analysis = context.get("risk_analysis", {})
        
        prompt = f"""
        Generate specific, actionable investment recommendations for this hypothesis:
        
        HYPOTHESIS: {hypothesis}
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        - Market: {asset_info.get("market", "Unknown")}
        
        HYPOTHESIS PARAMETERS:
        - Direction: {hypothesis_details.get("direction", "Unknown")}
        - Target: {hypothesis_details.get("price_target", "Not specified")}
        - Timeframe: {hypothesis_details.get("timeframe", "Not specified")}
        - Confidence: {confidence_score:.2f}
        
        KEY METRICS TO MONITOR: {research_guidance.get("key_metrics", [])}
        EVENTS TO WATCH: {research_guidance.get("monitoring_events", [])}
        PRIMARY RISKS: {risk_analysis.get("primary_risks", [])}
        
        SYNTHESIS SUMMARY: {synthesis[:500]}...
        
        Provide specific, actionable recommendations including:
        
        1. **Entry Strategy**: Specific entry criteria and timing for this asset type
        2. **Position Sizing**: Appropriate position size based on confidence level and risk
        3. **Risk Management**: Stop-loss levels and risk controls specific to this asset
        4. **Monitoring Plan**: Key metrics and events to track for this specific asset
        5. **Exit Strategy**: Profit-taking levels and exit criteria
        6. **Timeline**: Specific milestones and reassessment points
        7. **Asset-Specific Considerations**: Unique factors for this asset type and market
        
        Make all recommendations:
        - Specific to this asset and its characteristics
        - Actionable with clear criteria and levels
        - Appropriate for the confidence level and timeframe
        - Realistic given current market conditions
        - Tailored to this asset type's typical behavior
        
        Avoid generic advice - focus on this specific investment opportunity.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️  Intelligent recommendation generation failed: {str(e)}")
            return self._generate_fallback_recommendations(context, hypothesis, confidence_score)
    
    def _generate_fallback_recommendations(self, context: Dict, hypothesis: str, confidence_score: float) -> str:
        """Generate intelligent fallback recommendations using context"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        asset_type = asset_info.get("asset_type", "unknown")
        primary_symbol = asset_info.get("primary_symbol", "N/A")
        
        recommendations = [
            f"Investment Recommendations for {asset_name} ({primary_symbol}):",
            "",
            f"Hypothesis: {hypothesis}",
            f"Confidence Level: {confidence_score:.2f}",
            "",
            "Recommended Actions:"
        ]
        
        if confidence_score > 0.7:
            recommendations.extend([
                f"1. HIGH CONFIDENCE - Consider initiating position in {asset_name}",
                f"2. Position Size: Standard allocation appropriate for {asset_type} investments",
                f"3. Entry: Begin position building on current analysis",
                f"4. Stop Loss: Set at 10-15% below entry for {asset_type} assets"
            ])
        elif confidence_score > 0.5:
            recommendations.extend([
                f"1. MEDIUM CONFIDENCE - Wait for additional confirmation signals",
                f"2. Position Size: Reduced allocation until stronger signals emerge",
                f"3. Entry: Monitor for technical or fundamental confirmations",
                f"4. Stop Loss: Tight stops appropriate given uncertainty"
            ])
        else:
            recommendations.extend([
                f"1. LOW CONFIDENCE - Avoid position or wait for better setup",
                f"2. Position Size: Minimal or no allocation recommended",
                f"3. Entry: Significant improvement in thesis required",
                f"4. Alternative: Consider related opportunities with higher confidence"
            ])
        
        recommendations.extend([
            "",
            f"Monitoring Requirements:",
            f"- Track {asset_name} price action and volume patterns",
            f"- Monitor sector developments and competitive landscape",
            f"- Watch for asset-specific news and announcements",
            f"- Reassess thesis monthly or on significant developments",
            "",
            f"Risk Management for {asset_type.title()} Assets:",
            f"- Diversify across multiple positions to reduce single-asset risk",
            f"- Set position limits appropriate for {asset_type} volatility",
            f"- Monitor correlation with broader market conditions",
            f"- Have exit strategy ready for both profit-taking and loss-cutting"
        ])
        
        return "\n".join(recommendations)
    
    def _generate_generic_recommendations(self, hypothesis: str, confidence_score: float) -> str:
        """Generate generic recommendations when context is unavailable"""
        
        generic_recs = [
            f"Investment Analysis Summary:",
            f"Hypothesis: {hypothesis}",
            f"Confidence Level: {confidence_score:.2f}",
            "",
            "General Recommendations:",
        ]
        
        if confidence_score > 0.6:
            generic_recs.extend([
                "1. Consider opportunity with appropriate risk management",
                "2. Use standard position sizing for this confidence level",
                "3. Implement stop-loss and profit-taking levels",
                "4. Monitor key market developments"
            ])
        else:
            generic_recs.extend([
                "1. Exercise caution given lower confidence signals",
                "2. Consider reduced position size or waiting for better setup",
                "3. Implement tight risk controls if proceeding",
                "4. Monitor for improvement in thesis strength"
            ])
        
        generic_recs.extend([
            "",
            "Risk Management:",
            "- Diversify investments appropriately",
            "- Set clear entry and exit criteria", 
            "- Monitor market conditions regularly",
            "- Reassess thesis based on new information"
        ])
        
        return "\n".join(generic_recs)
    
    def _parse_alerts(self, text):
        """Parse alerts from response text - legacy method for compatibility"""
        alerts = []
        lines = text.split('\n')
        
        alert_id = 1
        for line in lines:
            if any(keyword in line.lower() for keyword in ['alert:', 'watch:', 'trigger:', 'recommendation:']):
                alerts.append({
                    "id": alert_id,
                    "type": "parsed_alert",
                    "message": line.strip(),
                    "timestamp": datetime.now().isoformat(),
                    "priority": "medium",
                    "asset_specific": False
                })
                alert_id += 1
        
        return alerts

def create():
    """Create and return an intelligent alert agent instance"""
    return AlertAgent()

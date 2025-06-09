# app/agents/synthesis_agent/agent.py - Intelligent, context-driven synthesis
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import re
from typing import Dict, Any, List

class SynthesisAgent:
    """Intelligent Synthesis Agent using context - no hardcoded patterns"""
    
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
        """Synthesize using intelligent context analysis - no hardcoded asset detection"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("processed_hypothesis", "")
        research_data = input_data.get("research_data", {})
        contradictions = input_data.get("contradictions", [])
        context = input_data.get("context", {})
        
        print(f"🔬 Starting intelligent synthesis for: {hypothesis}")
        
        # Log context usage
        if context:
            self._log_context_usage(context)
        
        # Generate context-aware confirmations
        confirmations = self._generate_context_aware_confirmations(context, hypothesis)
        
        # Create intelligent synthesis using context
        synthesis_result = self._create_intelligent_synthesis(
            hypothesis, research_data, contradictions, confirmations, context
        )
        
        return {
            "synthesis": synthesis_result["synthesis"],
            "assessment": synthesis_result["assessment"], 
            "status": "success",
            "confirmations": confirmations
        }
    
    def _log_context_usage(self, context: Dict) -> None:
        """Log how context is being used"""
        asset_info = context.get("asset_info", {})
        hypothesis_details = context.get("hypothesis_details", {})
        
        print(f"🔧 Using context: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('asset_type', 'Unknown')})")
        print(f"   🎯 Target: {hypothesis_details.get('price_target', 'Not specified')}")
        print(f"   ⏰ Timeframe: {hypothesis_details.get('timeframe', 'Not specified')}")
    
    def _generate_context_aware_confirmations(self, context: Dict, hypothesis: str) -> List[Dict]:
        """Generate confirmations using context intelligence - no hardcoded patterns"""
        
        if not context:
            return self._ai_generate_generic_confirmations(hypothesis)
        
        asset_info = context.get("asset_info", {})
        asset_type = asset_info.get("asset_type", "unknown")
        asset_name = asset_info.get("asset_name", "Unknown")
        sector = asset_info.get("sector", "Unknown")
        business_model = asset_info.get("business_model", "")
        
        print(f"   📈 Generating context-aware confirmations for {asset_type} in {sector}")
        
        # Generate confirmations using AI and context
        confirmations = self._ai_generate_context_confirmations(
            asset_info, asset_type, asset_name, sector, business_model, hypothesis
        )
        
        return confirmations[:3]  # Limit to 3 most relevant confirmations
    
    def _ai_generate_context_confirmations(self, asset_info: Dict, asset_type: str, 
                                         asset_name: str, sector: str, business_model: str, 
                                         hypothesis: str) -> List[Dict]:
        """Use AI to generate context-specific confirmations with database constraints"""
        
        prompt = f"""
        Generate specific confirmations that support this investment hypothesis using context:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET CONTEXT:
        - Asset: {asset_name}
        - Type: {asset_type}
        - Sector: {sector}
        - Business Model: {business_model}
        
        CRITICAL CONSTRAINTS - Each confirmation must have:
        - Quote: Maximum 400 characters (keep concise!)
        - Reason: Maximum 400 characters (keep concise!)
        - Source: Maximum 40 characters (e.g., "Market Analysis")
        - Strength: ONLY "Strong", "Medium", or "Weak"
        
        Generate 3 specific confirmations that:
        1. Are directly relevant to this asset type and sector
        2. Reference realistic positive factors for this specific asset
        3. Are concise and database-friendly (NO markdown, NO special formatting)
        
        Format each as exactly: quote|reason|source|strength
        
        Example:
        Services revenue growth drives Apple valuation higher|Recurring services provide stable margins and investor confidence|Earnings Analysis|Strong
        
        Keep everything under the character limits. Be specific but concise.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_context_confirmations_strict(response.text, asset_name)
        except Exception as e:
            print(f"❌ Context confirmation generation failed: {str(e)}")
            return self._generate_fallback_confirmations_strict(asset_type, asset_name, sector)

    def _parse_context_confirmations_strict(self, response_text: str, asset_name: str) -> List[Dict]:
        """Parse AI-generated confirmations with strict database constraints"""
        confirmations = []
        
        # Try structured format first
        lines = response_text.split('\n')
        
        for line in lines:
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
                if len(quote) > 20 and len(reason) > 10:
                    confirmations.append({
                        "quote": quote,
                        "reason": reason,
                        "source": source,
                        "strength": strength
                    })
        
        # Fallback parsing if structured format fails
        if not confirmations:
            sections = response_text.split('\n')
            for section in sections:
                section = section.strip()
                if len(section) > 30 and not section.startswith('#'):
                    # Create safe confirmation
                    quote = section[:300] + "..." if len(section) > 300 else section
                    confirmations.append({
                        "quote": quote,
                        "reason": f"This factor supports {asset_name} positive outlook.",
                        "source": "AI Analysis",
                        "strength": "Medium"
                    })
                    if len(confirmations) >= 3:
                        break
        
        return confirmations[:3]  # Limit to 3

    def _generate_fallback_confirmations_strict(self, asset_type: str, asset_name: str, sector: str) -> List[Dict]:
        """Generate intelligent fallback confirmations with strict database constraints"""
        
        fallback_confirmations = []
        
        if asset_type == "stock":
            fallback_confirmations.extend([
                {
                    "quote": f"{asset_name} operates in {sector} with strong market fundamentals.",
                    "reason": f"{sector} industry trends support {asset_name} business growth.",
                    "source": "Sector Analysis",
                    "strength": "Medium"
                },
                {
                    "quote": f"Institutional investment in {sector} companies continues growing.",
                    "reason": "Growing institutional interest provides capital and validation.",
                    "source": "Institutional Data",
                    "strength": "Medium"
                }
            ])
        
        elif asset_type in ["crypto", "cryptocurrency"]:
            fallback_confirmations.extend([
                {
                    "quote": f"{asset_name} benefits from increasing institutional adoption.",
                    "reason": "Institutional acceptance drives demand and legitimacy.",
                    "source": "Adoption Analysis",
                    "strength": "Strong"
                },
                {
                    "quote": f"Network effects of {asset_name} create value propositions.",
                    "reason": "Strong network effects support long-term appreciation.",
                    "source": "Technology Analysis",
                    "strength": "Medium"
                }
            ])
        
        else:
            # Generic but safe confirmations
            fallback_confirmations.extend([
                {
                    "quote": f"Market fundamentals support positive outlook for {asset_name}.",
                    "reason": f"Current conditions favor {asset_type} assets.",
                    "source": "Market Analysis",
                    "strength": "Medium"
                }
            ])
        
        return fallback_confirmations

    def _parse_context_confirmations(self, response_text: str, asset_name: str) -> List[Dict]:
      """Parse AI-generated confirmations"""
      confirmations = []
      
      # Try structured format first
      lines = response_text.split('\n')
      
      for line in lines:
          if '|' in line and len(line.split('|')) >= 4:
              parts = line.split('|')
              confirmations.append({
                  "quote": parts[0].strip(),
                  "reason": parts[1].strip(),
                  "source": parts[2].strip(),
                  "strength": parts[3].strip()
              })
      
      # Fallback parsing
      if not confirmations:
          sections = response_text.split('\n')
          for section in sections:
              section = section.strip()
              if len(section) > 30 and not section.startswith('#'):
                  confirmations.append({
                      "quote": section,
                      "reason": f"This factor supports the positive outlook for {asset_name}.",
                      "source": "AI Context Analysis",
                      "strength": "Medium"
                  })
      
      return confirmations
    
    def _generate_fallback_confirmations(self, asset_type: str, asset_name: str, sector: str) -> List[Dict]:
        """Generate intelligent fallback confirmations based on context"""
        
        fallback_confirmations = []
        
        if asset_type == "stock":
            fallback_confirmations.extend([
                {
                    "quote": f"{asset_name} operates in the {sector} sector with strong market fundamentals and growth potential.",
                    "reason": f"The {sector} industry shows positive trends that could support {asset_name}'s business growth.",
                    "source": "Sector Analysis",
                    "strength": "Medium"
                },
                {
                    "quote": f"Institutional investment interest in {sector} companies like {asset_name} continues to grow.",
                    "reason": "Growing institutional interest provides capital flow support and market validation.",
                    "source": "Institutional Analysis",
                    "strength": "Medium"
                }
            ])
        
        elif asset_type in ["crypto", "cryptocurrency"]:
            fallback_confirmations.extend([
                {
                    "quote": f"{asset_name} benefits from increasing institutional adoption and mainstream acceptance of cryptocurrency assets.",
                    "reason": "Growing institutional acceptance drives demand and legitimacy for established cryptocurrencies.",
                    "source": "Adoption Analysis",
                    "strength": "Strong"
                },
                {
                    "quote": f"The underlying blockchain technology and network effects of {asset_name} create long-term value propositions.",
                    "reason": "Strong network effects and technological advantages support long-term price appreciation.",
                    "source": "Technology Analysis",
                    "strength": "Medium"
                }
            ])
        
        elif asset_type == "commodity":
            fallback_confirmations.extend([
                {
                    "quote": f"Global economic growth and industrial demand continue to support {asset_name} fundamentals.",
                    "reason": "Increasing industrial and economic activity drives demand for commodity assets.",
                    "source": "Demand Analysis",
                    "strength": "Medium"
                }
            ])
        
        else:
            # Generic but contextual confirmations
            fallback_confirmations.extend([
                {
                    "quote": f"Market fundamentals and sector dynamics support positive outlook for {asset_name}.",
                    "reason": f"Current market conditions create favorable environment for {asset_type} assets.",
                    "source": "Market Analysis",
                    "strength": "Medium"
                }
            ])
        
        return fallback_confirmations
    
    def _ai_generate_generic_confirmations(self, hypothesis: str) -> List[Dict]:
        """AI fallback when no context is available"""
        prompt = f"""
        Generate confirmations that support this hypothesis:
        
        "{hypothesis}"
        
        Provide 2-3 realistic factors that could support this prediction.
        Format each as: quote|reason|source|strength
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_context_confirmations(response.text, "the asset")
        except:
            return [{
                "quote": "Market fundamentals support the positive outlook for this investment.",
                "reason": "Current market conditions create opportunities for price appreciation.",
                "source": "Market Analysis",
                "strength": "Medium"
            }]
    
    def _create_intelligent_synthesis(self, hypothesis: str, research_data: Dict, 
                                    contradictions: List, confirmations: List, context: Dict) -> Dict:
        """Create synthesis using intelligent context analysis"""
        
        try:
            synthesis_text = self._generate_context_aware_synthesis(
                hypothesis, research_data, contradictions, confirmations, context
            )
            
            # Parse synthesis for assessment
            assessment = self._parse_intelligent_synthesis(synthesis_text, contradictions, confirmations, context)
            
            return {
                "synthesis": synthesis_text,
                "assessment": assessment
            }
            
        except Exception as e:
            print(f"Synthesis generation error: {str(e)}")
            return self._generate_intelligent_fallback_synthesis(context, hypothesis, contradictions, confirmations)
    
    def _generate_context_aware_synthesis(self, hypothesis: str, research_data: Dict, 
                                        contradictions: List, confirmations: List, context: Dict) -> str:
        """Generate synthesis using context intelligence"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        hypothesis_details = context.get("hypothesis_details", {}) if context else {}
        risk_analysis = context.get("risk_analysis", {}) if context else {}
        
        prompt = f"""
        Synthesize a comprehensive investment analysis for this specific hypothesis:
        
        HYPOTHESIS: {hypothesis}
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        - Market: {asset_info.get("market", "Unknown")}
        - Business Model: {asset_info.get("business_model", "Unknown")}
        
        HYPOTHESIS DETAILS:
        - Direction: {hypothesis_details.get("direction", "Unknown")}
        - Target: {hypothesis_details.get("price_target", "Not specified")}
        - Timeframe: {hypothesis_details.get("timeframe", "Not specified")}
        - Confidence Level: {hypothesis_details.get("confidence_level", "Unknown")}
        
        RESEARCH FINDINGS: {json.dumps(research_data, indent=2)[:1000]}...
        
        CONTRADICTIONS ({len(contradictions)}): {json.dumps(contradictions, indent=2)[:1000]}...
        
        CONFIRMATIONS ({len(confirmations)}): {json.dumps(confirmations, indent=2)[:1000]}...
        
        KEY RISKS: {risk_analysis.get("primary_risks", [])}
        
        Provide a balanced, intelligent synthesis that considers:
        
        1. **Asset-Specific Analysis**: How do the findings relate specifically to this asset type and sector?
        
        2. **Evidence Evaluation**: What is the weight of supporting vs. contradicting evidence?
        
        3. **Risk-Reward Assessment**: What are the specific risks and rewards for this asset?
        
        4. **Confidence Analysis**: Based on the evidence quality, what confidence level is justified?
        
        5. **Asset-Specific Recommendations**: What specific actions are appropriate for this asset type?
        
        6. **Monitoring Strategy**: What asset-specific factors should be monitored?
        
        7. **Timeline Assessment**: How realistic is the timeframe given this asset's characteristics?
        
        Structure your response with clear sections and provide:
        - Specific confidence score (0.0-1.0) with detailed reasoning
        - Asset-specific risk factors and mitigation strategies
        - Tailored recommendations for this particular investment
        - Key monitoring points specific to this asset and sector
        
        Be specific to this asset and avoid generic market commentary.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️  Context synthesis generation failed: {str(e)}")
            return self._generate_basic_synthesis(asset_info, hypothesis, contradictions, confirmations)
    
    def _generate_basic_synthesis(self, asset_info: Dict, hypothesis: str, 
                                contradictions: List, confirmations: List) -> str:
        """Generate basic synthesis when AI fails"""
        asset_name = asset_info.get("asset_name", "the asset")
        asset_type = asset_info.get("asset_type", "unknown")
        
        analysis_parts = [
            f"Investment Analysis for {asset_name}:",
            f"Asset Type: {asset_type}",
            f"Hypothesis: {hypothesis}",
            "",
            f"Evidence Summary:",
            f"- Supporting factors: {len(confirmations)} confirmations identified",
            f"- Challenge factors: {len(contradictions)} contradictions identified",
            "",
        ]
        
        # Assess balance
        strong_contradictions = sum(1 for c in contradictions if c.get("strength", "").lower() == "strong")
        strong_confirmations = sum(1 for c in confirmations if c.get("strength", "").lower() == "strong")
        
        if strong_confirmations > strong_contradictions:
            analysis_parts.append(f"Assessment: The evidence appears to favor the positive outlook for {asset_name}.")
            confidence = 0.7
        elif strong_contradictions > strong_confirmations:
            analysis_parts.append(f"Assessment: Significant challenges identified for {asset_name} require careful consideration.")
            confidence = 0.3
        else:
            analysis_parts.append(f"Assessment: Mixed evidence requires balanced approach for {asset_name}.")
            confidence = 0.5
        
        analysis_parts.extend([
            "",
            f"Confidence Score: {confidence:.1f}",
            f"Recommendation: {'Consider position' if confidence > 0.6 else 'Exercise caution' if confidence < 0.4 else 'Monitor closely'}"
        ])
        
        return "\n".join(analysis_parts)
    
    def _parse_intelligent_synthesis(self, synthesis_text: str, contradictions: List, 
                                   confirmations: List, context: Dict) -> Dict:
        """Parse synthesis and extract intelligent assessment"""
        
        # Extract confidence score
        confidence_patterns = [
            r'confidence[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)[%\s]*confidence',
            r'score[:\s]+(\d+\.?\d*)'
        ]
        
        confidence = 0.5  # Default
        
        for pattern in confidence_patterns:
            match = re.search(pattern, synthesis_text.lower())
            if match:
                extracted_confidence = float(match.group(1))
                # Convert percentage to decimal if needed
                if extracted_confidence > 1.0:
                    extracted_confidence = extracted_confidence / 100.0
                confidence = max(0.0, min(1.0, extracted_confidence))
                break
        
        # Intelligent confidence adjustment based on evidence
        evidence_adjustment = self._calculate_evidence_based_confidence(contradictions, confirmations, context)
        final_confidence = (confidence + evidence_adjustment) / 2
        
        # Generate summary
        asset_name = context.get("asset_info", {}).get("asset_name", "the asset") if context else "the asset"
        summary = synthesis_text[:300] + "..." if len(synthesis_text) > 300 else synthesis_text
        
        return {
            "confidence": final_confidence,
            "summary": summary,
            "evidence_balance": {
                "confirmations": len(confirmations),
                "contradictions": len(contradictions),
                "net_sentiment": len(confirmations) - len(contradictions)
            },
            "asset_context": asset_name
        }
    
    def _calculate_evidence_based_confidence(self, contradictions: List, confirmations: List, context: Dict) -> float:
        """Calculate confidence based on evidence quality and context"""
        
        # Count strong evidence
        strong_contradictions = sum(1 for c in contradictions if c.get("strength", "").lower() == "strong")
        strong_confirmations = sum(1 for c in confirmations if c.get("strength", "").lower() == "strong")
        
        # Evidence-based scoring
        evidence_score = 0.5  # Neutral baseline
        
        # Adjust based on strong evidence
        if strong_confirmations > strong_contradictions:
            evidence_score += 0.2 * (strong_confirmations - strong_contradictions)
        elif strong_contradictions > strong_confirmations:
            evidence_score -= 0.2 * (strong_contradictions - strong_confirmations)
        
        # Context quality adjustment
        if context and context.get("asset_info", {}).get("asset_type") != "unknown":
            evidence_score += 0.1  # Bonus for good context
        
        return max(0.0, min(1.0, evidence_score))
    
    def _generate_intelligent_fallback_synthesis(self, context: Dict, hypothesis: str, 
                                               contradictions: List, confirmations: List) -> Dict:
        """Generate intelligent fallback when synthesis fails"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        asset_type = asset_info.get("asset_type", "unknown")
        
        fallback_text = f"""
        Investment Analysis Summary for {asset_name}:
        
        Hypothesis under review: {hypothesis}
        
        Evidence Assessment:
        - Supporting factors identified: {len(confirmations)}
        - Challenge factors identified: {len(contradictions)}
        - Asset type: {asset_type}
        
        The analysis reveals a {'positive' if len(confirmations) > len(contradictions) else 'cautious' if len(contradictions) > len(confirmations) else 'balanced'} 
        outlook based on the available evidence for {asset_name}.
        
        Recommendation: {'Consider opportunity' if len(confirmations) > len(contradictions) else 'Exercise caution' if len(contradictions) > len(confirmations) else 'Monitor developments'} 
        with appropriate risk management for this {asset_type} investment.
        """
        
        fallback_confidence = self._calculate_evidence_based_confidence(contradictions, confirmations, context)
        
        return {
            "synthesis": fallback_text.strip(),
            "assessment": {
                "confidence": fallback_confidence,
                "summary": f"Intelligent fallback analysis for {asset_name} with {len(confirmations)} confirmations and {len(contradictions)} contradictions."
            }
        }

def create():
    """Create and return an intelligent synthesis agent instance"""
    return SynthesisAgent()
    


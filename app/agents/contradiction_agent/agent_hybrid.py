# app/agents/contradiction_agent/agent_hybrid.py
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import re
import asyncio
from typing import Dict, Any, List

class HybridContradictionAgent:
    """Enhanced Contradiction Agent that uses RAG database to find opposing evidence"""
    
    def __init__(self):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            # Initialize hybrid RAG service for contradiction research
            self._initialize_hybrid_service()
            
        except Exception as e:
            print(f"Error initializing Hybrid Contradiction Agent: {e}")
            self.model = None
            self.hybrid_service = None
    
    def _initialize_hybrid_service(self):
        """Initialize the hybrid RAG service"""
        try:
            from app.services.hybrid_rag_service import get_hybrid_rag_service
            self.hybrid_service = get_hybrid_rag_service()
            print("✅ Hybrid RAG service connected to Contradiction Agent")
        except Exception as e:
            print(f"⚠️  Hybrid RAG service initialization failed: {str(e)}")
            self.hybrid_service = None
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Find contradictions using both RAG research and AI analysis"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        research_data = input_data.get("research_data", {})
        
        print(f"🎯 Finding contradictions for: {processed_hypothesis}")
        
        try:
            # Step 1: Search for contradictory evidence in RAG database
            contradiction_evidence = []
            if self.hybrid_service:
                contradiction_evidence = asyncio.run(
                    self._search_contradictory_evidence(processed_hypothesis)
                )
            
            # Step 2: Generate AI-based contradictions
            ai_contradictions = self._generate_ai_contradictions(
                processed_hypothesis, research_data, contradiction_evidence
            )
            
            # Step 3: Merge and rank contradictions
            final_contradictions = self._merge_and_rank_contradictions(
                ai_contradictions, contradiction_evidence
            )
            
            return {
                "contradictions": final_contradictions,
                "analysis": self._create_contradiction_analysis(final_contradictions),
                "evidence_sources": {
                    "rag_database": len(contradiction_evidence),
                    "ai_generated": len(ai_contradictions),
                    "total": len(final_contradictions)
                },
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Contradiction analysis failed: {str(e)}")
            return {
                "contradictions": self._get_fallback_contradictions(processed_hypothesis),
                "analysis": "Contradiction analysis encountered errors, using fallback analysis.",
                "evidence_sources": {"rag_database": 0, "ai_generated": 0, "total": 0},
                "status": "error_fallback"
            }
    
    async def _search_contradictory_evidence(self, hypothesis: str) -> List[Dict[str, Any]]:
        """Search RAG database for evidence that contradicts the hypothesis"""
        if not self.hybrid_service:
            return []
        
        print("🔍 Searching RAG database for contradictory evidence...")
        
        # Create contradiction-focused search queries
        contradiction_queries = self._create_contradiction_queries(hypothesis)
        
        all_evidence = []
        
        for query in contradiction_queries:
            try:
                # Search RAG database
                result = await self.hybrid_service._rag_search(query, limit=5)
                
                if result.get("historical_insights"):
                    for insight in result["historical_insights"]:
                        # Filter for potentially contradictory content
                        if self._is_potentially_contradictory(insight["full_content"], hypothesis):
                            all_evidence.append({
                                "quote": insight["content_preview"],
                                "source": f"{insight['source']} - {insight['instrument']}",
                                "date": insight["date"],
                                "similarity": insight["similarity"],
                                "strength": self._assess_contradiction_strength(insight["full_content"], hypothesis),
                                "evidence_type": "historical_data"
                            })
                            
            except Exception as e:
                print(f"   ⚠️  RAG search failed for query '{query}': {str(e)}")
                continue
        
        # Remove duplicates and sort by relevance
        unique_evidence = self._deduplicate_evidence(all_evidence)
        print(f"   Found {len(unique_evidence)} pieces of contradictory evidence")
        
        return unique_evidence[:5]  # Limit to top 5 pieces of evidence
    
    def _create_contradiction_queries(self, hypothesis: str) -> List[str]:
        """Create search queries designed to find contradictory evidence"""
        base_terms = self._extract_key_terms(hypothesis)
        
        contradiction_queries = []
        
        # Add opposing terms and scenarios
        for term in base_terms:
            contradiction_queries.extend([
                f"{term} decline fall drop",
                f"{term} risk failure challenge",
                f"{term} bearish negative outlook",
                f"{term} overvalued bubble crash"
            ])
        
        # Add general market contradiction terms
        if "bitcoin" in hypothesis.lower() or "crypto" in hypothesis.lower():
            contradiction_queries.extend([
                "bitcoin regulation ban government",
                "cryptocurrency crash volatility risk",
                "bitcoin energy concerns environmental",
                "crypto market manipulation"
            ])
        elif "oil" in hypothesis.lower():
            contradiction_queries.extend([
                "oil demand peak electric vehicles",
                "renewable energy transition",
                "oil supply increase production",
                "recession oil demand decline"
            ])
        else:
            contradiction_queries.extend([
                "market recession economic downturn",
                "inflation interest rates rising",
                "geopolitical uncertainty market risk"
            ])
        
        return contradiction_queries[:8]  # Limit to avoid excessive API calls
    
    def _extract_key_terms(self, hypothesis: str) -> List[str]:
        """Extract key financial terms from hypothesis"""
        import re
        
        # Extract instruments and key terms
        terms = []
        
        # Cryptocurrency terms
        if re.search(r'bitcoin|btc', hypothesis.lower()):
            terms.append("bitcoin")
        if re.search(r'ethereum|eth', hypothesis.lower()):
            terms.append("ethereum")
        
        # Other financial terms
        financial_terms = re.findall(r'\b(?:oil|gold|stock|market|price|inflation|interest)\b', hypothesis.lower())
        terms.extend(financial_terms)
        
        # Stock symbols
        stock_symbols = re.findall(r'\$?([A-Z]{2,5})', hypothesis)
        terms.extend(stock_symbols)
        
        return list(set(terms))[:3]  # Limit to 3 most relevant terms
    
    def _is_potentially_contradictory(self, content: str, hypothesis: str) -> bool:
        """Assess if content potentially contradicts the hypothesis"""
        # Look for negative sentiment indicators
        negative_indicators = [
            'decline', 'fall', 'drop', 'crash', 'risk', 'challenge', 'difficult',
            'unlikely', 'bearish', 'negative', 'concern', 'problem', 'issue',
            'overvalued', 'bubble', 'correction', 'downturn'
        ]
        
        content_lower = content.lower()
        
        # Count negative indicators
        negative_count = sum(1 for indicator in negative_indicators if indicator in content_lower)
        
        # If hypothesis is bullish and content has negative indicators, it's potentially contradictory
        if any(bullish_term in hypothesis.lower() for bullish_term in ['will reach', 'will rise', 'will increase', 'bullish']):
            return negative_count >= 2
        
        # General contradiction check
        return negative_count >= 3
    
    def _assess_contradiction_strength(self, content: str, hypothesis: str) -> str:
        """Assess the strength of contradiction"""
        strong_indicators = ['impossible', 'never', 'cannot', 'will not', 'highly unlikely']
        medium_indicators = ['difficult', 'challenging', 'unlikely', 'risky']
        
        content_lower = content.lower()
        
        if any(indicator in content_lower for indicator in strong_indicators):
            return "Strong"
        elif any(indicator in content_lower for indicator in medium_indicators):
            return "Medium"
        else:
            return "Weak"
    
    def _generate_ai_contradictions(self, hypothesis: str, research_data: Dict, evidence: List[Dict]) -> List[Dict[str, Any]]:
        """Generate AI-based contradictions"""
        
        # Determine hypothesis type for specialized prompts
        is_crypto = 'bitcoin' in hypothesis.lower() or 'btc' in hypothesis.lower()
        is_oil = 'oil' in hypothesis.lower()
        
        if is_crypto:
            prompt = self._create_crypto_contradiction_prompt(hypothesis, research_data, evidence)
        elif is_oil:
            prompt = self._create_oil_contradiction_prompt(hypothesis, research_data, evidence)
        else:
            prompt = self._create_general_contradiction_prompt(hypothesis, research_data, evidence)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_ai_contradictions(response.text, is_crypto)
        except Exception as e:
            print(f"❌ AI contradiction generation failed: {str(e)}")
            return self._get_fallback_contradictions(hypothesis)
    
    def _create_crypto_contradiction_prompt(self, hypothesis: str, research_data: Dict, evidence: List[Dict]) -> str:
        """Create specialized prompt for cryptocurrency contradictions"""
        return f"""
        Challenge this Bitcoin hypothesis with specific contradictions: "{hypothesis}"
        
        Research Data: {json.dumps(research_data, indent=2)[:800]}...
        
        Historical Evidence: {json.dumps(evidence, indent=2)[:600]}...
        
        Provide 4-5 specific contradictions focusing on:
        1. Regulatory risks and government interventions
        2. Technical analysis suggesting price resistance
        3. Macroeconomic factors limiting crypto growth
        4. Historical patterns of failed price predictions
        5. Market sentiment and institutional concerns
        
        Format each as: quote|reason|source|strength
        Be specific with dates, numbers, and expert opinions where possible.
        """
    
    def _create_oil_contradiction_prompt(self, hypothesis: str, research_data: Dict, evidence: List[Dict]) -> str:
        """Create specialized prompt for oil price contradictions"""
        return f"""
        Challenge this oil market hypothesis: "{hypothesis}"
        
        Research Data: {json.dumps(research_data, indent=2)[:800]}...
        
        Historical Evidence: {json.dumps(evidence, indent=2)[:600]}...
        
        Provide 4-5 specific contradictions focusing on:
        1. Supply increases from major producers
        2. Demand decline due to economic factors
        3. Energy transition and renewable adoption
        4. Geopolitical factors affecting oil markets
        5. Historical price volatility patterns
        
        Format each as: quote|reason|source|strength
        """
    
    def _create_general_contradiction_prompt(self, hypothesis: str, research_data: Dict, evidence: List[Dict]) -> str:
        """Create general contradiction prompt"""
        return f"""
        Challenge this hypothesis: "{hypothesis}"
        
        Research Data: {json.dumps(research_data, indent=2)[:800]}...
        
        Historical Evidence: {json.dumps(evidence, indent=2)[:600]}...
        
        Provide 4-5 specific contradictions focusing on:
        1. Market risks and economic headwinds
        2. Technical analysis contradicting the thesis
        3. Historical precedents of similar failed predictions
        4. Alternative market scenarios
        5. Fundamental analysis challenges
        
        Format each as: quote|reason|source|strength
        """
    
    def _parse_ai_contradictions(self, response_text: str, is_crypto: bool = False) -> List[Dict[str, Any]]:
        """Parse AI-generated contradictions"""
        contradictions = []
        
        # Try to parse structured format first
        lines = response_text.split('\n')
        
        for line in lines:
            if '|' in line and len(line.split('|')) >= 4:
                parts = line.split('|')
                contradictions.append({
                    "quote": parts[0].strip(),
                    "reason": parts[1].strip(),
                    "source": parts[2].strip(),
                    "strength": parts[3].strip(),
                    "evidence_type": "ai_generated"
                })
        
        # If structured parsing failed, use regex parsing
        if not contradictions:
            sections = re.split(r'\n\d+[\.\)]\s+', '\n' + response_text)
            
            for section in sections[1:]:
                if len(section.strip()) < 20:
                    continue
                
                contradiction = {
                    "quote": section.strip()[:200] + ("..." if len(section) > 200 else ""),
                    "reason": "AI analysis identifies this challenge to the hypothesis",
                    "source": "AI Analysis",
                    "strength": "Medium",
                    "evidence_type": "ai_generated"
                }
                contradictions.append(contradiction)
        
        return contradictions[:5]  # Limit to 5 contradictions
    
    def _merge_and_rank_contradictions(self, ai_contradictions: List[Dict], evidence: List[Dict]) -> List[Dict[str, Any]]:
        """Merge and rank contradictions by strength and relevance"""
        all_contradictions = []
        
        # Add evidence-based contradictions (higher priority)
        for item in evidence:
            item["priority"] = self._calculate_priority(item, source_type="evidence")
            all_contradictions.append(item)
        
        # Add AI-generated contradictions
        for item in ai_contradictions:
            item["priority"] = self._calculate_priority(item, source_type="ai")
            all_contradictions.append(item)
        
        # Sort by priority (higher is better)
        all_contradictions.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        # Remove duplicates based on content similarity
        final_contradictions = self._deduplicate_evidence(all_contradictions)
        
        return final_contradictions[:6]  # Return top 6 contradictions
    
    def _calculate_priority(self, contradiction: Dict, source_type: str) -> float:
        """Calculate priority score for contradiction"""
        priority = 0.0
        
        # Base priority by source type
        if source_type == "evidence":
            priority += 0.6  # Historical evidence gets higher base score
        else:
            priority += 0.4  # AI-generated gets lower base score
        
        # Strength modifier
        strength = contradiction.get("strength", "Medium").lower()
        if strength == "strong":
            priority += 0.3
        elif strength == "medium":
            priority += 0.2
        else:
            priority += 0.1
        
        # Similarity/relevance modifier (for evidence)
        if "similarity" in contradiction:
            priority += min(contradiction["similarity"] * 0.2, 0.2)
        
        return priority
    
    def _deduplicate_evidence(self, evidence_list: List[Dict]) -> List[Dict]:
        """Remove duplicate evidence based on content similarity"""
        if not evidence_list:
            return []
        
        unique_evidence = []
        
        for item in evidence_list:
            is_duplicate = False
            item_text = item.get("quote", "").lower()
            
            for existing in unique_evidence:
                existing_text = existing.get("quote", "").lower()
                
                # Simple similarity check
                if len(item_text) > 20 and len(existing_text) > 20:
                    # Check for significant overlap
                    words_item = set(item_text.split())
                    words_existing = set(existing_text.split())
                    
                    if len(words_item & words_existing) / len(words_item | words_existing) > 0.6:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_evidence.append(item)
        
        return unique_evidence
    
    def _create_contradiction_analysis(self, contradictions: List[Dict]) -> str:
        """Create summary analysis of contradictions"""
        if not contradictions:
            return "No significant contradictions identified."
        
        strong_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "strong")
        medium_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "medium")
        evidence_count = sum(1 for c in contradictions if c.get("evidence_type") == "historical_data")
        
        analysis = f"""
        Contradiction Analysis Summary:
        - Total contradictions identified: {len(contradictions)}
        - Strong contradictions: {strong_count}
        - Medium contradictions: {medium_count}
        - Based on historical evidence: {evidence_count}
        - AI-generated analysis: {len(contradictions) - evidence_count}
        
        The analysis reveals {'significant' if strong_count >= 2 else 'moderate' if strong_count >= 1 else 'limited'} 
        challenges to the hypothesis.
        """
        
        return analysis.strip()
    
    def _get_fallback_contradictions(self, hypothesis: str) -> List[Dict[str, Any]]:
        """Get fallback contradictions if all else fails"""
        if 'bitcoin' in hypothesis.lower() or 'btc' in hypothesis.lower():
            return [
                {
                    "quote": "Regulatory uncertainty continues to pose significant risks to Bitcoin adoption and price stability.",
                    "reason": "Government interventions could limit institutional adoption and retail accessibility.",
                    "source": "Regulatory Risk Analysis",
                    "strength": "Strong",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "Bitcoin's historical volatility shows 80-90% drawdowns are common, potentially preventing sustained price appreciation.",
                    "reason": "Extreme volatility patterns suggest difficulty maintaining high price levels.",
                    "source": "Technical Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                }
            ]
        
        return [
            {
                "quote": "Market conditions remain uncertain with potential for significant volatility.",
                "reason": "Economic uncertainty creates challenges for sustained price appreciation.",
                "source": "Market Analysis",
                "strength": "Medium",
                "evidence_type": "fallback"
            }
        ]

def create():
    """Create and return a hybrid contradiction agent instance"""
    return HybridContradictionAgent()

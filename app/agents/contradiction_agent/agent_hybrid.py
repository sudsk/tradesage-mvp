# app/agents/contradiction_agent/agent_hybrid.py
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import re
import asyncio
from typing import Dict, Any, List
import concurrent.futures
import threading

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
            
            # Initialize hybrid RAG service
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
        """Find contradictions using both RAG and AI analysis"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        research_data = input_data.get("research_data", {})
        
        print(f"🎯 Finding contradictions for: {processed_hypothesis}")

        # Extract context from input_data
        context = input_data.get("context", {})
        asset_info = context.get("asset_info", {})
        research_guidance = context.get("research_guidance", {})
        risk_analysis = context.get("risk_analysis", {})
        
        print(f"🔧 Using context: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('asset_type', 'Unknown')})")
        
        try:
            # Step 1: Search for contradictory evidence in RAG database
            contradiction_evidence = []
            if self.hybrid_service:
                # Run async code in a separate thread to avoid event loop conflicts
                contradiction_evidence = self._run_async_search(processed_hypothesis)
            
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
    
    def _run_async_search(self, hypothesis: str) -> List[Dict[str, Any]]:
        """Run async search in a thread pool to avoid event loop conflicts"""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we get here, we're in a running event loop
                # Use a thread pool executor to run the async code
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_search_in_new_loop, hypothesis)
                    return future.result(timeout=30)  # 30 second timeout
            except RuntimeError:
                # No running event loop, we can use asyncio.run()
                return asyncio.run(self._search_contradictory_evidence(hypothesis))
        except Exception as e:
            print(f"⚠️  RAG search failed: {str(e)}")
            return []
    
    def _run_search_in_new_loop(self, hypothesis: str) -> List[Dict[str, Any]]:
        """Run search in a completely new event loop"""
        try:
            # Create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._search_contradictory_evidence(hypothesis))
            finally:
                new_loop.close()
        except Exception as e:
            print(f"⚠️  New loop search failed: {str(e)}")
            return []
    
    def _clean_rag_content(self, raw_content: str) -> str:
        """Clean content from RAG database to make it suitable for contradictions"""
        if not raw_content:
            return ""
        
        # Remove image markdown and URLs
        content = re.sub(r'!\[.*?\]\(.*?\)', '', raw_content)
        content = re.sub(r'https?://[^\s\)]+', '', content)
        
        # Remove empty markdown links
        content = re.sub(r'\[\]\([^\)]*\)', '', content)
        
        # Remove excessive whitespace
        content = ' '.join(content.split())
        
        # Extract meaningful text from headlines/titles
        # Look for actual content after cleaning
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
        
        if sentences:
            # Take the first meaningful sentence
            clean_sentence = sentences[0]
            # Remove any remaining markdown artifacts
            clean_sentence = re.sub(r'[\*#]+', '', clean_sentence)
            return clean_sentence.strip()
        
        return ""
    
    def _is_relevant_to_hypothesis(self, content: str, hypothesis: str) -> bool:
        """Check if content is relevant to the current hypothesis"""
        if not content or not hypothesis:
            return False
        
        hypothesis_lower = hypothesis.lower()
        content_lower = content.lower()
        
        # Extract key terms from hypothesis
        hypothesis_terms = set()
        
        # Company names and tickers
        if 'apple' in hypothesis_lower or 'aapl' in hypothesis_lower:
            hypothesis_terms.update(['apple', 'aapl', 'iphone', 'ios', 'mac'])
        elif 'microsoft' in hypothesis_lower or 'msft' in hypothesis_lower:
            hypothesis_terms.update(['microsoft', 'msft', 'windows', 'azure'])
        elif 'bitcoin' in hypothesis_lower or 'btc' in hypothesis_lower:
            hypothesis_terms.update(['bitcoin', 'btc'])
        elif 'oil' in hypothesis_lower:
            hypothesis_terms.update(['oil', 'crude', 'petroleum', 'energy'])
        
        # Check if any hypothesis terms appear in content
        for term in hypothesis_terms:
            if term in content_lower:
                return True
        
        # If no specific terms match, reject crypto content for non-crypto hypothesis
        crypto_terms = ['bitcoin', 'ethereum', 'crypto', 'defi', 'nft', 'blockchain']
        is_crypto_content = any(term in content_lower for term in crypto_terms)
        is_crypto_hypothesis = any(term in hypothesis_lower for term in ['bitcoin', 'crypto', 'ethereum'])
        
        if is_crypto_content and not is_crypto_hypothesis:
            return False
        
        return True
    
    def _generate_contextual_contradiction(self, content: str, hypothesis: str) -> dict:
        """Generate a contextual contradiction from cleaned content"""
        
        # Extract the main point from the content
        clean_content = self._clean_rag_content(content)
        
        if not clean_content or not self._is_relevant_to_hypothesis(clean_content, hypothesis):
            return None
        
        # Create a contradiction based on the cleaned content
        if len(clean_content) > 200:
            quote = clean_content[:200] + "..."
        else:
            quote = clean_content
        
        # Generate contextual reason based on hypothesis
        if 'apple' in hypothesis.lower() or 'aapl' in hypothesis.lower():
            reason = "This development could impact Apple's market position and limit its ability to reach the projected price target."
        elif 'bitcoin' in hypothesis.lower() or 'btc' in hypothesis.lower():
            reason = "This market development could create headwinds for Bitcoin's price appreciation to the target level."
        elif 'oil' in hypothesis.lower():
            reason = "This factor could influence oil market dynamics and prevent the projected price increase."
        else:
            reason = "This market development could challenge the underlying assumptions of the hypothesis."
        
        return {
            "quote": quote,
            "reason": reason,
            "source": "Market Intelligence",
            "strength": "Medium",
            "evidence_type": "rag_processed"
        }

    async def _search_contradictory_evidence(self, hypothesis: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the historical RAG database"""
        if not self.hybrid_service:
            return []
        
        print("📚 Searching RAG database for contradictory evidence...")
        
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
                            # Clean and process the content
                            cleaned_contradiction = self._generate_contextual_contradiction(insight["full_content"], hypothesis)
                            if cleaned_contradiction:
                                all_evidence.append(cleaned_contradiction)
                            
            except Exception as e:
                print(f"   ⚠️  RAG search failed for query '{query}': {str(e)}")
                continue
        
        # Remove duplicates and sort by relevance
        unique_evidence = self._deduplicate_evidence(all_evidence)
        print(f"   Found {len(unique_evidence)} pieces of contradictory evidence")
        
        return unique_evidence[:5]  # Limit to top 5 pieces of evidence
    
    def _create_contradiction_queries(self, hypothesis: str) -> List[str]:
        """Create search queries designed to find contradictory evidence"""
        # Use the ORIGINAL simple hypothesis, not the processed version
        original_input = self._extract_original_hypothesis(hypothesis)
        base_terms = self._extract_key_terms(original_input)
        
        contradiction_queries = []
        
        # Add opposing terms and scenarios
        for term in base_terms:
            contradiction_queries.extend([
                f"{term} decline fall drop",
                f"{term} risk failure challenge", 
                f"{term} bearish negative outlook",
                f"{term} overvalued correction"
            ])
        
        # Company-specific contradiction terms
        if any(company in original_input.lower() for company in ['apple', 'aapl']):
            contradiction_queries.extend([
                "apple revenue decline iphone sales",
                "apple competition android market share",
                "apple china ban regulation",
                "tech stock correction valuation"
            ])
        elif any(company in original_input.lower() for company in ['microsoft', 'msft']):
            contradiction_queries.extend([
                "microsoft cloud competition aws",
                "microsoft software decline",
                "tech stock correction"
            ])
        elif any(company in original_input.lower() for company in ['tesla', 'tsla']):
            contradiction_queries.extend([
                "tesla competition electric vehicles",
                "tesla production issues",
                "ev market slowdown"
            ])
        # Bitcoin/crypto
        elif "bitcoin" in original_input.lower() or "btc" in original_input.lower():
            contradiction_queries.extend([
                "bitcoin regulation ban government",
                "cryptocurrency crash volatility risk",
                "bitcoin energy concerns environmental",
                "crypto market manipulation"
            ])
        # Oil
        elif "oil" in original_input.lower():
            contradiction_queries.extend([
                "oil demand peak electric vehicles",
                "renewable energy transition",
                "oil supply increase production",
                "recession oil demand decline"
            ])
        # General market
        else:
            contradiction_queries.extend([
                "market recession economic downturn",
                "inflation interest rates rising",
                "geopolitical uncertainty market risk"
            ])
        
        return contradiction_queries[:6]  # Limit to avoid excessive API calls
    
    def _extract_original_hypothesis(self, processed_text: str) -> str:
        """Extract the original simple hypothesis from processed text"""
        # If the text is very long (like the Apple example), it's been over-processed
        if len(processed_text) > 200:
            # Look for the original thesis statement
            import re
            
            # Look for "Apple will reach" pattern
            simple_patterns = [
                r'([A-Za-z\s]+will reach[^\.]+)',
                r'([A-Za-z\s]+to go above[^\.]+)', 
                r'([A-Za-z\s]+will exceed[^\.]+)',
                r'\*\s*Thesis Statement:\*\*([^*]+)',
                r'Apple \(AAPL\)[^.]+\$220[^.]+2025[^.]*\.'
            ]
            
            for pattern in simple_patterns:
                match = re.search(pattern, processed_text, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    # Clean up any markdown or formatting
                    extracted = re.sub(r'\*+', '', extracted)
                    extracted = re.sub(r'^\*\s*', '', extracted)
                    return extracted
            
            # Fallback: extract first line that looks like a hypothesis
            lines = processed_text.split('\n')
            for line in lines:
                if any(word in line.lower() for word in ['will reach', 'will exceed', 'target']):
                    if len(line) < 150:  # Reasonable length
                        return line.strip()
        
        # If it's already simple, return as-is
        return processed_text
    
    def _extract_key_terms(self, hypothesis: str) -> List[str]:
        """Extract key financial terms from hypothesis with better company recognition"""
        import re
        
        # Extract instruments and key terms
        terms = []
        
        # Company names
        companies = ['apple', 'microsoft', 'google', 'alphabet', 'amazon', 'tesla', 'nvidia', 'meta', 'facebook']
        for company in companies:
            if company in hypothesis.lower():
                terms.append(company)
        
        # Cryptocurrency terms
        if re.search(r'bitcoin|btc', hypothesis.lower()):
            terms.append("bitcoin")
        if re.search(r'ethereum|eth', hypothesis.lower()):
            terms.append("ethereum")
        
        # Other financial terms
        financial_terms = re.findall(r'\b(?:oil|gold|stock|market|price|inflation|interest)\b', hypothesis.lower())
        terms.extend(financial_terms)
        
        # Stock symbols - be more restrictive
        stock_symbols = re.findall(r'\$?([A-Z]{2,5})(?:\s|$|\)|,)', hypothesis)
        for symbol in stock_symbols:
            if symbol not in ['THE', 'AND', 'FOR', 'ARE', 'WILL', 'USD', 'HAS', 'NOT', 'BY', 'END', 'INC']:
                terms.append(symbol.lower())
        
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
            return []  # Return empty list, will use fallbacks later
    
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
        
        # If we don't have enough contradictions, add fallbacks
        if len(all_contradictions) < 3:
            fallback_contradictions = self._get_fallback_contradictions_list()
            for item in fallback_contradictions:
                item["priority"] = self._calculate_priority(item, source_type="fallback")
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
        elif source_type == "ai":
            priority += 0.4  # AI-generated gets lower base score
        else:  # fallback
            priority += 0.3  # Fallback gets lowest base score
        
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
        """Get fallback contradictions if all else fails - backwards compatibility"""
        return self._get_fallback_contradictions_list(hypothesis)
    
    def _get_fallback_contradictions_list(self, hypothesis: str = "") -> List[Dict[str, Any]]:
        """Get intelligent fallback contradictions based on hypothesis analysis"""
        
        hypothesis_lower = hypothesis.lower() if hypothesis else ""
        
        # Apple-specific contradictions
        if 'apple' in hypothesis_lower or 'aapl' in hypothesis_lower:
            return [
                {
                    "quote": "Apple's iPhone sales in China have declined due to increased competition from domestic brands and regulatory restrictions.",
                    "reason": "China represents approximately 20% of Apple's revenue, and market share loss could limit reaching the price target.",
                    "source": "China Market Analysis",
                    "strength": "Strong",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "The global smartphone market has reached saturation with declining year-over-year growth rates.",
                    "reason": "Market saturation in developed countries creates structural headwinds for Apple's core iPhone business.",
                    "source": "Industry Analysis",
                    "strength": "Strong",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "Apple's current valuation metrics suggest the stock is trading at premium levels compared to historical averages.",
                    "reason": "Reaching higher price targets would require even more elevated valuation multiples that may not be sustainable.",
                    "source": "Valuation Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "Rising interest rates typically lead to multiple compression for high-valuation technology stocks.",
                    "reason": "Elevated interest rates could pressure growth stock valuations and limit price appreciation.",
                    "source": "Monetary Policy Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                }
            ]
        
        # Bitcoin-specific contradictions
        elif 'bitcoin' in hypothesis_lower or 'btc' in hypothesis_lower:
            return [
                {
                    "quote": "Regulatory uncertainty continues to pose significant risks to Bitcoin adoption and price stability.",
                    "reason": "Government interventions could limit institutional adoption and retail accessibility.",
                    "source": "Regulatory Risk Analysis",
                    "strength": "Strong",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "Bitcoin has historically experienced 80-90% drawdowns after major bull runs.",
                    "reason": "Extreme volatility patterns suggest difficulty maintaining high price levels over time.",
                    "source": "Technical Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "Macroeconomic tightening cycles typically pressure speculative assets like Bitcoin.",
                    "reason": "Current monetary policy conditions may not support rapid price appreciation to target levels.",
                    "source": "Macroeconomic Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                }
            ]
        
        # Oil-specific contradictions
        elif 'oil' in hypothesis_lower:
            return [
                {
                    "quote": "Global oil demand growth is slowing as electric vehicle adoption accelerates and energy efficiency improves.",
                    "reason": "The energy transition could reduce long-term demand growth and limit price appreciation potential.",
                    "source": "Energy Transition Analysis",
                    "strength": "Strong",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "OPEC+ production capacity remains significant and could increase output if prices rise substantially.",
                    "reason": "Increased production from major oil producers could cap price increases and prevent sustained higher levels.",
                    "source": "OPEC Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                }
            ]
        
        # Generic contradictions for other assets
        else:
            return [
                {
                    "quote": "Market volatility and economic uncertainty could prevent the projected price target from being achieved within the specified timeframe.",
                    "reason": "Current market conditions and external economic factors often impact price movements more than fundamental analysis suggests.",
                    "source": "Market Risk Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "The target price may represent a significant premium to current valuation metrics and historical trading ranges.",
                    "reason": "Achieving substantial price appreciation requires sustained fundamental improvements and favorable market conditions.",
                    "source": "Valuation Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                },
                {
                    "quote": "The specified timeframe may be too aggressive given current market dynamics and typical price movement patterns.",
                    "reason": "Market timing predictions are notoriously difficult, and external factors can significantly delay expected price movements.",
                    "source": "Timing Analysis",
                    "strength": "Medium",
                    "evidence_type": "fallback"
                }
            ]

def create():
    """Create and return a hybrid contradiction agent instance"""
    return HybridContradictionAgent()

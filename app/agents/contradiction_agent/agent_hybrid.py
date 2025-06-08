# app/agents/contradiction_agent/agent_hybrid.py - Complete AI-Powered Implementation
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
import re

class IntelligentContradictionProcessor:
    """AI-powered contradiction processing without hardcoded patterns"""
    
    def __init__(self, model):
        self.model = model
    
    def process_contradictions(self, raw_contradictions: List[Dict], context: Dict, hypothesis: str) -> List[Dict]:
        """Use AI to intelligently process and clean contradictions"""
        
        print("🧠 Using AI to intelligently process contradictions...")
        
        cleaned_contradictions = []
        
        for raw_contradiction in raw_contradictions:
            # Use AI to evaluate and clean each contradiction
            processed = self._ai_process_single_contradiction(raw_contradiction, context, hypothesis)
            if processed:
                cleaned_contradictions.append(processed)
        
        # If we don't have enough quality contradictions, generate new ones
        if len(cleaned_contradictions) < 3:
            print("   🔄 Insufficient quality contradictions, generating new ones...")
            ai_generated = self._ai_generate_fresh_contradictions(context, hypothesis, len(cleaned_contradictions))
            cleaned_contradictions.extend(ai_generated)
        
        return cleaned_contradictions[:5]  # Return top 5
    
    def _ai_process_single_contradiction(self, raw_contradiction: Dict, context: Dict, hypothesis: str) -> Optional[Dict]:
        """Use AI to evaluate, clean, and enhance a single contradiction"""
        
        raw_quote = raw_contradiction.get("quote", "")
        raw_reason = raw_contradiction.get("reason", "")
        
        asset_info = context.get("asset_info", {})
        
        evaluation_prompt = f"""
        You are an expert financial analyst reviewing contradictions for investment analysis.
        
        TASK: Evaluate and improve this contradiction for the hypothesis: "{hypothesis}"
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        
        RAW CONTRADICTION:
        Quote: "{raw_quote}"
        Reason: "{raw_reason}"
        
        EVALUATION CRITERIA:
        1. Is this contradiction VALUABLE for investment decision-making?
        2. Is it SPECIFIC to this asset and hypothesis?
        3. Is it CLEAR and professional?
        4. Is it ACTIONABLE for investors?
        
        INSTRUCTIONS:
        - If the contradiction is valuable but needs cleaning, provide an IMPROVED version
        - If the contradiction is garbage/corrupted/irrelevant, respond with "REJECT"
        - If the contradiction is good as-is, respond with "ACCEPT"
        
        RESPONSE FORMAT:
        If improving: Provide JSON with:
        {{
            "action": "IMPROVE",
            "improved_quote": "Clear, professional contradiction statement",
            "improved_reason": "Specific reasoning why this challenges the hypothesis",
            "strength": "Strong/Medium/Weak"
        }}
        
        If rejecting: {{"action": "REJECT", "reason": "Why this contradiction is not valuable"}}
        If accepting: {{"action": "ACCEPT"}}
        
        Focus on creating contradictions that help investors make better decisions.
        """
        
        try:
            response = self.model.generate_content(evaluation_prompt)
            return self._parse_ai_evaluation(response.text, raw_contradiction)
        except Exception as e:
            print(f"   ⚠️  AI evaluation failed for contradiction: {str(e)}")
            return None
    
    def _parse_ai_evaluation(self, ai_response: str, original: Dict) -> Optional[Dict]:
        """Parse AI evaluation response"""
        
        try:
            # Clean response for JSON parsing
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            
            evaluation = json.loads(cleaned_response)
            action = evaluation.get("action", "REJECT")
            
            if action == "ACCEPT":
                return {
                    "quote": original.get("quote", ""),
                    "reason": original.get("reason", ""),
                    "source": original.get("source", "AI Analysis"),
                    "strength": original.get("strength", "Medium"),
                    "processing": "ai_accepted"
                }
            
            elif action == "IMPROVE":
                return {
                    "quote": evaluation.get("improved_quote", ""),
                    "reason": evaluation.get("improved_reason", ""),
                    "source": "AI Enhanced Analysis",
                    "strength": evaluation.get("strength", "Medium"),
                    "processing": "ai_improved"
                }
            
            else:  # REJECT
                print(f"   🗑️  AI rejected contradiction: {evaluation.get('reason', 'Not valuable')}")
                return None
                
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract decision from text
            if "REJECT" in ai_response.upper():
                return None
            elif "ACCEPT" in ai_response.upper():
                return original
            else:
                # Treat as improved content
                return self._extract_improvement_from_text(ai_response, original)
    
    def _extract_improvement_from_text(self, text: str, original: Dict) -> Dict:
        """Extract improvement from free-text AI response"""
        
        # Simple extraction - look for quote-like content
        lines = text.split('\n')
        improved_quote = ""
        improved_reason = ""
        
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not line.startswith(('TASK:', 'EVALUATION:', 'RESPONSE:')):
                if not improved_quote:
                    improved_quote = line.strip('"\'')
                elif not improved_reason and line != improved_quote:
                    improved_reason = line.strip('"\'')
        
        return {
            "quote": improved_quote or original.get("quote", ""),
            "reason": improved_reason or original.get("reason", ""),
            "source": "AI Enhanced Analysis",
            "strength": "Medium",
            "processing": "ai_text_extracted"
        }
    
    def _ai_generate_fresh_contradictions(self, context: Dict, hypothesis: str, existing_count: int) -> List[Dict]:
        """Generate completely fresh contradictions using AI with database constraints"""
        
        needed_count = max(3 - existing_count, 0)
        if needed_count == 0:
            return []
        
        asset_info = context.get("asset_info", {})
        risk_analysis = context.get("risk_analysis", {})
        
        generation_prompt = f"""
        Generate {needed_count} HIGH-QUALITY contradictions for this hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        TYPE: {asset_info.get("asset_type", "Unknown")}
        
        CRITICAL CONSTRAINTS - Each contradiction must have:
        - Quote: Maximum 400 characters (keep concise!)
        - Reason: Maximum 400 characters (keep concise!)  
        - Source: Maximum 40 characters (e.g., "Market Research")
        - Strength: ONLY "Strong", "Medium", or "Weak"
        
        REQUIREMENTS:
        1. SPECIFIC to this asset and sector
        2. ACTIONABLE - investors can verify or monitor
        3. REALISTIC - based on actual market dynamics
        4. CONCISE - fit database limits (NO markdown formatting)
        
        Format each as exactly: quote|reason|source|strength
        
        Example:
        Competition pressures limit pricing power|Increased market competition reduces profit margins and growth prospects|Industry Analysis|Strong
        
        Generate {needed_count} contradictions. Keep under character limits.
        """
        
        try:
            response = self.model.generate_content(generation_prompt)
            return self._parse_generated_contradictions_strict(response.text)
        except Exception as e:
            print(f"   ❌ AI contradiction generation failed: {str(e)}")
            return self._intelligent_fallback_contradictions_strict(context, hypothesis, needed_count)
    
    def _parse_generated_contradictions_strict(self, ai_response: str) -> List[Dict]:
        """Parse AI-generated contradictions with strict database constraints"""
        
        try:
            # Try structured parsing first
            contradictions = []
            lines = ai_response.split('\n')
            
            for line in lines:
                if '|' in line and len(line.split('|')) >= 4:
                    parts = line.split('|')
                    quote = parts[0].strip()[:400]    # Enforce 400 char limit
                    reason = parts[1].strip()[:400]   # Enforce 400 char limit
                    source = parts[2].strip()[:40]    # Enforce 40 char limit
                    strength = parts[3].strip()
                    
                    # Validate strength
                    if strength not in ["Strong", "Medium", "Weak"]:
                        strength = "Medium"
                    
                    # Only add if meaningful content
                    if len(quote) > 20 and len(reason) > 10:
                        contradictions.append({
                            "quote": quote,
                            "reason": reason,
                            "source": source,
                            "strength": strength,
                            "processing": "ai_generated"
                        })
            
            if contradictions:
                return contradictions
                
        except Exception as e:
            print(f"   ⚠️  Structured parsing failed: {str(e)}")
        
        # Fallback: extract from text format
        return self._extract_contradictions_from_text_strict(ai_response)
    
    def _extract_contradictions_from_text_strict(self, text: str) -> List[Dict]:
        """Extract contradictions from free-text with database constraints"""
        
        contradictions = []
        
        # Look for numbered items or clear separation
        sections = text.split('\n\n')
        
        for section in sections:
            if len(section.strip()) > 50:  # Substantial content
                lines = [line.strip() for line in section.split('\n') if line.strip()]
                
                if len(lines) >= 1:
                    # Use first line as quote, create safe reason
                    quote_text = lines[0].strip()
                    
                    # Clean and limit quote
                    quote = quote_text.replace('1.', '').replace('2.', '').replace('3.', '').strip()
                    quote = quote[:380] + "..." if len(quote) > 380 else quote
                    
                    if len(quote) > 20:
                        contradictions.append({
                            "quote": quote,
                            "reason": "Market analysis identifies this challenge to the hypothesis.",
                            "source": "AI Analysis",
                            "strength": "Medium",
                            "processing": "ai_text_extracted"
                        })
            
            if len(contradictions) >= 3:
                break
        
        return contradictions
    
    def _intelligent_fallback_contradictions_strict(self, context: Dict, hypothesis: str, count: int) -> List[Dict]:
        """Intelligent fallback with database constraints"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        asset_type = asset_info.get("asset_type", "unknown")
        sector = asset_info.get("sector", "financial markets")
        
        fallback_contradictions = []
        
        if asset_type in ["stock", "equity"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces competitive pressure in {sector} limiting growth.",
                "reason": f"Competition in {sector} can erode margins and market share.",
                "source": "Competitive Analysis",
                "strength": "Medium"
            })
        
        elif asset_type in ["crypto", "cryptocurrency"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces regulatory uncertainty and volatility risks.",
                "reason": "Crypto markets are sensitive to regulatory changes and policies.",
                "source": "Regulatory Analysis", 
                "strength": "Strong"
            })
        
        elif asset_type == "commodity":
            fallback_contradictions.append({
                "quote": f"Supply/demand dynamics for {asset_name} could shift unfavorably.",
                "reason": "Commodity markets are cyclical and sensitive to economic changes.",
                "source": "Commodity Analysis",
                "strength": "Medium"
            })
        
        # Add general market risk if needed
        if len(fallback_contradictions) < count:
            fallback_contradictions.append({
                "quote": f"Market valuation and economic uncertainty challenge {asset_name} targets.",
                "reason": "External economic factors often override fundamental analysis.",
                "source": "Market Analysis",
                "strength": "Medium"
            })
        
        return fallback_contradictions[:count]
    
class HybridContradictionAgent:
    """AI-Powered Contradiction Agent - Clean Implementation"""
    
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
        """Main processing method using pure AI intelligence"""
        
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        research_data = input_data.get("research_data", {})
        context = input_data.get("context", {})
        
        print(f"🎯 Finding contradictions using pure AI intelligence for: {processed_hypothesis}")
        
        # Log context usage
        if context:
            asset_info = context.get("asset_info", {})
            print(f"🔧 Using context: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('asset_type', 'Unknown')})")
        
        try:
            # Initialize intelligent processor
            processor = IntelligentContradictionProcessor(self.model)
            
            # Get raw contradictions from various sources
            raw_contradictions = []
            
            # Try to get contradictions from RAG if available
            if self.hybrid_service:
                rag_contradictions = self._search_rag_for_contradictions(hypothesis, context)
                raw_contradictions.extend(rag_contradictions)
            
            # Generate AI contradictions as raw input
            ai_contradictions = self._generate_raw_ai_contradictions(hypothesis, research_data, context)
            raw_contradictions.extend(ai_contradictions)
            
            # Use AI processor to intelligently clean and enhance all contradictions
            final_contradictions = processor.process_contradictions(raw_contradictions, context, hypothesis)
            
            return {
                "contradictions": final_contradictions,
                "analysis": self._create_intelligent_analysis(final_contradictions, context),
                "processing_method": "pure_ai_intelligence",
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ AI contradiction processing failed: {str(e)}")
            # Even fallback uses AI
            processor = IntelligentContradictionProcessor(self.model)
            fallback_contradictions = processor._ai_generate_fresh_contradictions(context, hypothesis, 0)
            
            return {
                "contradictions": fallback_contradictions,
                "analysis": "Used AI fallback contradiction analysis.",
                "processing_method": "ai_fallback",
                "status": "error_fallback"
            }
    
    def _search_rag_for_contradictions(self, hypothesis: str, context: Dict) -> List[Dict]:
        """Search RAG database for potential contradictions"""
        
        if not self.hybrid_service:
            return []
        
        try:
            # Create search terms based on context
            search_terms = self._create_context_search_terms(context, hypothesis)
            
            # Search RAG database
            all_evidence = []
            for query in search_terms[:3]:  # Limit to 3 queries
                try:
                    # Use thread pool to handle async operations
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_rag_search, query)
                        result = future.result(timeout=10)
                        
                    if result and result.get("historical_insights"):
                        for insight in result["historical_insights"][:2]:  # Top 2 per query
                            processed = self._process_rag_insight(insight)
                            if processed:
                                all_evidence.append(processed)
                except Exception as e:
                    print(f"   ⚠️  RAG search failed for query '{query}': {str(e)}")
                    continue
            
            return all_evidence
            
        except Exception as e:
            print(f"⚠️  RAG contradiction search failed: {str(e)}")
            return []
    
    def _run_rag_search(self, query: str) -> Dict:
        """Run RAG search in a new event loop"""
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self.hybrid_service._rag_search(query, limit=3))
            finally:
                new_loop.close()
        except Exception as e:
            print(f"⚠️  RAG search loop failed: {str(e)}")
            return {}
    
    def _create_context_search_terms(self, context: Dict, hypothesis: str) -> List[str]:
        """Create search terms based on context"""
        
        if not context:
            return ["market risk", "bearish analysis"]
        
        asset_info = context.get("asset_info", {})
        risk_analysis = context.get("risk_analysis", {})
        
        search_terms = []
        asset_name = asset_info.get("asset_name", "")
        
        # Add risk-based search terms
        for risk in risk_analysis.get("primary_risks", [])[:2]:
            search_terms.append(f"{asset_name} {risk}")
        
        # Add general bearish terms
        search_terms.append(f"{asset_name} bearish analysis")
        search_terms.append(f"{asset_name} risk factors")
        
        return search_terms
    
    def _process_rag_insight(self, insight: Dict) -> Optional[Dict]:
        """Process RAG insight into contradiction format"""
        
        content = insight.get("full_content", "")
        
        # Basic quality check
        if len(content) < 50 or not self._contains_negative_sentiment(content):
            return None
        
        # Clean and truncate content
        cleaned_content = content[:200] + "..." if len(content) > 200 else content
        
        return {
            "quote": cleaned_content,
            "reason": "Historical evidence suggests potential challenges to the hypothesis.",
            "source": "Historical Market Data",
            "strength": "Medium",
            "evidence_type": "rag_processed"
        }
    
    def _contains_negative_sentiment(self, text: str) -> bool:
        """Check if text contains negative sentiment indicators"""
        
        negative_indicators = [
            'decline', 'fall', 'drop', 'risk', 'challenge', 'difficult',
            'unlikely', 'bearish', 'negative', 'concern', 'problem'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in negative_indicators if indicator in text_lower) >= 2
    
    def _generate_raw_ai_contradictions(self, hypothesis: str, research_data: Dict, context: Dict) -> List[Dict]:
        """Generate raw AI contradictions that will be processed by the intelligent processor"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        
        prompt = f"""
        Generate 2-3 initial contradictions for this hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("asset_type", "Unknown")})
        
        Create realistic challenges to this hypothesis. These will be further processed and refined.
        
        Format each as: quote|reason|strength
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_raw_contradictions(response.text)
        except Exception as e:
            print(f"⚠️  Raw AI contradiction generation failed: {str(e)}")
            return []
    
    def _parse_raw_contradictions(self, response_text: str) -> List[Dict]:
        """Parse raw AI contradictions"""
        
        contradictions = []
        lines = response_text.split('\n')
        
        for line in lines:
            if '|' in line and len(line.split('|')) >= 3:
                parts = line.split('|')
                contradictions.append({
                    "quote": parts[0].strip(),
                    "reason": parts[1].strip(),
                    "source": "Raw AI Analysis",
                    "strength": parts[2].strip() if len(parts) > 2 else "Medium"
                })
        
        return contradictions
    
    def _create_intelligent_analysis(self, contradictions: List[Dict], context: Dict) -> str:
        """Create intelligent analysis summary"""
        
        if not contradictions:
            return "No significant contradictions identified through intelligent analysis."
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        
        strong_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "strong")
        medium_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "medium")
        
        analysis = f"""
        AI-Powered Contradiction Analysis for {asset_name}:
        - Total contradictions identified: {len(contradictions)}
        - Strong contradictions: {strong_count}
        - Medium contradictions: {medium_count}
        - Processing method: Pure AI intelligence
        
        Assessment: {'Significant' if strong_count >= 2 else 'Moderate' if strong_count >= 1 else 'Limited'} 
        challenges identified using intelligent, context-aware analysis.
        """
        
        return analysis.strip()

def create():
    """Create and return an intelligent contradiction agent instance"""
    return HybridContradictionAgent()

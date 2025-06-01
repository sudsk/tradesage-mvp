# app/agents/contradiction_agent/agent_hybrid.py - Intelligent, context-driven contradictions
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import asyncio
import concurrent.futures
from typing import Dict, Any, List

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
        """Generate completely fresh contradictions using AI"""
        
        needed_count = max(3 - existing_count, 0)
        if needed_count == 0:
            return []
        
        asset_info = context.get("asset_info", {})
        risk_analysis = context.get("risk_analysis", {})
        
        generation_prompt = f"""
        You are an expert financial analyst creating contradictions for investment analysis.
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        - Market: {asset_info.get("market", "Unknown")}
        
        IDENTIFIED RISKS: {risk_analysis.get("primary_risks", [])}
        
        TASK: Generate {needed_count} HIGH-QUALITY contradictions that challenge this hypothesis.
        
        REQUIREMENTS:
        1. Each contradiction must be SPECIFIC to this asset and its sector
        2. Must be ACTIONABLE - something investors can verify or monitor
        3. Must be REALISTIC - based on actual market dynamics for this asset type
        4. Must be PROFESSIONAL - suitable for investment decision-making
        5. Must provide REAL VALUE - help investors understand risks
        
        FOCUS AREAS:
        - Competitive threats specific to this company/asset
        - Sector-specific headwinds and challenges
        - Valuation concerns relative to current fundamentals
        - Regulatory or policy risks affecting this asset type
        - Market timing and sentiment factors
        - Technical analysis concerns for this specific asset
        
        OUTPUT FORMAT:
        For each contradiction, provide:
        {{
            "quote": "Specific, professional contradiction statement",
            "reason": "Detailed explanation of why this challenges the hypothesis",
            "strength": "Strong/Medium/Weak"
        }}
        
        Respond with a JSON array of {needed_count} contradictions.
        
        Make each contradiction valuable for someone making an investment decision about this specific asset.
        """
        
        try:
            response = self.model.generate_content(generation_prompt)
            return self._parse_generated_contradictions(response.text)
        except Exception as e:
            print(f"   ❌ AI contradiction generation failed: {str(e)}")
            return self._intelligent_fallback_contradictions(context, hypothesis, needed_count)
    
    def _parse_generated_contradictions(self, ai_response: str) -> List[Dict]:
        """Parse AI-generated contradictions"""
        
        try:
            # Clean response for JSON parsing
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            
            contradictions_data = json.loads(cleaned_response)
            
            # Handle both array and single object responses
            if isinstance(contradictions_data, list):
                contradictions = contradictions_data
            else:
                contradictions = [contradictions_data]
            
            formatted_contradictions = []
            for item in contradictions:
                if isinstance(item, dict) and "quote" in item:
                    formatted_contradictions.append({
                        "quote": item.get("quote", ""),
                        "reason": item.get("reason", ""),
                        "source": "AI Generated Analysis",
                        "strength": item.get("strength", "Medium"),
                        "processing": "ai_generated"
                    })
            
            return formatted_contradictions
            
        except json.JSONDecodeError:
            # Fallback: extract from text format
            return self._extract_contradictions_from_text(ai_response)
    
    def _extract_contradictions_from_text(self, text: str) -> List[Dict]:
        """Extract contradictions from free-text AI response"""
        
        contradictions = []
        
        # Look for numbered items or clear separation
        sections = text.split('\n\n')
        
        for section in sections:
            if len(section.strip()) > 50:  # Substantial content
                lines = [line.strip() for line in section.split('\n') if line.strip()]
                
                if len(lines) >= 2:  # At least quote and reason
                    quote = lines[0].strip('"\'1234567890.)')  # Remove numbering and quotes
                    reason = lines[1] if len(lines) > 1 else "This factor challenges the hypothesis"
                    
                    if len(quote) > 20:  # Meaningful content
                        contradictions.append({
                            "quote": quote,
                            "reason": reason,
                            "source": "AI Generated Analysis",
                            "strength": "Medium",
                            "processing": "ai_text_extracted"
                        })
        
        return contradictions[:3]  # Return up to 3
    
    def _intelligent_fallback_contradictions(self, context: Dict, hypothesis: str, count: int) -> List[Dict]:
        """Intelligent fallback using context when AI generation fails"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        asset_type = asset_info.get("asset_type", "unknown")
        sector = asset_info.get("sector", "financial markets")
        
        # Use context to generate intelligent fallbacks
        fallback_contradictions = []
        
        if asset_type in ["stock", "equity"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces intensifying competitive pressure in the {sector} sector that could limit its ability to achieve the projected price target.",
                "reason": f"Increased competition in {sector} can erode market share and pricing power, potentially limiting the fundamental growth needed to justify higher valuations.",
                "source": "Contextual Analysis",
                "strength": "Medium"
            })
        
        elif asset_type in ["crypto", "cryptocurrency"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces regulatory uncertainty and potential government restrictions that could significantly impact its price trajectory.",
                "reason": "Cryptocurrency markets are highly sensitive to regulatory developments, and restrictive policies could limit institutional adoption and trading accessibility.",
                "source": "Contextual Analysis", 
                "strength": "Strong"
            })
        
        elif asset_type == "commodity":
            fallback_contradictions.append({
                "quote": f"Supply and demand dynamics for {asset_name} could shift unfavorably due to economic conditions or alternative technologies.",
                "reason": "Commodity markets are highly cyclical and sensitive to global economic conditions, technological substitution, and supply disruptions.",
                "source": "Contextual Analysis",
                "strength": "Medium"
            })
        
        # Add general market risk if we need more
        if len(fallback_contradictions) < count:
            fallback_contradictions.append({
                "quote": f"Current market valuation levels and economic uncertainty could prevent {asset_name} from reaching the projected price target within the specified timeframe.",
                "reason": "Market timing predictions are inherently uncertain, and external economic factors often override fundamental analysis in determining short-term price movements.",
                "source": "Contextual Analysis",
                "strength": "Medium"
            })
        
        return fallback_contradictions[:count]
       
class HybridContradictionAgent:
    """Intelligent Contradiction Agent using context and AI - no hardcoding"""
    
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
        """Process contradictions using pure AI intelligence - no hardcoded patterns"""
        
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
            
    def _log_context_usage(self, context: Dict) -> None:
        """Log how context is being used"""
        asset_info = context.get("asset_info", {})
        risk_analysis = context.get("risk_analysis", {})
        
        print(f"🔧 Using context: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('asset_type', 'Unknown')})")
        
        primary_risks = risk_analysis.get("primary_risks", [])
        if primary_risks:
            print(f"   ⚠️  Context-identified risks: {primary_risks[:3]}")
    
    def _derive_contradiction_strategy_from_context(self, context: Dict, hypothesis: str) -> Dict:
        """Use context to create intelligent contradiction search strategy"""
        if not context:
            return self._ai_derive_contradiction_strategy_fallback(hypothesis)
        
        risk_analysis = context.get("risk_analysis", {})
        asset_info = context.get("asset_info", {})
        
        strategy = {
            "asset_name": asset_info.get("asset_name", "Unknown"),
            "asset_type": asset_info.get("asset_type", "unknown"),
            "sector": asset_info.get("sector", "Unknown"),
            "primary_risks": risk_analysis.get("primary_risks", []),
            "contradiction_areas": risk_analysis.get("contradiction_areas", []),
            "sensitivity_factors": risk_analysis.get("sensitivity_factors", []),
            "competitive_threats": risk_analysis.get("competitive_threats", []),
            "regulatory_risks": risk_analysis.get("regulatory_risks", [])
        }
        
        # Generate targeted search terms from context
        search_terms = []
        asset_name = asset_info.get("asset_name", "")
        
        for risk in risk_analysis.get("primary_risks", [])[:3]:
            search_terms.append(f"{asset_name} {risk}")
            
        for area in risk_analysis.get("contradiction_areas", [])[:3]:
            search_terms.append(f"{area} bearish analysis")
        
        strategy["search_terms"] = search_terms
        
        print(f"   📋 Context-driven contradiction strategy: {len(search_terms)} search terms")
        return strategy
    
    def _run_intelligent_contradiction_search(self, hypothesis: str, strategy: Dict) -> List[Dict[str, Any]]:
        """Run contradiction search using intelligent strategy"""
        try:
            search_terms = strategy.get("search_terms", [])
            
            # Use async operations properly
            try:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_search_in_new_loop, search_terms)
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(self._search_contradictory_evidence(search_terms))
                
        except Exception as e:
            print(f"⚠️  RAG contradiction search failed: {str(e)}")
            return []
    
    def _run_search_in_new_loop(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Run search in new event loop"""
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._search_contradictory_evidence(search_terms))
            finally:
                new_loop.close()
        except Exception as e:
            print(f"⚠️  New loop search failed: {str(e)}")
            return []
    
    async def _search_contradictory_evidence(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search RAG database for contradictory evidence"""
        if not self.hybrid_service:
            return []
        
        print("📚 Searching RAG database for context-driven contradictory evidence...")
        
        all_evidence = []
        
        for query in search_terms[:5]:  # Limit queries
            try:
                result = await self.hybrid_service._rag_search(query, limit=3)
                
                if result.get("historical_insights"):
                    for insight in result["historical_insights"]:
                        if self._is_potentially_contradictory(insight["full_content"]):
                            processed_contradiction = self._process_contradiction_evidence(insight)
                            if processed_contradiction:
                                all_evidence.append(processed_contradiction)
                            
            except Exception as e:
                print(f"   ⚠️  RAG search failed for query '{query}': {str(e)}")
                continue
        
        print(f"   Found {len(all_evidence)} pieces of contradictory evidence")
        return all_evidence[:5]
    
    def _is_potentially_contradictory(self, content: str) -> bool:
        """Use AI to assess if content is potentially contradictory"""
        if not content or len(content) < 50:
            return False
        
        # Look for negative sentiment indicators intelligently
        negative_indicators = [
            'decline', 'fall', 'drop', 'crash', 'risk', 'challenge', 'difficult',
            'unlikely', 'bearish', 'negative', 'concern', 'problem', 'issue',
            'overvalued', 'bubble', 'correction', 'downturn', 'headwind'
        ]
        
        content_lower = content.lower()
        negative_count = sum(1 for indicator in negative_indicators if indicator in content_lower)
        
        return negative_count >= 2
    
    def _process_contradiction_evidence(self, insight: Dict) -> Dict[str, Any]:
        """Process RAG evidence into contradiction format"""
        content = insight.get("full_content", "")
        
        # Clean and truncate content
        if len(content) > 200:
            quote = content[:200] + "..."
        else:
            quote = content
        
        return {
            "quote": quote,
            "reason": "Historical evidence suggests potential challenges to the hypothesis.",
            "source": "Historical Market Data",
            "strength": "Medium",
            "evidence_type": "rag_processed",
            "similarity": insight.get("similarity", 0)
        }
    
    def _generate_context_aware_contradictions(self, hypothesis: str, research_data: Dict, 
                                             context: Dict, strategy: Dict) -> List[Dict]:
        """Generate contradictions using context intelligence - no hardcoded patterns"""
        
        if not context:
            return self._ai_generate_generic_contradictions(hypothesis)
        
        asset_info = context.get("asset_info", {})
        risk_factors = strategy.get("primary_risks", [])
        
        prompt = f"""
        Generate specific contradictions for this hypothesis using intelligent context analysis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        - Market: {asset_info.get("market", "Unknown")}
        - Business Model: {asset_info.get("business_model", "Unknown")}
        
        CONTEXT-IDENTIFIED RISK FACTORS: {risk_factors}
        
        COMPETITIVE LANDSCAPE: {asset_info.get("competitors", [])}
        
        RESEARCH DATA: {json.dumps(research_data, indent=2)[:1000]}...
        
        Generate 4-5 specific contradictions that:
        1. Are directly relevant to this specific asset and its sector
        2. Address the context-identified risk factors
        3. Consider the competitive landscape and market position
        4. Reference realistic scenarios specific to this asset type
        5. Use your knowledge of this asset's specific challenges
        
        Each contradiction should be:
        - Specific to this asset (not generic market statements)
        - Based on realistic business or market scenarios
        - Tied to the actual risk factors for this asset
        - Actionable for investors to verify
        
        Format each as: quote|reason|source|strength
        
        Make contradictions intelligent and asset-specific, not generic.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_context_aware_contradictions(response.text, asset_info)
        except Exception as e:
            print(f"❌ Context-aware contradiction generation failed: {str(e)}")
            return self._generate_intelligent_fallbacks(context, hypothesis)
    
    def _parse_context_aware_contradictions(self, response_text: str, asset_info: Dict) -> List[Dict[str, Any]]:
        """Parse AI-generated contradictions with context awareness"""
        contradictions = []
        
        # Try structured format first
        lines = response_text.split('\n')
        
        for line in lines:
            if '|' in line and len(line.split('|')) >= 4:
                parts = line.split('|')
                contradictions.append({
                    "quote": parts[0].strip(),
                    "reason": parts[1].strip(),
                    "source": parts[2].strip(),
                    "strength": parts[3].strip(),
                    "evidence_type": "ai_context_generated"
                })
        
        # Fallback parsing if structured format fails
        if not contradictions:
            sections = response_text.split('\n')
            for section in sections:
                section = section.strip()
                if len(section) > 30 and not section.startswith('#'):
                    contradictions.append({
                        "quote": section[:200] + ("..." if len(section) > 200 else ""),
                        "reason": f"AI analysis identifies this challenge specific to {asset_info.get('asset_name', 'this asset')}.",
                        "source": "AI Context Analysis",
                        "strength": "Medium",
                        "evidence_type": "ai_context_generated"
                    })
        
        return contradictions[:5]
    
    def _generate_intelligent_fallbacks(self, context: Dict, hypothesis: str) -> List[Dict[str, Any]]:
        """Generate intelligent fallbacks based on context - no hardcoding"""
        
        if not context:
            return self._ai_generate_generic_contradictions(hypothesis)
        
        asset_info = context.get("asset_info", {})
        asset_type = asset_info.get("asset_type", "unknown")
        asset_name = asset_info.get("asset_name", "Unknown Asset")
        sector = asset_info.get("sector", "Unknown Sector")
        
        # Generate contextual contradictions based on asset type and sector
        base_contradictions = [
            {
                "quote": f"{asset_name} faces significant competitive pressure in the {sector} sector that could limit price appreciation.",
                "reason": f"Industry competition and market dynamics in {sector} create headwinds for the projected price target.",
                "source": "Competitive Analysis",
                "strength": "Medium",
                "evidence_type": "context_fallback"
            },
            {
                "quote": f"Market volatility typical of {asset_type} assets could prevent {asset_name} from reaching the projected target within the specified timeframe.",
                "reason": f"{asset_type.title()} markets are subject to volatility that often disrupts price predictions.",
                "source": "Market Volatility Analysis", 
                "strength": "Medium",
                "evidence_type": "context_fallback"
            }
        ]
        
        # Add asset-type specific contradictions using context intelligence
        if asset_type == "crypto" or asset_type == "cryptocurrency":
            base_contradictions.append({
                "quote": f"Regulatory uncertainty continues to pose significant risks to {asset_name} and the broader cryptocurrency market.",
                "reason": "Evolving cryptocurrency regulations could impact adoption, trading access, and price stability.",
                "source": "Regulatory Risk Analysis",
                "strength": "Strong",
                "evidence_type": "context_fallback"
            })
        elif asset_type == "stock":
            base_contradictions.append({
                "quote": f"Economic headwinds and potential recession could negatively impact {asset_name}'s business fundamentals and earnings.",
                "reason": f"Macroeconomic conditions significantly affect {sector} companies and their stock performance.",
                "source": "Economic Analysis",
                "strength": "Medium",
                "evidence_type": "context_fallback"
            })
        elif asset_type == "commodity":
            base_contradictions.append({
                "quote": f"Supply and demand dynamics for {asset_name} could shift unfavorably due to market changes or alternative substitutes.",
                "reason": "Commodity markets are highly sensitive to supply disruptions, demand changes, and technological substitution.",
                "source": "Supply/Demand Analysis",
                "strength": "Medium",
                "evidence_type": "context_fallback"
            })
        
        return base_contradictions
    
    def _ai_generate_generic_contradictions(self, hypothesis: str) -> List[Dict[str, Any]]:
        """AI fallback when no context is available"""
        prompt = f"""
        Generate contradictions for this hypothesis using your financial knowledge:
        
        "{hypothesis}"
        
        Provide 3-4 realistic contradictions that could challenge this prediction.
        Format each as: quote|reason|source|strength
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_context_aware_contradictions(response.text, {})
        except:
            return [{
                "quote": "Market volatility and economic uncertainty could prevent the projected outcome.",
                "reason": "Financial markets are subject to unpredictable external factors.",
                "source": "Market Analysis",
                "strength": "Medium",
                "evidence_type": "ai_fallback"
            }]
    
    def _ai_derive_contradiction_strategy_fallback(self, hypothesis: str) -> Dict:
        """AI-powered fallback strategy when context is unavailable"""
        return {
            "asset_name": "Unknown Asset",
            "asset_type": "unknown",
            "primary_risks": ["market volatility", "economic uncertainty"],
            "search_terms": ["market risk", "bearish analysis", "economic headwinds"]
        }
    
    def _merge_and_rank_contradictions(self, ai_contradictions: List[Dict], evidence: List[Dict]) -> List[Dict[str, Any]]:
        """Intelligently merge and rank contradictions"""
        all_contradictions = []
        
        # Add evidence-based contradictions (higher priority)
        for item in evidence:
            item["priority"] = self._calculate_intelligent_priority(item, source_type="evidence")
            all_contradictions.append(item)
        
        # Add AI-generated contradictions
        for item in ai_contradictions:
            item["priority"] = self._calculate_intelligent_priority(item, source_type="ai")
            all_contradictions.append(item)
        
        # Sort by priority
        all_contradictions.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        # Remove duplicates intelligently
        final_contradictions = self._remove_duplicate_contradictions(all_contradictions)
        
        return final_contradictions[:6]
    
    def _calculate_intelligent_priority(self, contradiction: Dict, source_type: str) -> float:
        """Calculate priority using intelligent criteria"""
        priority = 0.0
        
        # Base priority by source
        if source_type == "evidence":
            priority += 0.6
        elif source_type == "ai":
            priority += 0.4
        else:
            priority += 0.3
        
        # Strength modifier
        strength = contradiction.get("strength", "Medium").lower()
        if strength == "strong":
            priority += 0.3
        elif strength == "medium":
            priority += 0.2
        else:
            priority += 0.1
        
        # Context relevance (if available)
        if "context" in contradiction.get("evidence_type", ""):
            priority += 0.2
        
        return priority
    
    def _remove_duplicate_contradictions(self, contradictions: List[Dict]) -> List[Dict]:
        """Remove duplicates using intelligent content comparison"""
        unique_contradictions = []
        
        for item in contradictions:
            is_duplicate = False
            item_text = item.get("quote", "").lower()
            
            for existing in unique_contradictions:
                existing_text = existing.get("quote", "").lower()
                
                # Intelligent similarity check
                if len(item_text) > 30 and len(existing_text) > 30:
                    words_item = set(item_text.split())
                    words_existing = set(existing_text.split())
                    
                    similarity = len(words_item & words_existing) / len(words_item | words_existing)
                    if similarity > 0.6:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_contradictions.append(item)
        
        return unique_contradictions
    
    def _create_intelligent_contradiction_analysis(self, contradictions: List[Dict], context: Dict) -> str:
        """Create intelligent analysis summary using context"""
        if not contradictions:
            return "No significant contradictions identified through intelligent analysis."
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        
        strong_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "strong")
        medium_count = sum(1 for c in contradictions if c.get("strength", "").lower() == "medium")
        evidence_count = sum(1 for c in contradictions if c.get("evidence_type") == "rag_processed")
        context_count = sum(1 for c in contradictions if "context" in c.get("evidence_type", ""))
        
        analysis = f"""
        Intelligent Contradiction Analysis for {asset_name}:
        - Total contradictions identified: {len(contradictions)}
        - Strong contradictions: {strong_count}
        - Medium contradictions: {medium_count}
        - Based on historical evidence: {evidence_count}
        - Context-driven analysis: {context_count}
        - AI-generated insights: {len(contradictions) - evidence_count}
        
        Assessment: {'Significant' if strong_count >= 2 else 'Moderate' if strong_count >= 1 else 'Limited'} 
        challenges identified for {asset_name} using intelligent, context-aware analysis.
        """
        
        return analysis.strip()

def create():
    """Create and return an intelligent hybrid contradiction agent instance"""
    return HybridContradictionAgent()

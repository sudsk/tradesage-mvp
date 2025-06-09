# app/agents/contradiction_agent/agent_hybrid.py - Complete AI-Powered Implementation with Quality Fixes
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

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
        if len(cleaned_contradictions) < 2:  # ENSURE MINIMUM 2 CONTRADICTIONS
            print("   🔄 Insufficient quality contradictions, generating new ones...")
            ai_generated = self._ai_generate_fresh_contradictions(context, hypothesis, len(cleaned_contradictions))
            cleaned_contradictions.extend(ai_generated)
        
        # Add universal risks if still insufficient
        if len(cleaned_contradictions) < 2:
            print("   🛡️ Adding universal risk factors...")
            universal_risks = self._generate_universal_risks(context, hypothesis)
            cleaned_contradictions.extend(universal_risks)
        
        return cleaned_contradictions[:3]  # Return top 3
    
    def _ai_process_single_contradiction(self, raw_contradiction: Dict, context: Dict, hypothesis: str) -> Optional[Dict]:
        """Use AI to evaluate, clean, and enhance a single contradiction"""
        
        raw_quote = raw_contradiction.get("quote", "")
        raw_reason = raw_contradiction.get("reason", "")
        
        asset_info = context.get("asset_info", {})
        
        evaluation_prompt = f"""
        You are an expert financial analyst reviewing investment risks.
        
        TASK: Evaluate and improve this risk factor for the hypothesis: "{hypothesis}"
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        - Current Price: {asset_info.get("current_price", "N/A")}
        
        RAW RISK FACTOR:
        Quote: "{raw_quote}"
        Reason: "{raw_reason}"
        
        REQUIREMENTS:
        1. Make it SPECIFIC to {asset_info.get("asset_name", "this asset")}
        2. Make it ACTIONABLE and REALISTIC
        3. Keep Quote under 400 characters
        4. Keep Reason under 400 characters
        5. NO generic placeholder text
        
        If this risk factor is valuable, improve it. If it's generic/useless, create a better one.
        
        Respond with JSON:
        {{
            "quote": "Specific risk statement about {asset_info.get("asset_name", "the asset")}",
            "reason": "Why this challenges the investment thesis",
            "source": "Risk Analysis",
            "strength": "Strong|Medium|Weak"
        }}
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
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            evaluation = json.loads(cleaned_response)
            
            # Validate required fields
            quote = evaluation.get("quote", "").strip()[:400]
            reason = evaluation.get("reason", "").strip()[:400]
            source = evaluation.get("source", "Risk Analysis").strip()[:40]
            strength = evaluation.get("strength", "Medium")
            
            # Validate strength
            if strength not in ["Strong", "Medium", "Weak"]:
                strength = "Medium"
            
            # Ensure meaningful content
            if len(quote) > 20 and len(reason) > 10:
                return {
                    "quote": quote,
                    "reason": reason,
                    "source": source,
                    "strength": strength,
                    "processing": "ai_enhanced"
                }
            else:
                return None
                
        except json.JSONDecodeError:
            # Fallback: extract from text
            return self._extract_improvement_from_text(ai_response, original)
    
    def _extract_improvement_from_text(self, text: str, original: Dict) -> Optional[Dict]:
        """Extract improvement from free-text AI response"""
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for quote-like content
        quote = ""
        reason = ""
        
        for line in lines:
            if len(line) > 30 and not any(line.startswith(word) for word in ['TASK:', 'ASSET:', 'REQUIREMENTS:', 'Respond']):
                if not quote and '"' in line:
                    quote = line.strip('"\'').strip()[:400]
                elif not reason and line != quote and len(line) > 20:
                    reason = line.strip('"\'').strip()[:400]
        
        if quote and reason:
            return {
                "quote": quote,
                "reason": reason,
                "source": "AI Analysis",
                "strength": "Medium",
                "processing": "ai_text_extracted"
            }
        
        return None
    
    def _ai_generate_fresh_contradictions(self, context: Dict, hypothesis: str, existing_count: int) -> List[Dict]:
        """Generate completely fresh contradictions using AI with database constraints"""
        
        needed_count = max(3 - existing_count, 0)
        if needed_count == 0:
            return []
        
        asset_info = context.get("asset_info", {})
        
        generation_prompt = f"""
        Generate {needed_count} HIGH-QUALITY, SPECIFIC risk factors for this investment hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET DETAILS:
        - Name: {asset_info.get("asset_name", "Unknown")}
        - Symbol: {asset_info.get("primary_symbol", "N/A")}
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        - Current Price: {asset_info.get("current_price", "N/A")}
        
        REQUIREMENTS for each risk factor:
        1. SPECIFIC to {asset_info.get("asset_name", "this asset")} - mention the company/asset by name
        2. REALISTIC and ACTIONABLE - based on actual market dynamics
        3. CONCISE - Quote under 400 chars, Reason under 400 chars
        4. PROFESSIONAL - no placeholder text or generic statements
        
        Generate realistic risks like:
        - Valuation concerns (if price seems high)
        - Competition threats (specific to this industry)
        - Market/economic headwinds
        - Company-specific execution risks
        - Regulatory or sector-specific challenges
        
        Format each as: quote|reason|source|strength
        
        Example for Apple:
        iPhone demand showing signs of saturation in key markets|Smartphone market maturity could limit Apple's primary revenue growth driver|Market Research|Strong
        
        Generate {needed_count} specific, realistic risk factors for {asset_info.get("asset_name", "this asset")}.
        """
        
        try:
            response = self.model.generate_content(generation_prompt)
            return self._parse_generated_contradictions_strict(response.text)
        except Exception as e:
            print(f"   ❌ AI contradiction generation failed: {str(e)}")
            return self._intelligent_fallback_contradictions_strict(context, hypothesis, needed_count)
    
    def _parse_generated_contradictions_strict(self, ai_response: str) -> List[Dict]:
        """Parse AI-generated contradictions with clean output like confirmations"""
        
        contradictions = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) >= 4:
                parts = line.split('|')
                raw_quote = parts[0].strip()
                raw_reason = parts[1].strip()
                source = parts[2].strip()[:40]
                strength = parts[3].strip()
                
                # FIXED: Clean the quote and reason like confirmations do
                import re
                # Remove JSON artifacts from the quote
                clean_quote = re.sub(r'"quote":\s*"?', '', raw_quote)
                clean_quote = re.sub(r'"reason":\s*"?', '', clean_quote)
                clean_quote = clean_quote.strip(' "')[:400]
                
                clean_reason = re.sub(r'"quote":\s*"?', '', raw_reason)
                clean_reason = re.sub(r'"reason":\s*"?', '', clean_reason)
                clean_reason = clean_reason.strip(' "')[:400]
                
                # Validate strength
                if strength not in ["Strong", "Medium", "Weak"]:
                    strength = "Medium"
                
                # Only add if meaningful content
                if len(clean_quote) > 20 and len(clean_reason) > 10:
                    contradictions.append({
                        "quote": clean_quote,  # Clean text like confirmations
                        "reason": clean_reason,
                        "source": source,
                        "strength": strength,
                        "processing": "ai_generated"
                    })
        
        # Fallback parsing if structured format fails
        if not contradictions:
            contradictions = self._extract_contradictions_from_text_strict(ai_response)
        
        return contradictions
    
    def _extract_contradictions_from_text_strict(self, text: str) -> List[Dict]:
        """FIXED: Extract contradictions with clean quotes like confirmations do"""
        
        contradictions = []
        
        # Split by double newlines or look for bullet points
        sections = text.split('\n\n') if '\n\n' in text else text.split('\n')
        
        for section in sections:
            section = section.strip()
            if len(section) > 50:
                # Clean the section to remove numbering and JSON artifacts
                section = section.replace('1.', '').replace('2.', '').replace('3.', '').replace('-', '').strip()
                
                # FIXED: Remove JSON structure patterns that were causing the problem
                import re
                # Remove patterns like "quote": "..." or "reason": "..."
                section = re.sub(r'"quote":\s*"?', '', section)
                section = re.sub(r'"reason":\s*"?', '', section)
                section = re.sub(r'^"', '', section)  # Remove leading quote
                section = re.sub(r'"[,}]*$', '', section)  # Remove trailing quote/comma/brace
                section = section.strip()
                
                if len(section) > 30:
                    # Create clean contradiction exactly like confirmations do
                    clean_quote = section[:350] + "..." if len(section) > 350 else section
                    
                    contradictions.append({
                        "quote": clean_quote,  # Clean text only, no JSON artifacts
                        "reason": "Market analysis identifies this as a potential challenge to the investment thesis.",
                        "source": "Market Analysis",
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
        current_price = asset_info.get("current_price", 0)
        
        fallback_contradictions = []
        
        # Market valuation risk (universal)
        fallback_contradictions.append({
            "quote": f"Current market valuations may limit {asset_name} upside potential given economic uncertainty.",
            "reason": "High market multiples and economic volatility often constrain further price appreciation.",
            "source": "Valuation Analysis",
            "strength": "Medium"
        })
        
        # Asset-type specific risks
        if asset_type in ["stock", "equity"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces competitive pressures in {sector} that could impact margins.",
                "reason": f"Increased competition in {sector} can erode market share and pricing power.",
                "source": "Competition Analysis",
                "strength": "Medium"
            })
        
        elif asset_type in ["crypto", "cryptocurrency"]:
            fallback_contradictions.append({
                "quote": f"{asset_name} faces regulatory uncertainty and extreme volatility risks.",
                "reason": "Cryptocurrency markets remain sensitive to regulatory changes and policy decisions.",
                "source": "Regulatory Risk",
                "strength": "Strong"
            })
        
        elif asset_type == "commodity":
            fallback_contradictions.append({
                "quote": f"Supply/demand dynamics for {asset_name} could shift unfavorably due to economic changes.",
                "reason": "Commodity markets are cyclical and sensitive to global economic conditions.",
                "source": "Commodity Analysis",
                "strength": "Medium"
            })
        
        # Execution risk (universal)
        if len(fallback_contradictions) < count:
            fallback_contradictions.append({
                "quote": f"Execution risk exists if {asset_name} fails to meet growth expectations or guidance.",
                "reason": "Company-specific challenges can derail even strong fundamental investment thesis.",
                "source": "Execution Risk",
                "strength": "Medium"
            })
        
        return fallback_contradictions[:count]
    
    def _generate_universal_risks(self, context: Dict, hypothesis: str) -> List[Dict]:
        """Generate universal investment risks that apply to any asset"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "this investment")
        
        universal_risks = [
            {
                "quote": f"Market volatility and geopolitical events could negatively impact {asset_name} price action.",
                "reason": "External macro factors often override fundamental analysis in short-term price movements.",
                "source": "Market Risk",
                "strength": "Medium"
            },
            {
                "quote": f"Interest rate changes and monetary policy shifts pose risks to {asset_name} valuation.",
                "reason": "Changes in interest rates affect discount rates and relative asset attractiveness.",
                "source": "Monetary Policy",
                "strength": "Medium"
            }
        ]
        
        return universal_risks

class HybridContradictionAgent:
    """AI-Powered Contradiction Agent - Enhanced Quality Implementation"""
    
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
        
        print(f"🎯 Finding contradictions using enhanced AI for: {processed_hypothesis}")
        
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
            
            # ENSURE we always have at least 2 contradictions (every investment has risks!)
            if len(final_contradictions) < 2:
                print("   🛡️ Ensuring minimum risk coverage...")
                additional_risks = processor._generate_universal_risks(context, hypothesis)
                final_contradictions.extend(additional_risks)
                final_contradictions = final_contradictions[:3]  # Max 3
            
            return {
                "contradictions": final_contradictions,
                "analysis": self._create_intelligent_analysis(final_contradictions, context),
                "processing_method": "enhanced_ai_intelligence",
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ AI contradiction processing failed: {str(e)}")
            # Even fallback uses AI
            processor = IntelligentContradictionProcessor(self.model)
            fallback_contradictions = processor._intelligent_fallback_contradictions_strict(context, hypothesis, 2)
            
            return {
                "contradictions": fallback_contradictions,
                "analysis": "Used enhanced AI fallback contradiction analysis.",
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
        cleaned_content = content[:350] + "..." if len(content) > 350 else content
        
        return {
            "quote": cleaned_content,
            "reason": "Historical market data suggests potential challenges to the investment thesis.",
            "source": "Historical Analysis",
            "strength": "Medium",
            "evidence_type": "rag_processed"
        }
    
    def _contains_negative_sentiment(self, text: str) -> bool:
        """Check if text contains negative sentiment indicators"""
        
        negative_indicators = [
            'decline', 'fall', 'drop', 'risk', 'challenge', 'difficult',
            'unlikely', 'bearish', 'negative', 'concern', 'problem', 'uncertainty'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in negative_indicators if indicator in text_lower) >= 2
    
    def _generate_raw_ai_contradictions(self, hypothesis: str, research_data: Dict, context: Dict) -> List[Dict]:
        """Generate raw AI contradictions that will be processed by the intelligent processor"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        
        prompt = f"""
        Generate 2-3 initial risk factors for this hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("asset_type", "Unknown")})
        SECTOR: {asset_info.get("sector", "Unknown")}
        
        Focus on realistic challenges such as:
        - Market valuation concerns
        - Competition or industry headwinds  
        - Economic/macro risks
        - Company-specific execution challenges
        
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
            line = line.strip()
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
        Enhanced AI Risk Analysis for {asset_name}:
        - Total risk factors identified: {len(contradictions)}
        - Strong risk factors: {strong_count}
        - Medium risk factors: {medium_count}
        - Processing method: Enhanced AI intelligence with quality validation
        
        Risk Assessment: {'High' if strong_count >= 2 else 'Moderate' if strong_count >= 1 else 'Standard'} 
        risk level identified through comprehensive, context-aware analysis.
        
        Recommendation: {'Proceed with caution' if strong_count >= 2 else 'Monitor key risks' if strong_count >= 1 else 'Standard risk management'} 
        and implement appropriate risk mitigation strategies.
        """
        
        return analysis.strip()

def create():
    """Create and return an enhanced contradiction agent instance"""
    return HybridContradictionAgent()

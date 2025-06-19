# app/adk/agents/contradiction_agent.py 
from google.adk.agents import Agent
from app.config.adk_config import AGENT_CONFIGS
from app.adk.tools import news_search
from app.adk.agents.model_integration import ADKModelIntegrator
from google.adk.sessions import InMemorySessionService
import json
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

# Smart system instruction 
SMART_CONTRADICTION_INSTRUCTION = """
You are the Contradiction Agent for TradeSage AI. Use intelligent analysis to generate DIVERSE, SPECIFIC contradictions.

Your approach:
1. Intelligently analyze the asset's business model and context
2. Generate diverse search strategies for different risk categories
3. Extract specific business risks from retrieved documents
4. Ensure contradictions cover different analytical perspectives

RISK CATEGORIES TO COVER:
- Business Model Risks (revenue streams, competitive moats)
- Regulatory/Policy Risks (government, compliance, legal)
- Competitive Risks (market share, disruption, new entrants)
- Execution Risks (management, guidance, operational)
- Macro/Economic Risks (rates, cycles, sector rotation)

Be SPECIFIC to the asset and use REAL business factors, not generic statements.
"""

class SmartContradictionProcessor:
    """Smart processor that dynamically generates diverse contradictions"""
    
    def __init__(self, model, hybrid_service=None):
        self.model = model
        self.hybrid_service = hybrid_service
    
    def process_contradictions(self, hypothesis: str, context: Dict, research_data: Dict) -> List[Dict]:
        """Process contradictions using smart, dynamic approach"""
        
        print("🧠 Using smart dynamic processing for contradictions...")
        
        # Step 1: Intelligently analyze the asset context
        asset_analysis = self._analyze_asset_context(context)
        
        # Step 2: Generate diverse search strategies based on analysis
        search_strategies = self._generate_smart_search_strategies(asset_analysis, hypothesis)
        
        # Step 3: Search for diverse evidence using RAG
        diverse_evidence = []
        if self.hybrid_service:
            diverse_evidence = self._search_diverse_evidence(search_strategies)
        
        # Step 4: Generate contradictions using evidence + AI
        contradictions = self._generate_diverse_contradictions(
            hypothesis, asset_analysis, diverse_evidence
        )
        
        # Step 5: Ensure diversity and quality
        final_contradictions = self._ensure_contradiction_diversity(contradictions)
        
        print(f"   ✅ Smart processing: {len(final_contradictions)} diverse contradictions")
        return final_contradictions
    
    def _analyze_asset_context(self, context: Dict) -> Dict[str, Any]:
        """Intelligently analyze asset context to understand business model"""
        
        asset_info = context.get("asset_info", {})
        
        analysis = {
            "asset_name": asset_info.get("asset_name", "Unknown"),
            "asset_type": asset_info.get("asset_type", "unknown"),
            "sector": asset_info.get("sector", "Unknown"),
            "business_model": asset_info.get("business_model", ""),
            "competitors": asset_info.get("competitors", []),
            "primary_symbol": asset_info.get("primary_symbol", ""),
            
            # Derived insights
            "is_tech_company": self._is_tech_company(asset_info),
            "is_consumer_facing": self._is_consumer_facing(asset_info),
            "is_regulated_industry": self._is_regulated_industry(asset_info),
            "has_platform_business": self._has_platform_business(asset_info),
            "revenue_model_type": self._identify_revenue_model(asset_info)
        }
        
        print(f"   📊 Asset analysis: {analysis['asset_name']} - {analysis['revenue_model_type']} in {analysis['sector']}")
        return analysis
    
    def _is_tech_company(self, asset_info: Dict) -> bool:
        """Check if asset is a technology company"""
        sector = asset_info.get("sector", "").lower()
        business_model = asset_info.get("business_model", "").lower()
        
        tech_indicators = ["technology", "software", "cloud", "ai", "digital", "internet", "platform"]
        return any(indicator in sector or indicator in business_model for indicator in tech_indicators)
    
    def _is_consumer_facing(self, asset_info: Dict) -> bool:
        """Check if asset has consumer-facing business"""
        business_model = asset_info.get("business_model", "").lower()
        sector = asset_info.get("sector", "").lower()
        
        consumer_indicators = ["consumer", "retail", "app store", "subscription", "brand", "customer"]
        return any(indicator in business_model or indicator in sector for indicator in consumer_indicators)
    
    def _is_regulated_industry(self, asset_info: Dict) -> bool:
        """Check if asset operates in heavily regulated industry"""
        sector = asset_info.get("sector", "").lower()
        asset_type = asset_info.get("asset_type", "").lower()
        
        regulated_indicators = ["financial", "healthcare", "energy", "utility", "bank", "insurance", "crypto"]
        return any(indicator in sector or indicator in asset_type for indicator in regulated_indicators)
    
    def _has_platform_business(self, asset_info: Dict) -> bool:
        """Check if asset has platform business model"""
        business_model = asset_info.get("business_model", "").lower()
        
        platform_indicators = ["platform", "marketplace", "app store", "ecosystem", "network"]
        return any(indicator in business_model for indicator in platform_indicators)
    
    def _identify_revenue_model(self, asset_info: Dict) -> str:
        """Identify the primary revenue model type"""
        business_model = asset_info.get("business_model", "").lower()
        sector = asset_info.get("sector", "").lower()
        
        if "subscription" in business_model or "saas" in business_model:
            return "subscription"
        elif "platform" in business_model or "marketplace" in business_model:
            return "platform"
        elif "advertising" in business_model or "ad" in business_model:
            return "advertising"
        elif "hardware" in business_model or "manufacturing" in sector:
            return "hardware"
        elif "services" in business_model:
            return "services"
        else:
            return "traditional"
    
    def _generate_smart_search_strategies(self, asset_analysis: Dict, hypothesis: str) -> Dict[str, str]:
        """Generate smart search strategies based on asset analysis"""
        
        asset_name = asset_analysis["asset_name"]
        asset_type = asset_analysis["asset_type"]
        sector = asset_analysis["sector"]
        
        strategies = {}
        
        # 1. Business Model Specific Risks
        revenue_model = asset_analysis["revenue_model_type"]
        if revenue_model == "subscription":
            strategies["subscription_risk"] = f"{asset_name} subscription churn retention growth"
        elif revenue_model == "platform":
            strategies["platform_risk"] = f"{asset_name} platform regulation antitrust policy"
        elif revenue_model == "advertising":
            strategies["advertising_risk"] = f"{asset_name} advertising revenue decline privacy"
        elif revenue_model == "hardware":
            strategies["hardware_risk"] = f"{asset_name} supply chain manufacturing cost"
        
        # 2. Technology Company Specific
        if asset_analysis["is_tech_company"]:
            strategies["tech_regulation"] = f"{asset_name} technology regulation antitrust big tech"
            strategies["tech_competition"] = f"{asset_name} technology disruption innovation competition"
        
        # 3. Consumer Facing Risks
        if asset_analysis["is_consumer_facing"]:
            strategies["consumer_sentiment"] = f"{asset_name} consumer sentiment brand reputation"
            strategies["market_saturation"] = f"{asset_name} market saturation user growth"
        
        # 4. Regulated Industry Risks
        if asset_analysis["is_regulated_industry"]:
            strategies["regulatory_change"] = f"{asset_name} regulatory change compliance cost"
            strategies["policy_risk"] = f"{asset_name} policy change government regulation"
        
        # 5. Sector Specific Risks
        strategies["sector_headwinds"] = f"{sector} sector headwinds challenges {asset_name}"
        strategies["competitive_pressure"] = f"{asset_name} competitive pressure market share"
        
        # 6. Economic/Macro Risks (universal)
        strategies["macro_headwinds"] = f"{asset_name} economic headwinds interest rates recession"
        
        print(f"   🎯 Generated {len(strategies)} smart search strategies")
        return strategies
    
    def _search_diverse_evidence(self, search_strategies: Dict[str, str]) -> List[Dict]:
        """Search for diverse evidence using smart strategies"""
        
        if not self.hybrid_service:
            return []
        
        all_evidence = []
        
        # Search with each strategy (limit to prevent overload)
        for strategy_name, query in list(search_strategies.items())[:5]:  # Top 5 strategies
            try:
                print(f"     📚 RAG search ({strategy_name}): {query}")
                
                # Run RAG search
                result = self._run_rag_search_sync(query)
                
                if result and result.get("historical_insights"):
                    for insight in result["historical_insights"][:2]:  # Top 2 per strategy
                        insight["strategy_type"] = strategy_name
                        insight["search_query"] = query
                        all_evidence.append(insight)
                
            except Exception as e:
                print(f"       ❌ Search failed for {strategy_name}: {str(e)}")
                continue
        
        print(f"     📊 Found {len(all_evidence)} pieces of evidence")
        return all_evidence
    
    def _run_rag_search_sync(self, query: str) -> Dict:
        """Run RAG search synchronously with timeout"""
        try:
            # Use thread pool for async RAG search
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_rag_in_loop, query)
                return future.result(timeout=8)
        except Exception as e:
            print(f"       ⚠️ RAG search failed: {str(e)}")
            return {}
    
    def _run_rag_in_loop(self, query: str) -> Dict:
        """Run RAG search in new event loop"""
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(
                    self.hybrid_service._rag_search(query, limit=3)
                )
            finally:
                new_loop.close()
        except Exception as e:
            return {}
    
    def _generate_diverse_contradictions(self, hypothesis: str, asset_analysis: Dict, 
                                       evidence: List[Dict]) -> List[Dict]:
        """Generate diverse contradictions using evidence + AI"""
        
        contradictions = []
        
        # Process evidence into contradictions
        for evidence_item in evidence:
            contradiction = self._process_evidence_to_contradiction(evidence_item, asset_analysis)
            if contradiction:
                contradictions.append(contradiction)
        
        # If not enough from evidence, generate AI contradictions
        if len(contradictions) < 3:
            ai_contradictions = self._generate_ai_contradictions(
                hypothesis, asset_analysis, 3 - len(contradictions)
            )
            contradictions.extend(ai_contradictions)
        
        return contradictions
    
    def _process_evidence_to_contradiction(self, evidence: Dict, asset_analysis: Dict) -> Optional[Dict]:
        """Process evidence into contradiction format"""
        
        content = evidence.get("full_content", "")
        strategy_type = evidence.get("strategy_type", "unknown")
        similarity = evidence.get("similarity", 0)
        asset_name = asset_analysis["asset_name"]
        
        # Quality filters
        if similarity < 0.3 or len(content) < 100:
            return None
        
        # Must mention asset or be relevant
        if asset_name.lower() not in content.lower() and similarity < 0.5:
            return None
        
        # Must have risk indicators
        if not self._has_risk_indicators(content):
            return None
        
        # Create contradiction with strategy-specific processing
        quote = content[:350] + "..." if len(content) > 350 else content
        
        # Map strategy to source and reason
        strategy_mapping = {
            "subscription_risk": ("Business Model", f"Subscription model challenges could impact {asset_name} recurring revenue growth."),
            "platform_risk": ("Regulatory Risk", f"Platform regulation could force {asset_name} to change business model."),
            "tech_regulation": ("Tech Regulation", f"Technology regulation could impose constraints on {asset_name} operations."),
            "consumer_sentiment": ("Brand Risk", f"Consumer sentiment shifts could affect {asset_name} market position."),
            "regulatory_change": ("Regulatory Risk", f"Regulatory changes could increase compliance costs for {asset_name}."),
            "sector_headwinds": ("Sector Analysis", f"Sector-wide challenges could pressure {asset_name} performance."),
            "competitive_pressure": ("Competition", f"Competitive pressures could erode {asset_name} market advantages.")
        }
        
        source, reason = strategy_mapping.get(strategy_type, ("Market Analysis", f"Market analysis suggests challenges for {asset_name}."))
        
        return {
            "quote": quote,
            "reason": reason[:400],
            "source": source[:40],
            "strength": "Strong" if similarity > 0.7 else "Medium",
            "strategy_type": strategy_type,
            "similarity": similarity
        }
    
    def _has_risk_indicators(self, content: str) -> bool:
        """Check if content has risk indicators"""
        content_lower = content.lower()
        
        risk_words = [
            "risk", "challenge", "threat", "concern", "pressure", "headwind", 
            "decline", "fall", "competition", "regulation", "uncertainty",
            "disruption", "weakness", "vulnerable", "problem"
        ]
        
        return sum(1 for word in risk_words if word in content_lower) >= 2
    
    def _generate_ai_contradictions(self, hypothesis: str, asset_analysis: Dict, count: int) -> List[Dict]:
        """Generate AI contradictions using smart prompting"""
        
        if count <= 0:
            return []
        
        asset_name = asset_analysis["asset_name"]
        asset_type = asset_analysis["asset_type"]
        sector = asset_analysis["sector"]
        revenue_model = asset_analysis["revenue_model_type"]
        
        # Smart prompt based on asset analysis
        prompt = f"""
        Generate {count} specific business risk factors for this investment hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET ANALYSIS:
        - Company: {asset_name}
        - Type: {asset_type} 
        - Sector: {sector}
        - Revenue Model: {revenue_model}
        - Tech Company: {asset_analysis["is_tech_company"]}
        - Consumer Facing: {asset_analysis["is_consumer_facing"]}
        - Regulated Industry: {asset_analysis["is_regulated_industry"]}
        
        Focus on SPECIFIC risks relevant to this business model:
        - Business model vulnerabilities
        - Sector-specific challenges  
        - Competitive threats
        - Regulatory/policy risks
        - Execution challenges
        
        Requirements:
        - Be specific to {asset_name} business
        - Under 400 characters each
        - Realistic and actionable
        - Different risk categories
        
        Format: quote|reason|source|strength
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_ai_contradictions(response.text)
        except Exception as e:
            print(f"   ❌ AI contradiction generation failed: {str(e)}")
            return self._get_smart_fallbacks(asset_analysis, count)
    
    def _parse_ai_contradictions(self, response: str) -> List[Dict]:
        """Parse AI contradictions from response"""
        
        contradictions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) >= 4:
                parts = line.split('|')
                
                quote = parts[0].strip()[:400]
                reason = parts[1].strip()[:400]
                source = parts[2].strip()[:40]
                strength = parts[3].strip()
                
                if strength not in ["Strong", "Medium", "Weak"]:
                    strength = "Medium"
                
                if len(quote) > 20 and len(reason) > 15:
                    contradictions.append({
                        "quote": quote,
                        "reason": reason,
                        "source": source,
                        "strength": strength,
                        "method": "ai_generated"
                    })
        
        return contradictions
    
    def _get_smart_fallbacks(self, asset_analysis: Dict, count: int) -> List[Dict]:
        """Get smart fallbacks based on asset analysis"""
        
        asset_name = asset_analysis["asset_name"]
        sector = asset_analysis["sector"]
        revenue_model = asset_analysis["revenue_model_type"]
        
        fallbacks = []
        
        # Business model specific fallback
        if revenue_model == "platform" and asset_analysis["is_tech_company"]:
            fallbacks.append({
                "quote": f"Regulatory scrutiny on platform businesses could impact {asset_name} operations and revenue model.",
                "reason": f"Platform regulation trends pose risks to {asset_name} business model flexibility.",
                "source": "Regulatory Risk",
                "strength": "Strong"
            })
        
        # Competitive fallback
        if asset_analysis["is_consumer_facing"]:
            fallbacks.append({
                "quote": f"Increasing competition in {sector} could pressure {asset_name} market share and pricing power.",
                "reason": f"Competitive dynamics may limit {asset_name} ability to maintain market position.",
                "source": "Competition",
                "strength": "Medium"
            })
        
        # Universal fallback
        fallbacks.append({
            "quote": f"Economic headwinds and interest rate environment present challenges for {asset_name} valuation.",
            "reason": f"Macroeconomic factors could constrain {asset_name} growth and investment flows.",
            "source": "Economic Risk",
            "strength": "Medium"
        })
        
        return fallbacks[:count]
    
    def _ensure_contradiction_diversity(self, contradictions: List[Dict]) -> List[Dict]:
        """Ensure contradictions are diverse across categories"""
        
        if len(contradictions) <= 3:
            return contradictions[:3]
        
        # Group by strategy type / source
        by_category = {}
        for contradiction in contradictions:
            category = contradiction.get("strategy_type") or contradiction.get("source", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(contradiction)
        
        # Select best from each category
        diverse_contradictions = []
        for category, group in by_category.items():
            # Sort by similarity or quality
            group.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            diverse_contradictions.append(group[0])
            
            if len(diverse_contradictions) >= 3:
                break
        
        return diverse_contradictions[:3]

class SmartContradictionAgent:
    """Smart contradiction agent with dynamic processing (no hardcoding)"""
    
    def __init__(self):
        try:
            import vertexai
            from vertexai.preview.generative_models import GenerativeModel
            
            vertexai.init(project="tradesage-mvp", location="us-central1")
            self.model = GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=SMART_CONTRADICTION_INSTRUCTION
            )
            
            # Initialize RAG service
            self._initialize_hybrid_service()
            
        except Exception as e:
            print(f"Error initializing Smart Contradiction Agent: {e}")
            self.model = None
            self.hybrid_service = None
    
    def _initialize_hybrid_service(self):
        """Initialize the hybrid RAG service"""
        try:
            from app.services.hybrid_rag_service import get_hybrid_rag_service
            self.hybrid_service = get_hybrid_rag_service()
            print("✅ RAG service connected to Smart Contradiction Agent")
        except Exception as e:
            print(f"⚠️  RAG service initialization failed: {str(e)}")
            self.hybrid_service = None
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method using smart, dynamic approach"""
        
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        research_data = input_data.get("research_data", {})
        context = input_data.get("context", {})
        
        print(f"🎯 Smart contradiction processing for: {processed_hypothesis}")
        
        try:
            # Initialize smart processor
            processor = SmartContradictionProcessor(self.model, self.hybrid_service)
            
            # Process using smart, dynamic approach
            contradictions = processor.process_contradictions(
                processed_hypothesis, context, research_data
            )
            
            return {
                "contradictions": contradictions,
                "analysis": self._create_analysis(contradictions, context),
                "processing_method": "smart_dynamic",
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Smart contradiction processing failed: {str(e)}")
            
            # Simple fallback
            fallback_contradictions = self._get_simple_fallbacks(context)
            
            return {
                "contradictions": fallback_contradictions,
                "analysis": "Used smart fallback analysis based on asset context.",
                "processing_method": "smart_fallback",
                "status": "error_fallback"
            }
    
    def _get_simple_fallbacks(self, context: Dict) -> List[Dict]:
        """Get simple fallbacks when processing fails"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        sector = asset_info.get("sector", "Unknown")
        
        return [
            {
                "quote": f"Competitive pressures in {sector} could impact {asset_name} market position and pricing power.",
                "reason": f"Industry competition may limit {asset_name} ability to maintain competitive advantages.",
                "source": "Competition",
                "strength": "Medium"
            },
            {
                "quote": f"Regulatory changes and policy shifts present risks to {asset_name} business operations.",
                "reason": f"Policy developments could create operational headwinds for {asset_name}.",
                "source": "Regulatory Risk",
                "strength": "Medium"
            },
            {
                "quote": f"Economic uncertainty and market volatility challenge {asset_name} investment thesis.",
                "reason": "Macroeconomic factors could affect discount rates and investment flows.",
                "source": "Economic Risk", 
                "strength": "Medium"
            }
        ]
    
    def _create_analysis(self, contradictions: List[Dict], context: Dict) -> str:
        """Create analysis summary"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        asset_name = asset_info.get("asset_name", "the asset")
        
        strategy_types = [c.get("strategy_type", "unknown") for c in contradictions]
        sources = [c.get("source", "Unknown") for c in contradictions]
        
        analysis = f"""
        Smart Dynamic Risk Analysis for {asset_name}:
        - Risk categories analyzed: {len(set(strategy_types))} unique areas
        - Sources: {', '.join(set(sources))}
        - Processing method: Context-aware dynamic generation
        - Business model considerations: Integrated
        
        Assessment: Smart analysis identified diverse business risks using
        dynamic search strategies tailored to the asset's specific business model
        and market context, without hardcoded company patterns.
        """
        
        return analysis.strip()

def create_contradiction_agent() -> Agent:
    """Create the smart dynamic contradiction agent."""
    config = AGENT_CONFIGS["contradiction_agent"]
    
    return Agent(
        name=config["name"],
        model=config["model"],
        description=config["description"],
        instruction=SMART_CONTRADICTION_INSTRUCTION,
        tools=[news_search],
    )

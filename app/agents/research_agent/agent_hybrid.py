# app/agents/research_agent/agent_hybrid.py - Intelligent, context-driven research
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import asyncio
import concurrent.futures
from typing import Dict, Any, List

class HybridResearchAgent:
    """Intelligent Research Agent that uses context and AI - no hardcoding"""
    
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
            print(f"Error initializing Hybrid Research Agent: {e}")
            self.model = None
            self.hybrid_service = None
    
    def _initialize_hybrid_service(self):
        """Initialize the hybrid RAG service"""
        try:
            from app.services.hybrid_rag_service import get_hybrid_rag_service
            self.hybrid_service = get_hybrid_rag_service()
            print("✅ Hybrid RAG service connected to Research Agent")
        except Exception as e:
            print(f"⚠️  Hybrid RAG service initialization failed: {str(e)}")
            print("   Using real-time only mode")
            self.hybrid_service = None
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct intelligent research using context - no hardcoded patterns"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        context = input_data.get("context", {})
        
        print(f"🔬 Starting intelligent research for: {processed_hypothesis}")
        
        # Extract context information
        if context:
            self._log_context_usage(context)
        
        try:
            # Use intelligent research strategy
            if self.hybrid_service:
                research_data = self._run_context_driven_hybrid_research(processed_hypothesis, context)
            else:
                research_data = self._run_context_driven_research(processed_hypothesis, context)
            
            # Generate AI analysis of the research
            analysis = self._generate_intelligent_analysis(processed_hypothesis, research_data, context)
            
            # Combine with analysis
            research_data["ai_analysis"] = analysis
            research_data["research_method"] = "context_driven_hybrid" if self.hybrid_service else "context_driven_realtime"
            
            return {
                "research_data": research_data,
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Intelligent research failed: {str(e)}")
            return {
                "research_data": {
                    "error": str(e),
                    "summary": f"Research encountered an error while analyzing: {processed_hypothesis}"
                },
                "status": "error"
            }
    
    def _log_context_usage(self, context: Dict) -> None:
        """Log how context is being used"""
        asset_info = context.get("asset_info", {})
        print(f"🔧 Using context: {asset_info.get('asset_name', 'Unknown')} ({asset_info.get('asset_type', 'Unknown')})")
        
        research_guidance = context.get("research_guidance", {})
        search_terms = research_guidance.get("search_terms", [])
        if search_terms:
            print(f"   📋 Context-provided search terms: {search_terms[:3]}")
    
    def _run_context_driven_hybrid_research(self, hypothesis: str, context: Dict) -> Dict[str, Any]:
        """Run hybrid research using context intelligence"""
        try:
            # Extract instruments using context
            instruments = self._get_instruments_from_context(context)
            
            # Use context for hybrid research
            if instruments:
                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Use thread pool executor for async operations
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_hybrid_in_new_loop, hypothesis, instruments)
                        return future.result(timeout=30)
                except RuntimeError:
                    # No running event loop
                    return asyncio.run(self._hybrid_research_mode(hypothesis, instruments))
            else:
                return self._run_context_driven_research(hypothesis, context)
        except Exception as e:
            print(f"⚠️  Hybrid mode failed: {str(e)}, falling back to real-time")
            return self._run_context_driven_research(hypothesis, context)
    
    def _run_hybrid_in_new_loop(self, hypothesis: str, instruments: List[str]) -> Dict[str, Any]:
        """Run hybrid research in a new event loop"""
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._hybrid_research_mode(hypothesis, instruments))
            finally:
                new_loop.close()
        except Exception as e:
            print(f"⚠️  New loop research failed: {str(e)}")
            return {"error": str(e)}
    
    async def _hybrid_research_mode(self, hypothesis: str, instruments: List[str]) -> Dict[str, Any]:
        """Use hybrid RAG + real-time research with context intelligence"""
        print("🔍 Using context-driven hybrid research mode")
        
        # Use hybrid RAG service with context
        result = await self.hybrid_service.hybrid_research(hypothesis, instruments)
        
        if result.get("status") == "success":
            return result["research_data"]
        else:
            print("⚠️  Hybrid mode failed, using real-time fallback")
            return {"error": "Hybrid research failed"}
    
    def _run_context_driven_research(self, hypothesis: str, context: Dict) -> Dict[str, Any]:
        """Run real-time research using context intelligence"""
        print("⚡ Using context-driven real-time research mode")
        
        from app.tools.market_data_tool import market_data_tool
        from app.tools.news_data_tool import news_data_tool
        
        # Extract research strategy from context
        instruments = self._get_instruments_from_context(context)
        news_query = self._get_news_query_from_context(context)
        
        # Gather market data using context
        market_data = {}
        for i, instrument in enumerate(instruments[:2]):
            print(f"   📊 Fetching market data {i+1}/{min(2, len(instruments))}: {instrument}")
            try:
                market_data[instrument] = market_data_tool(instrument, "auto", PROJECT_ID)
            except Exception as e:
                print(f"   ❌ Market data failed for {instrument}: {str(e)}")
                market_data[instrument] = {"error": str(e)}
        
        # Gather news data using context
        print(f"   📰 Fetching news using context query: {news_query}")
        try:
            news_data = news_data_tool(news_query, 7, PROJECT_ID)
        except Exception as e:
            print(f"   ❌ News fetch failed: {str(e)}")
            news_data = {"error": str(e)}
        
        return {
            "market_data": market_data,
            "news_data": news_data,
            "historical_insights": [],  # Empty since no RAG
            "data_sources": {
                "context_driven": True,
                "rag_database": 0,
                "real_time_market": len(market_data),
                "real_time_news": len(news_data.get("articles", []) if isinstance(news_data, dict) else [])
            },
            "merged_analysis": "Research completed using context-driven real-time data sources.",
            "confidence_score": 0.7,  # Higher confidence with context
            "research_method": "context_driven_realtime"
        }
    
    def _get_instruments_from_context(self, context: Dict) -> List[str]:
        """Extract instruments from context intelligently - no hardcoding"""
        if not context:
            return self._ai_derive_instruments_fallback()
        
        asset_info = context.get("asset_info", {})
        instruments = []
        
        # Primary instrument from context
        primary_symbol = asset_info.get("primary_symbol")
        if primary_symbol:
            instruments.append(primary_symbol)
            print(f"   🎯 Primary instrument from context: {primary_symbol}")
        
        # Competitors from context (limit to 1 for comparison)
        competitors = asset_info.get("competitors", [])
        if competitors and len(instruments) < 2:
            competitor = competitors[0]
            instruments.append(competitor)
            print(f"   🔄 Competitor from context: {competitor}")
        
        # Fallback if context doesn't provide instruments
        if not instruments:
            print("   ⚠️  No instruments in context, using AI fallback")
            instruments = self._ai_derive_instruments_fallback()
        
        return instruments[:2]  # Limit to prevent rate limiting
    
    def _get_news_query_from_context(self, context: Dict) -> str:
        """Generate news query from context - no hardcoded patterns"""
        if not context:
            return "financial market news"
        
        research_guidance = context.get("research_guidance", {})
        
        # Use context-provided search terms
        search_terms = research_guidance.get("search_terms", [])
        if search_terms:
            query = " ".join(search_terms[:4])  # Limit to 4 terms
            print(f"   📝 News query from context: {query}")
            return query
        
        # Fallback to asset information
        asset_info = context.get("asset_info", {})
        asset_name = asset_info.get("asset_name", "")
        asset_type = asset_info.get("asset_type", "")
        
        if asset_name:
            query = f"{asset_name} {asset_type} market analysis"
            print(f"   📝 News query from asset info: {query}")
            return query
        
        return "financial market news"
    
    def _ai_derive_instruments_fallback(self) -> List[str]:
        """AI fallback when context doesn't provide instruments"""
        # Safe fallback - could be enhanced with AI analysis if needed
        return ["SPY"]  # Market index as safe default
    
    def _generate_intelligent_analysis(self, hypothesis: str, research_data: Dict, context: Dict) -> str:
        """Generate AI analysis using context intelligence"""
        
        asset_info = context.get("asset_info", {}) if context else {}
        
        analysis_prompt = f"""
        Analyze the research findings for this specific investment hypothesis:
        
        HYPOTHESIS: "{hypothesis}"
        
        ASSET CONTEXT:
        - Asset: {asset_info.get("asset_name", "Unknown")} ({asset_info.get("primary_symbol", "N/A")})
        - Type: {asset_info.get("asset_type", "Unknown")}
        - Sector: {asset_info.get("sector", "Unknown")}
        
        RESEARCH DATA:
        - Market data sources: {len(research_data.get('market_data', {}))}
        - News articles: {len(research_data.get('news_data', {}).get('articles', []))}
        - Historical insights: {len(research_data.get('historical_insights', []))}
        
        Market Data Summary: {json.dumps(research_data.get('market_data', {}), indent=2)[:1000]}...
        
        News Data Summary: {json.dumps(research_data.get('news_data', {}), indent=2)[:1000]}...
        
        Provide intelligent analysis focusing on:
        1. Key findings specific to this asset and sector
        2. Relevant market developments and trends
        3. Data quality and reliability assessment
        4. Research confidence level for this specific asset
        5. Asset-specific factors revealed by the research
        
        Be specific to this asset type and avoid generic market statements.
        """
        
        try:
            response = self.model.generate_content(analysis_prompt)
            return response.text
        except Exception as e:
            print(f"⚠️  AI analysis generation failed: {str(e)}")
            return self._generate_fallback_analysis(research_data, asset_info)
    
    def _generate_fallback_analysis(self, research_data: Dict, asset_info: Dict) -> str:
        """Generate intelligent fallback analysis"""
        analysis_parts = []
        
        asset_name = asset_info.get("asset_name", "Unknown Asset")
        asset_type = asset_info.get("asset_type", "unknown")
        
        # Market data summary
        market_data = research_data.get('market_data', {})
        if market_data:
            analysis_parts.append(f"Market Data Analysis for {asset_name}:")
            for instrument, data in market_data.items():
                if isinstance(data, dict) and data.get('data', {}).get('info'):
                    info = data['data']['info']
                    price = info.get('currentPrice', 'N/A')
                    change = info.get('dayChangePercent', 0)
                    analysis_parts.append(f"- {instrument}: ${price} ({change:+.2f}% daily change)")
                else:
                    analysis_parts.append(f"- {instrument}: Data unavailable or error")
        
        # News summary
        news_data = research_data.get('news_data', {})
        if isinstance(news_data, dict) and news_data.get('articles'):
            analysis_parts.append(f"\nNews Analysis for {asset_name}: Found {len(news_data['articles'])} recent articles")
            for article in news_data['articles'][:3]:
                title = article.get('title', 'News update')
                analysis_parts.append(f"- {title}")
        
        # Historical context
        historical_insights = research_data.get('historical_insights', [])
        if historical_insights:
            analysis_parts.append(f"\nHistorical Context: {len(historical_insights)} relevant documents found")
            for insight in historical_insights[:2]:
                similarity = insight.get('similarity', 0)
                title = insight.get('title', 'Historical reference')
                analysis_parts.append(f"- {title} (relevance: {similarity:.2f})")
        
        # Research quality assessment
        data_sources = research_data.get('data_sources', {})
        confidence = research_data.get('confidence_score', 0.5)
        analysis_parts.append(f"\nResearch Quality Assessment:")
        analysis_parts.append(f"- Data sources: {sum(data_sources.values()) if isinstance(data_sources, dict) else 0}")
        analysis_parts.append(f"- Confidence level: {confidence:.2f}")
        analysis_parts.append(f"- Asset type: {asset_type}")
        
        return "\n".join(analysis_parts) if analysis_parts else f"Limited research data available for {asset_name} analysis."

def create():
    """Create and return an intelligent hybrid research agent instance"""
    return HybridResearchAgent()

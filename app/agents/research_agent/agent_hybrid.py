# app/agents/research_agent/agent_hybrid.py
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import asyncio
from typing import Dict, Any, List

class HybridResearchAgent:
    """Enhanced Research Agent that uses both RAG database and real-time APIs"""
    
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
            print("   Falling back to basic real-time only mode")
            self.hybrid_service = None
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct hybrid research using both RAG and real-time data"""
        if not self.model:
            return {"error": "Model not initialized"}
        
        hypothesis = input_data.get("hypothesis", "")
        processed_hypothesis = input_data.get("processed_hypothesis", hypothesis)
        
        print(f"🔬 Starting hybrid research for: {processed_hypothesis}")
        
        try:
            # Use hybrid research if available, otherwise fall back to basic mode
            if self.hybrid_service:
                research_data = asyncio.run(
                    self._hybrid_research_mode(processed_hypothesis)
                )
            else:
                research_data = self._fallback_research_mode(processed_hypothesis)
            
            # Generate AI analysis of the research
            analysis = self._generate_analysis(processed_hypothesis, research_data)
            
            # Combine with analysis
            research_data["ai_analysis"] = analysis
            research_data["research_method"] = "hybrid" if self.hybrid_service else "real_time_only"
            
            return {
                "research_data": research_data,
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Hybrid research failed: {str(e)}")
            return {
                "research_data": {
                    "error": str(e),
                    "summary": f"Research encountered an error while analyzing: {processed_hypothesis}"
                },
                "status": "error"
            }
    
    async def _hybrid_research_mode(self, hypothesis: str) -> Dict[str, Any]:
        """Use hybrid RAG + real-time research"""
        print("🔍 Using hybrid research mode (RAG + Real-time)")
        
        # Extract instruments for targeted research
        instruments = self._extract_instruments(hypothesis)
        
        # Use hybrid RAG service
        result = await self.hybrid_service.hybrid_research(hypothesis, instruments)
        
        if result.get("status") == "success":
            return result["research_data"]
        else:
            # If hybrid failed, fall back to basic mode
            print("⚠️  Hybrid mode failed, falling back to real-time only")
            return self._fallback_research_mode(hypothesis)
    
    def _fallback_research_mode(self, hypothesis: str) -> Dict[str, Any]:
        """Fallback to real-time only research"""
        print("⚡ Using real-time only research mode")
        
        from app.tools.market_data_tool import market_data_tool
        from app.tools.news_data_tool import news_data_tool
        
        # Extract instruments
        instruments = self._extract_instruments(hypothesis)
        
        # Gather market data
        market_data = {}
        for i, instrument in enumerate(instruments[:2]):
            print(f"   📊 Fetching market data {i+1}/{min(2, len(instruments))}: {instrument}")
            try:
                market_data[instrument] = market_data_tool(instrument, "auto", PROJECT_ID)
            except Exception as e:
                print(f"   ❌ Market data failed for {instrument}: {str(e)}")
                market_data[instrument] = {"error": str(e)}
        
        # Gather news data
        news_query = self._create_news_query(hypothesis)
        print(f"   📰 Fetching news for: {news_query}")
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
                "rag_database": 0,
                "real_time_market": len(market_data),
                "real_time_news": len(news_data.get("articles", []))
            },
            "merged_analysis": "Research completed using real-time data sources only.",
            "confidence_score": 0.6,  # Lower confidence without historical context
            "research_method": "real_time_fallback"
        }
    
    def _generate_analysis(self, hypothesis: str, research_data: Dict[str, Any]) -> str:
        """Generate AI analysis of the research findings"""
        
        # Create analysis prompt
        prompt = f"""
        Analyze the following research data for the hypothesis: "{hypothesis}"
        
        Research Data Summary:
        - Historical insights: {len(research_data.get('historical_insights', []))} documents
        - Market data sources: {len(research_data.get('market_data', {}))}
        - News articles: {len(research_data.get('news_data', {}).get('articles', []))}
        
        Market Data: {json.dumps(research_data.get('market_data', {}), indent=2)[:1000]}...
        
        News Data: {json.dumps(research_data.get('news_data', {}), indent=2)[:1000]}...
        
        Historical Context: {research_data.get('merged_analysis', 'No historical context available')}
        
        Please provide:
        1. Key findings from market data
        2. Important news developments
        3. Historical patterns (if available)
        4. Data quality assessment
        5. Research confidence level
        
        Focus on factual analysis without making investment recommendations.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️  AI analysis generation failed: {str(e)}")
            return self._generate_fallback_analysis(research_data)
    
    def _generate_fallback_analysis(self, research_data: Dict[str, Any]) -> str:
        """Generate a basic analysis if AI generation fails"""
        analysis_parts = []
        
        # Market data summary
        market_data = research_data.get('market_data', {})
        if market_data:
            analysis_parts.append("Market Data Summary:")
            for instrument, data in market_data.items():
                if data.get('data', {}).get('info'):
                    info = data['data']['info']
                    price = info.get('currentPrice', 'N/A')
                    change = info.get('dayChangePercent', 0)
                    analysis_parts.append(f"- {instrument}: ${price} ({change:+.2f}% daily change)")
        
        # News summary
        news_data = research_data.get('news_data', {})
        if news_data.get('articles'):
            analysis_parts.append(f"\nNews Analysis: Found {len(news_data['articles'])} recent articles")
            for article in news_data['articles'][:3]:
                analysis_parts.append(f"- {article.get('title', 'News update')}")
        
        # Historical context
        historical_insights = research_data.get('historical_insights', [])
        if historical_insights:
            analysis_parts.append(f"\nHistorical Context: {len(historical_insights)} relevant documents found")
            for insight in historical_insights[:2]:
                similarity = insight.get('similarity', 0)
                analysis_parts.append(f"- {insight.get('title', 'Historical reference')} (relevance: {similarity:.2f})")
        
        return "\n".join(analysis_parts) if analysis_parts else "Limited research data available for analysis."
    
    def _extract_instruments(self, hypothesis: str) -> List[str]:
        """Extract financial instruments from hypothesis"""
        import re
        
        instruments = []
        
        # Cryptocurrency patterns
        if re.search(r'bitcoin|btc', hypothesis.lower()):
            instruments.append('BTC-USD')
        if re.search(r'ethereum|eth', hypothesis.lower()):
            instruments.append('ETH-USD')
        
        # Stock patterns
        stock_matches = re.findall(r'\$([A-Z]{1,5})', hypothesis)
        instruments.extend(stock_matches)
        
        # Default fallbacks
        if not instruments:
            if 'bitcoin' in hypothesis.lower() or 'crypto' in hypothesis.lower():
                instruments = ['BTC-USD']
            elif 'oil' in hypothesis.lower():
                instruments = ['CL=F']  # Crude oil futures
            else:
                instruments = ['SPY']  # Default to S&P 500
        
        return instruments[:2]  # Limit to prevent rate limiting
    
    def _create_news_query(self, hypothesis: str) -> str:
        """Create targeted news search query"""
        if 'bitcoin' in hypothesis.lower() or 'crypto' in hypothesis.lower():
            return 'cryptocurrency bitcoin market news'
        elif 'oil' in hypothesis.lower():
            return 'oil price energy market OPEC'
        elif any(term in hypothesis.lower() for term in ['stock', 'market', 'sp500']):
            return 'stock market financial news'
        else:
            return 'financial market news'

def create():
    """Create and return a hybrid research agent instance"""
    return HybridResearchAgent()

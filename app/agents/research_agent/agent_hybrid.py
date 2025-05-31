# app/agents/research_agent/agent_hybrid.py
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import MODEL_NAME, GENERATION_CONFIG, PROJECT_ID, LOCATION
from .prompt import SYSTEM_INSTRUCTION
import json
import asyncio
import concurrent.futures
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
                research_data = self._run_hybrid_research(processed_hypothesis)
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
    
    def _run_hybrid_research(self, hypothesis: str) -> Dict[str, Any]:
        """Run hybrid research handling async/sync context properly"""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we get here, we're in a running event loop
                # Use a thread pool executor to run the async code
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_research_in_new_loop, hypothesis)
                    return future.result(timeout=30)  # 30 second timeout
            except RuntimeError:
                # No running event loop, we can use asyncio.run()
                return asyncio.run(self._hybrid_research_mode(hypothesis))
        except Exception as e:
            print(f"⚠️  Hybrid mode failed: {str(e)}, falling back to real-time only")
            return self._fallback_research_mode(hypothesis)
    
    def _run_research_in_new_loop(self, hypothesis: str) -> Dict[str, Any]:
        """Run research in a completely new event loop"""
        try:
            # Create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._hybrid_research_mode(hypothesis))
            finally:
                new_loop.close()
        except Exception as e:
            print(f"⚠️  New loop research failed: {str(e)}")
            return self._fallback_research_mode(hypothesis)
    
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
                "real_time_news": len(news_data.get("articles", []) if isinstance(news_data, dict) else [])
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
                if isinstance(data, dict) and data.get('data', {}).get('info'):
                    info = data['data']['info']
                    price = info.get('currentPrice', 'N/A')
                    change = info.get('dayChangePercent', 0)
                    analysis_parts.append(f"- {instrument}: ${price} ({change:+.2f}% daily change)")
        
        # News summary
        news_data = research_data.get('news_data', {})
        if isinstance(news_data, dict) and news_data.get('articles'):
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
        """Extract financial instruments from hypothesis with better company name mapping"""
        import re
        
        instruments = []
        
        # Company name to ticker mapping
        company_mappings = {
            'apple': 'AAPL',
            'microsoft': 'MSFT', 
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'nvidia': 'NVDA',
            'meta': 'META',
            'facebook': 'META',
            'netflix': 'NFLX',
            'salesforce': 'CRM',
            'oracle': 'ORCL',
            'adobe': 'ADBE',
            'intel': 'INTC',
            'amd': 'AMD',
            'uber': 'UBER',
            'airbnb': 'ABNB',
            'spotify': 'SPOT',
            'zoom': 'ZM',
            'slack': 'WORK',
            'twitter': 'TWTR',
            'snap': 'SNAP',
            'pinterest': 'PINS'
        }
        
        # Check for company names first
        hypothesis_lower = hypothesis.lower()
        for company, ticker in company_mappings.items():
            if company in hypothesis_lower:
                instruments.append(ticker)
                break  # Take the first match
        
        # Cryptocurrency patterns
        if re.search(r'bitcoin|btc', hypothesis_lower):
            instruments.append('BTC-USD')
        elif re.search(r'ethereum|eth', hypothesis_lower):
            instruments.append('ETH-USD')
        
        # Explicit ticker patterns: $AAPL or (AAPL)
        ticker_patterns = [
            r'\$([A-Z]{2,5})',           # $AAPL
            r'\(([A-Z]{2,5})\)',         # (AAPL) 
            r'\b([A-Z]{2,5})\b'          # AAPL (standalone)
        ]
        
        for pattern in ticker_patterns:
            matches = re.findall(pattern, hypothesis)
            for match in matches:
                if len(match) >= 2 and match not in ['USD', 'THE', 'AND', 'FOR', 'ARE', 'WILL']:
                    instruments.append(match)
        
        # Oil and commodities
        if 'oil' in hypothesis_lower:
            instruments.append('CL=F')  # Crude oil futures
        elif 'gold' in hypothesis_lower:
            instruments.append('GLD')   # Gold ETF
        
        # Remove duplicates
        instruments = list(dict.fromkeys(instruments))  # Preserves order
        
        # Default fallbacks if nothing found
        if not instruments:
            if 'crypto' in hypothesis_lower:
                instruments = ['BTC-USD']
            elif 'stock' in hypothesis_lower or 'market' in hypothesis_lower:
                instruments = ['SPY']
            else:
                instruments = ['SPY']  # Ultimate fallback
        
        print(f"🎯 Extracted instruments for '{hypothesis[:50]}...': {instruments}")
        return instruments[:2]  # Limit to prevent rate limiting
    
    def _create_news_query(self, hypothesis: str) -> str:
        """Create targeted news search query based on the original simple hypothesis"""
        # Use the original simple input, not the processed verbose version
        hypothesis_lower = hypothesis.lower()
        
        # Company-specific queries
        if 'apple' in hypothesis_lower:
            return 'Apple AAPL stock earnings revenue'
        elif 'microsoft' in hypothesis_lower:
            return 'Microsoft MSFT stock cloud azure'
        elif 'google' in hypothesis_lower or 'alphabet' in hypothesis_lower:
            return 'Google Alphabet GOOGL stock advertising'
        elif 'amazon' in hypothesis_lower:
            return 'Amazon AMZN stock AWS ecommerce'
        elif 'tesla' in hypothesis_lower:
            return 'Tesla TSLA stock electric vehicles'
        elif 'nvidia' in hypothesis_lower:
            return 'Nvidia NVDA stock AI chips'
        elif 'meta' in hypothesis_lower or 'facebook' in hypothesis_lower:
            return 'Meta Facebook META stock social media'
        
        # Crypto queries
        elif 'bitcoin' in hypothesis_lower or 'btc' in hypothesis_lower:
            return 'bitcoin cryptocurrency market price'
        elif 'ethereum' in hypothesis_lower or 'eth' in hypothesis_lower:
            return 'ethereum cryptocurrency market price'
        elif 'crypto' in hypothesis_lower:
            return 'cryptocurrency market news'
        
        # Commodity queries  
        elif 'oil' in hypothesis_lower:
            return 'oil price energy market OPEC crude'
        elif 'gold' in hypothesis_lower:
            return 'gold price precious metals market'
        
        # General market
        elif any(term in hypothesis_lower for term in ['stock', 'market', 'sp500', 'nasdaq']):
            return 'stock market financial news'
        else:
            return 'financial market news'

def create():
    """Create and return a hybrid research agent instance"""
    return HybridResearchAgent()

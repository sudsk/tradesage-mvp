# app/services/hybrid_rag_service.py - Fixed for FastAPI compatibility
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configuration
PROJECT_ID = "tradesage-mvp"
REGION = "us-central1"
INSTANCE_NAME = "agentic-db"
DATABASE_NAME = "tradesage_db"
DB_USER = "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD", "your-secure-password")

class HybridRAGService:
    """
    Hybrid RAG Service that combines:
    1. Historical RAG database for foundational knowledge
    2. Real-time APIs for latest market data and news
    3. Intelligent routing based on query type and recency needs
    """
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.region = REGION
        
        # Initialize Vertex AI
        try:
            vertexai.init(project=PROJECT_ID, location=REGION)
            self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        except Exception as e:
            print(f"⚠️  Vertex AI initialization failed: {str(e)}")
            self.embedding_model = None
        
        # Database connection
        self.connector = None
        self.connection = None
        self._connect_to_database()
        
        # Real-time service imports
        self._initialize_real_time_services()
        
        print("✅ Hybrid RAG Service initialized")
        print(f"   - Vector database: {'Connected' if self.connection else 'Failed'}")
        print(f"   - Real-time APIs: Ready")
        print(f"   - Embedding model: {'Available' if self.embedding_model else 'Failed'}")
    
    def _connect_to_database(self):
        """Connect to the Cloud SQL vector database"""
        try:
            from google.cloud.sql.connector import Connector
            self.connector = Connector()
            self.connection = self.connector.connect(
                f"{self.project_id}:{self.region}:{INSTANCE_NAME}",
                "pg8000",
                user=DB_USER,
                password=DB_PASSWORD,
                db=DATABASE_NAME
            )
            print("✅ Connected to vector database")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            self.connection = None
    
    def _initialize_real_time_services(self):
        """Initialize real-time data services"""
        try:
            # Import your existing tools
            from app.tools.market_data_tool import market_data_tool
            from app.tools.news_data_tool import news_data_tool
            
            self.market_data_tool = market_data_tool
            self.news_data_tool = news_data_tool
            print("✅ Real-time services initialized")
        except Exception as e:
            print(f"⚠️  Real-time services initialization warning: {str(e)}")
            self.market_data_tool = None
            self.news_data_tool = None
    
    async def hybrid_research(self, hypothesis: str, instruments: List[str] = None) -> Dict[str, Any]:
        """
        Main hybrid research method that combines RAG and real-time data
        
        Args:
            hypothesis: The trading hypothesis to research
            instruments: List of financial instruments to focus on
            
        Returns:
            Combined research data from both sources
        """
        print(f"🔍 Starting hybrid research for: {hypothesis}")
        
        try:
            # Step 1: Search for data in RAG database
            rag_results = await self._rag_search(hypothesis)
            
            # Step 2: Fetch real-time data
            real_time_results = await self._real_time_search(hypothesis, instruments or [])
            
            # Step 3: Merge and prioritize results
            merged_results = self._merge_results(rag_results, real_time_results, hypothesis)
            
            print(f"✅ Hybrid research completed")
            print(f"   - RAG insights: {len(rag_results.get('historical_insights', []))}")
            print(f"   - Real-time sources: {len(real_time_results.get('market_data', {}))}")
            
            return merged_results
            
        except Exception as e:
            print(f"❌ Hybrid research failed: {str(e)}")
            return {
                "error": str(e),
                "historical_insights": [],
                "market_data": {},
                "news_data": {},
                "merged_analysis": "Research failed due to technical error",
                "status": "error"
            }
    
    async def _rag_search(self, hypothesis: str, limit: int = 10) -> Dict[str, Any]:
        """Search the historical RAG database"""
        if not self.connection or not self.embedding_model:
            return {"historical_insights": [], "error": "Database or embedding service not available"}
        
        try:
            print("📚 Searching RAG database...")
            
            # Generate embedding for hypothesis
            query_embedding = self.embedding_model.get_embeddings([hypothesis])[0].values
            embedding_list = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
            embedding_str = '[' + ','.join(map(str, embedding_list)) + ']'
            
            # Search with different similarity thresholds
            thresholds = [0.4, 0.3, 0.2]  # Start with higher quality, fall back if needed
            
            for threshold in thresholds:
                cursor = self.connection.cursor()
                try:
                    query = """
                        SELECT 
                            title,
                            content,
                            instrument,
                            source_type,
                            date_published,
                            1 - (embedding <=> %s) AS similarity
                        FROM documents
                        WHERE 1 - (embedding <=> %s) >= %s
                        ORDER BY embedding <=> %s
                        LIMIT %s;
                    """
                    
                    cursor.execute(query, [embedding_str, embedding_str, threshold, embedding_str, limit])
                    results = cursor.fetchall()
                    
                    if results:
                        print(f"   Found {len(results)} results with threshold {threshold}")
                        break
                        
                finally:
                    cursor.close()
            else:
                results = []
            
            # Format results
            historical_insights = []
            for row in results:
                title, content, instrument, source_type, date_published, similarity = row
                
                historical_insights.append({
                    "title": title,
                    "content_preview": content[:300] + "..." if len(content) > 300 else content,
                    "full_content": content,
                    "instrument": instrument,
                    "source": source_type,
                    "date": str(date_published) if date_published else "Unknown",
                    "similarity": float(similarity),
                    "data_source": "rag_database"
                })
            
            return {
                "historical_insights": historical_insights,
                "search_query": hypothesis,
                "total_found": len(historical_insights)
            }
            
        except Exception as e:
            print(f"❌ RAG search error: {str(e)}")
            return {"historical_insights": [], "error": str(e)}
    
    async def _real_time_search(self, hypothesis: str, instruments: List[str]) -> Dict[str, Any]:
        """Fetch real-time market data and news"""
        print("⚡ Fetching real-time data...")
        
        # Extract instruments from hypothesis if not provided
        if not instruments:
            instruments = self._extract_instruments(hypothesis)
        
        market_data = {}
        news_data = {}
        
        try:
            # Fetch market data for each instrument
            if self.market_data_tool:
                for instrument in instruments[:3]:  # Limit to avoid rate limits
                    try:
                        print(f"   📊 Fetching market data for {instrument}")
                        data = self.market_data_tool(instrument, "auto", self.project_id)
                        market_data[instrument] = data
                    except Exception as e:
                        print(f"   ⚠️  Market data failed for {instrument}: {str(e)}")
                        market_data[instrument] = {"error": str(e)}
            
            # Fetch recent news
            if self.news_data_tool:
                try:
                    news_query = self._create_news_query(hypothesis)
                    print(f"   📰 Fetching news for: {news_query}")
                    news_data = self.news_data_tool(news_query, 7, self.project_id)
                except Exception as e:
                    print(f"   ⚠️  News fetch failed: {str(e)}")
                    news_data = {"error": str(e)}
            
            return {
                "market_data": market_data,
                "news_data": news_data,
                "instruments": instruments,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Real-time search error: {str(e)}")
            return {"market_data": {}, "news_data": {}, "error": str(e)}
    
    def _merge_results(self, rag_results: Dict, real_time_results: Dict, hypothesis: str) -> Dict[str, Any]:
        """Intelligently merge RAG and real-time results"""
        
        # Determine data recency needs
        is_breaking_news_query = any(term in hypothesis.lower() for term in 
                                   ['today', 'latest', 'current', 'breaking', 'recent'])
        
        # Create comprehensive analysis
        analysis_sections = []
        
        # Start with real-time data if query needs current info
        if is_breaking_news_query and real_time_results.get("news_data"):
            analysis_sections.append("🚨 **Latest Developments:**")
            news_data = real_time_results["news_data"]
            if isinstance(news_data, dict) and "articles" in news_data:
                for article in news_data["articles"][:3]:
                    analysis_sections.append(f"- {article.get('title', 'News update')}")
        
        # Add market data context
        if real_time_results.get("market_data"):
            analysis_sections.append("📊 **Current Market Data:**")
            for instrument, data in real_time_results["market_data"].items():
                if isinstance(data, dict) and data.get("data", {}).get("info"):
                    info = data["data"]["info"]
                    price = info.get("currentPrice", "N/A")
                    change = info.get("dayChangePercent", 0)
                    analysis_sections.append(f"- {instrument}: ${price} ({change:+.2f}%)")
        
        # Add historical context from RAG
        if rag_results.get("historical_insights"):
            analysis_sections.append("📚 **Historical Context:**")
            for insight in rag_results["historical_insights"][:3]:
                similarity = insight.get("similarity", 0)
                analysis_sections.append(f"- {insight['title']} (relevance: {similarity:.2f})")
        
        # Determine confidence based on data quality
        confidence_factors = []
        
        if rag_results.get("historical_insights"):
            avg_similarity = sum(h.get("similarity", 0) for h in rag_results["historical_insights"]) / len(rag_results["historical_insights"])
            confidence_factors.append(avg_similarity * 0.4)  # 40% weight for historical relevance
        
        if real_time_results.get("market_data") and not any("error" in str(v) for v in real_time_results["market_data"].values()):
            confidence_factors.append(0.3)  # 30% weight for current market data
        
        if real_time_results.get("news_data") and isinstance(real_time_results["news_data"], dict) and real_time_results["news_data"].get("articles"):
            confidence_factors.append(0.3)  # 30% weight for recent news
        
        overall_confidence = sum(confidence_factors) if confidence_factors else 0.1
        
        return {
            "research_data": {
                "historical_insights": rag_results.get("historical_insights", []),
                "market_data": real_time_results.get("market_data", {}),
                "news_data": real_time_results.get("news_data", {}),
                "merged_analysis": "\n".join(analysis_sections) if analysis_sections else "Limited data available for analysis",
                "data_sources": {
                    "rag_database": len(rag_results.get("historical_insights", [])),
                    "real_time_market": len(real_time_results.get("market_data", {})),
                    "real_time_news": len(real_time_results.get("news_data", {}).get("articles", []) if isinstance(real_time_results.get("news_data"), dict) else [])
                },
                "confidence_score": min(overall_confidence, 1.0),
                "timestamp": datetime.now().isoformat()
            },
            "status": "success"
        }
    
    def _extract_instruments(self, hypothesis: str) -> List[str]:
        """Extract financial instruments from hypothesis text"""
        import re
        
        instruments = []
        
        # Cryptocurrency patterns
        crypto_patterns = [
            r'(?:bitcoin|btc)[-\s]*(?:usd)?',
            r'(?:ethereum|eth)[-\s]*(?:usd)?',
        ]
        
        for pattern in crypto_patterns:
            if re.search(pattern, hypothesis.lower()):
                if 'bitcoin' in pattern or 'btc' in pattern:
                    instruments.append('BTC-USD')
                elif 'ethereum' in pattern or 'eth' in pattern:
                    instruments.append('ETH-USD')
        
        # Stock patterns
        stock_patterns = [
            r'\$([A-Z]{1,5})',  # $AAPL
            r'\b([A-Z]{2,5})\b'  # AAPL
        ]
        
        for pattern in stock_patterns:
            matches = re.findall(pattern, hypothesis)
            instruments.extend(matches)
        
        # Default fallbacks
        if not instruments:
            if 'bitcoin' in hypothesis.lower() or 'crypto' in hypothesis.lower():
                instruments = ['BTC-USD']
            elif 'stock' in hypothesis.lower() or 'market' in hypothesis.lower():
                instruments = ['SPY']
            else:
                instruments = ['SPY']
        
        return list(set(instruments))[:2]  # Limit to 2 instruments
    
    def _create_news_query(self, hypothesis: str) -> str:
        """Create targeted news search query"""
        if 'bitcoin' in hypothesis.lower() or 'crypto' in hypothesis.lower():
            return 'cryptocurrency bitcoin market news'
        elif 'oil' in hypothesis.lower():
            return 'oil price energy market'
        else:
            return 'financial market news'
    
    def close(self):
        """Close database connections"""
        if self.connection:
            self.connection.close()
        if self.connector:
            self.connector.close()

# Singleton instance
_hybrid_rag_service = None

def get_hybrid_rag_service() -> HybridRAGService:
    """Get or create the hybrid RAG service singleton"""
    global _hybrid_rag_service
    if _hybrid_rag_service is None:
        _hybrid_rag_service = HybridRAGService()
    return _hybrid_rag_service

# Convenience function for async usage
async def hybrid_research(hypothesis: str, instruments: List[str] = None) -> Dict[str, Any]:
    """Convenience function for hybrid research"""
    service = get_hybrid_rag_service()
    return await service.hybrid_research(hypothesis, instruments)

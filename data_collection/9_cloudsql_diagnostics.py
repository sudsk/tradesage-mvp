# cloudsql_diagnostics.py
import os
import json
from corpus_processor_cloudsql import CloudSQLVectorDB, create_query_function
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configuration
PROJECT_ID = "tradesage-mvp"
REGION = "us-central1" 
INSTANCE_NAME = "agentic-db"
DATABASE_NAME = "tradesage_db"
DB_USER = "postgres"
DB_PASSWORD = "your-secure-password"  # Update with your password

def test_similarity_thresholds():
    """Test different similarity thresholds to find optimal settings"""
    print("🔍 Testing Similarity Thresholds")
    print("=" * 50)
    
    # Connect to database
    db = CloudSQLVectorDB(PROJECT_ID, REGION, INSTANCE_NAME, DATABASE_NAME, DB_USER, DB_PASSWORD)
    if not db.connect():
        print("❌ Could not connect to database")
        return
    
    # Initialize embedding model
    vertexai.init(project=PROJECT_ID, location=REGION)
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    # Test queries
    test_queries = [
        "Apple quarterly earnings",
        "market volatility trends", 
        "Tesla stock performance",
        "cryptocurrency analysis",
        "financial market news"
    ]
    
    # Test different thresholds
    thresholds = [0.5, 0.4, 0.3, 0.2, 0.1, 0.0]
    
    for query in test_queries:
        print(f"\n📊 Query: '{query}'")
        print("-" * 40)
        
        # Generate embedding
        query_embedding = embedding_model.get_embeddings([query])[0].values
        embedding_list = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
        
        for threshold in thresholds:
            results = db.semantic_search(
                query_embedding=embedding_list,
                limit=3,
                similarity_threshold=threshold
            )
            
            if results:
                print(f"   Threshold {threshold}: {len(results)} results")
                best_similarity = max(result['similarity'] for result in results)
                print(f"     Best similarity: {best_similarity:.3f}")
                break
        else:
            print(f"   No results found even with threshold 0.0")
    
    db.close()

def analyze_document_content():
    """Analyze what types of content we actually have"""
    print("\n📋 Document Content Analysis")
    print("=" * 50)
    
    # Connect to database
    db = CloudSQLVectorDB(PROJECT_ID, REGION, INSTANCE_NAME, DATABASE_NAME, DB_USER, DB_PASSWORD)
    if not db.connect():
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = db.connection.cursor()
        
        # Get sample titles by instrument
        cursor.execute("""
            SELECT instrument, title, LEFT(content, 100) as content_preview
            FROM documents 
            WHERE title IS NOT NULL 
            ORDER BY instrument, created_at DESC
            LIMIT 20;
        """)
        
        results = cursor.fetchall()
        
        print("Sample document titles and content:")
        current_instrument = None
        for row in results:
            instrument, title, content_preview = row
            if instrument != current_instrument:
                print(f"\n📈 {instrument}:")
                current_instrument = instrument
            print(f"   - {title[:60]}...")
            print(f"     Content: {content_preview}...")
        
        # Get content keywords analysis
        cursor.execute("""
            SELECT 
                instrument,
                COUNT(*) as doc_count,
                AVG(LENGTH(content)) as avg_content_length,
                COUNT(CASE WHEN title ILIKE '%earnings%' THEN 1 END) as earnings_docs,
                COUNT(CASE WHEN title ILIKE '%analysis%' THEN 1 END) as analysis_docs,
                COUNT(CASE WHEN content ILIKE '%quarterly%' THEN 1 END) as quarterly_content
            FROM documents 
            GROUP BY instrument
            ORDER BY doc_count DESC;
        """)
        
        stats = cursor.fetchall()
        
        print(f"\n📊 Content Statistics by Instrument:")
        print(f"{'Instrument':<12} {'Docs':<5} {'Avg Length':<10} {'Earnings':<8} {'Analysis':<8} {'Quarterly':<9}")
        print("-" * 70)
        
        for row in stats:
            instrument, doc_count, avg_length, earnings, analysis, quarterly = row
            print(f"{instrument:<12} {doc_count:<5} {int(avg_length):<10} {earnings:<8} {analysis:<8} {quarterly:<9}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error analyzing content: {str(e)}")
    
    db.close()

def test_specific_searches():
    """Test searches with lower thresholds"""
    print("\n🔍 Testing Searches with Lower Thresholds")
    print("=" * 50)
    
    # Connect to database
    db = CloudSQLVectorDB(PROJECT_ID, REGION, INSTANCE_NAME, DATABASE_NAME, DB_USER, DB_PASSWORD)
    if not db.connect():
        print("❌ Could not connect to database")
        return
    
    # Create query function
    vertexai.init(project=PROJECT_ID, location=REGION)
    query_func = create_query_function(db)
    
    # Test with lower similarity thresholds
    test_cases = [
        {
            "query": "Apple quarterly earnings",
            "thresholds": [0.6, 0.5, 0.4, 0.3],
            "expected": "Should find Apple-related financial content"
        },
        {
            "query": "market volatility",
            "thresholds": [0.6, 0.5, 0.4, 0.3],
            "expected": "Should find market analysis content"
        },
        {
            "query": "stock price",
            "thresholds": [0.6, 0.5, 0.4, 0.3],
            "expected": "Should find stock-related content"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 Query: '{test_case['query']}'")
        print(f"   Expected: {test_case['expected']}")
        
        for threshold in test_case['thresholds']:
            print(f"\n   Threshold {threshold}:")
            
            results = query_func(
                test_case['query'],
                num_results=3,
                similarity_threshold=threshold
            )
            
            if results:
                print(f"     ✅ Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"       {i}. {result['title'][:50]}...")
                    print(f"          Similarity: {result['similarity']:.3f}, Instrument: {result['instrument']}")
                break
        else:
            print(f"     ❌ No results found with any threshold")
    
    db.close()

def interactive_search_with_debug():
    """Interactive search with debug information"""
    print("\n🔍 Interactive Search with Debug Info")
    print("=" * 50)
    print("Commands:")
    print("  - Type search query")
    print("  - 'stats' for database stats") 
    print("  - 'quit' to exit")
    
    # Connect to database
    db = CloudSQLVectorDB(PROJECT_ID, REGION, INSTANCE_NAME, DATABASE_NAME, DB_USER, DB_PASSWORD)
    if not db.connect():
        print("❌ Could not connect to database")
        return
    
    # Create query function
    vertexai.init(project=PROJECT_ID, location=REGION)
    query_func = create_query_function(db)
    
    while True:
        print("\n" + "-" * 40)
        user_input = input("🔍 Search: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if user_input.lower() == 'stats':
            stats = db.get_stats()
            if stats:
                print(f"\n📊 Database Stats:")
                print(f"   Total docs: {stats['stats']['total_documents']}")
                print(f"   Instruments: {stats['stats']['unique_instruments']}")
                print(f"   Sources: {stats['stats']['unique_sources']}")
            continue
        
        if not user_input:
            continue
        
        print(f"\n🔍 Searching for: '{user_input}'")
        
        # Try different thresholds automatically
        thresholds = [0.6, 0.5, 0.4, 0.3, 0.2]
        
        for threshold in thresholds:
            results = query_func(
                user_input,
                num_results=5,
                similarity_threshold=threshold
            )
            
            if results:
                print(f"\n✅ Found {len(results)} results (threshold: {threshold})")
                for result in results:
                    print(f"\n{result['rank']}. {result['title']}")
                    print(f"   Similarity: {result['similarity']:.3f}")
                    print(f"   Instrument: {result['instrument']}")
                    print(f"   Source: {result['source_type']}")
                    print(f"   Preview: {result['content_preview'][:150]}...")
                break
        else:
            print("❌ No results found with any threshold")
    
    db.close()
    print("👋 Search session ended.")

def main():
    """Run diagnostics and optimization"""
    print("🔧 Cloud SQL Vector Search Diagnostics & Optimization")
    print("=" * 60)
    
    # Run all diagnostic tests
    test_similarity_thresholds()
    analyze_document_content()
    test_specific_searches()
    
    # Offer interactive search
    print(f"\n🎯 Recommendations:")
    print(f"   1. Use similarity threshold 0.3-0.4 for better recall")
    print(f"   2. Your documents seem to be primarily news and technical analysis")
    print(f"   3. Search for broader terms like 'stock', 'price', 'market' for better results")
    
    if input(f"\n🔍 Start interactive search with debug? (y/N): ").lower() == 'y':
        interactive_search_with_debug()

if __name__ == "__main__":
    main()

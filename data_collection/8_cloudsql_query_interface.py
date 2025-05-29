# cloudsql_query_interface.py
import json
import os
from corpus_processor_cloudsql import CloudSQLVectorDB, create_query_function
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configuration
PROJECT_ID = "your-gcp-project-id"
REGION = "us-central1"
INSTANCE_NAME = "tradesage-postgres"
DATABASE_NAME = "tradesage_db"
DB_USER = "postgres"
DB_PASSWORD = "your-secure-password"

def load_metadata():
    """Load the latest Cloud SQL metadata"""
    metadata_files = [f for f in os.listdir("processed_corpus") if f.startswith("cloudsql_metadata_")]
    if not metadata_files:
        return None
    
    latest = sorted(metadata_files)[-1]
    with open(f"processed_corpus/{latest}", 'r') as f:
        return json.load(f)

def test_database_connection():
    """Test connection to Cloud SQL database"""
    print("🔌 Testing database connection...")
    
    db = CloudSQLVectorDB(PROJECT_ID, REGION, INSTANCE_NAME, DATABASE_NAME, DB_USER, DB_PASSWORD)
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return None
    
    # Get stats to verify data exists
    stats = db.get_stats()
    if stats and stats['stats']['total_documents'] > 0:
        print(f"✅ Connected successfully!")
        print(f"   Total documents: {stats['stats']['total_documents']}")
        print(f"   Unique instruments: {stats['stats']['unique_instruments']}")
        return db
    else:
        print("❌ Database connected but no documents found")
        return None

def run_comprehensive_tests(query_func):
    """Run comprehensive tests on the Cloud SQL vector search"""
    print("\n🧪 Running Comprehensive Tests...")
    
    test_queries = [
        {
            "query": "Bitcoin price analysis",
            "description": "Crypto analysis query"
        },
        {
            "query": "Apple quarterly earnings report",
            "description": "Company earnings query"
        },
        {
            "query": "market volatility and risk assessment",
            "description": "Market analysis query"
        },
        {
            "query": "oil price forecast OPEC",
            "description": "Commodity analysis query"
        },
        {
            "query": "technical analysis chart patterns",
            "description": "Technical analysis query"
        }
    ]
    
    test_results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n   Test {i}: {test['description']}")
        print(f"   Query: '{test['query']}'")
        
        try:
            # Test basic search
            results = query_func(test['query'], num_results=3)
            
            if results:
                print(f"   ✅ Found {len(results)} results")
                for j, result in enumerate(results, 1):
                    print(f"      {j}. {result['title'][:50]}...")
                    print(f"         Similarity: {result['similarity']:.3f}, "
                          f"Instrument: {result['instrument']}, "
                          f"Source: {result['source_type']}")
                
                test_results.append({"test": test['description'], "status": "PASS", "count": len(results)})
            else:
                print(f"   ❌ No results found")
                test_results.append({"test": test['description'], "status": "FAIL", "count": 0})
                
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            test_results.append({"test": test['description'], "status": "ERROR", "error": str(e)})
    
    # Test filtered searches
    print(f"\n   Testing filtered searches...")
    
    # Test instrument filter
    try:
        results = query_func("recent analysis", num_results=2, instrument_filter="AAPL")
        if results:
            print(f"   ✅ Instrument filter (AAPL): {len(results)} results")
        else:
            print(f"   ⚠️  Instrument filter returned no results")
    except Exception as e:
        print(f"   ❌ Instrument filter test failed: {str(e)}")
    
    # Test source filter
    try:
        results = query_func("financial news", num_results=2, source_filter="news")
        if results:
            print(f"   ✅ Source filter (news): {len(results)} results")
        else:
            print(f"   ⚠️  Source filter returned no results")
    except Exception as e:
        print(f"   ❌ Source filter test failed: {str(e)}")
    
    # Summary
    print(f"\n📊 Test Summary:")
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    total = len(test_results)
    
    for result in test_results:
        status = result["status"]
        emoji = "✅" if status == "PASS" else "❌"
        print(f"   {emoji} {result['test']}: {status}")
        if status == "PASS":
            print(f"      Found {result['count']} results")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    return passed > 0

def interactive_search(query_func, db):
    """Interactive search interface for Cloud SQL"""
    print("\n🔍 Interactive Cloud SQL Vector Search")
    print("=" * 50)
    print("Commands:")
    print("  - Type your search query and press Enter")
    print("  - 'stats' to show database statistics")
    print("  - 'instruments' to list available instruments")
    print("  - 'sources' to list available source types")
    print("  - 'quit' or 'exit' to stop")
    
    while True:
        print("\n" + "-" * 40)
        user_input = input("🔍 Search query: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if user_input.lower() == 'stats':
            stats = db.get_stats()
            if stats:
                print(f"\n📊 Database Statistics:")
                print(f"   Total documents: {stats['stats']['total_documents']}")
                print(f"   Unique instruments: {stats['stats']['unique_instruments']}")
                print(f"   Unique sources: {stats['stats']['unique_sources']}")
                print(f"   Date range: {stats['stats']['earliest_document']} to {stats['stats']['latest_document']}")
            continue
        
        if user_input.lower() == 'instruments':
            stats = db.get_stats()
            if stats:
                print(f"\n📈 Available Instruments:")
                for item in stats['instrument_distribution']:
                    print(f"   - {item['instrument']}: {item['count']} documents")
            continue
        
        if user_input.lower() == 'sources':
            # Get source distribution
            try:
                with db.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT source_type, COUNT(*) as count
                        FROM documents
                        GROUP BY source_type
                        ORDER BY count DESC;
                    """)
                    source_counts = cursor.fetchall()
                    
                    print(f"\n📰 Available Source Types:")
                    for source_type, count in source_counts:
                        print(f"   - {source_type}: {count} documents")
            except Exception as e:
                print(f"❌ Error getting sources: {str(e)}")
            continue
        
        if not user_input:
            continue
        
        # Optional filters
        print("Optional filters (press Enter to skip):")
        instrument = input("  Filter by instrument: ").strip()
        source = input("  Filter by source type: ").strip()
        similarity = input("  Minimum similarity (0.0-1.0, default 0.6): ").strip()
        
        try:
            similarity_threshold = float(similarity) if similarity else 0.6
        except ValueError:
            similarity_threshold = 0.6
        
        # Perform search
        try:
            results = query_func(
                user_input,
                num_results=5,
                instrument_filter=instrument if instrument else None,
                source_filter=source if source else None,
                similarity_threshold=similarity_threshold
            )
            
            if results:
                print(f"\n📊 Found {len(results)} results:")
                for result in results:
                    print(f"\n{result['rank']}. {result['title']}")
                    print(f"   Similarity: {result['similarity']:.3f}")
                    print(f"   Instrument: {result['instrument']}")
                    print(f"   Source: {result['source_type']}")
                    print(f"   Date: {result['date']}")
                    print(f"   Preview: {result['content_preview'][:200]}...")
                    
                    # Ask if user wants to see full content
                    if input("   Show full content? (y/N): ").lower() == 'y':
                        # Get full content from database
                        try:
                            with db.connection.cursor() as cursor:
                                cursor.execute("SELECT content FROM documents WHERE id = %s", (result['id'],))
                                full_content = cursor.fetchone()[0]
                                print(f"\n   Full Content:\n{full_content}\n")
                        except Exception as e:
                            print(f"   ❌ Error fetching full content: {str(e)}")
            else:
                print("❌ No results found")
                print("💡 Try:")
                print("   - Using different keywords")
                print("   - Lowering the similarity threshold")
                print("   - Removing filters")
                
        except Exception as e:
            print(f"❌ Search error: {str(e)}")

def compare_performance(query_func, db):
    """Compare performance with different similarity thresholds"""
    print("\n⚡ Performance Comparison")
    print("=" * 40)
    
    test_query = "Bitcoin price analysis"
    thresholds = [0.8, 0.7, 0.6, 0.5]
    
    print(f"Testing query: '{test_query}'")
    
    for threshold in thresholds:
        try:
            import time
            start_time = time.time()
            
            results = query_func(
                test_query,
                num_results=10,
                similarity_threshold=threshold
            )
            
            end_time = time.time()
            query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            print(f"   Threshold {threshold}: {len(results)} results in {query_time:.2f}ms")
            
        except Exception as e:
            print(f"   Threshold {threshold}: Error - {str(e)}")

def setup_cloud_sql_instructions():
    """Print setup instructions for Cloud SQL"""
    print("""
🏗️  Cloud SQL Setup Instructions:

1. Create Cloud SQL PostgreSQL instance:
   gcloud sql instances create tradesage-postgres \\
     --database-version=POSTGRES_14 \\
     --tier=db-g1-small \\
     --region=us-central1 \\
     --storage-type=SSD \\
     --storage-size=20GB

2. Set password for postgres user:
   gcloud sql users set-password postgres \\
     --instance=tradesage-postgres \\
     --password=your-secure-password

3. Create database:
   gcloud sql databases create tradesage_db \\
     --instance=tradesage-postgres

4. Install required Python packages:
   pip install psycopg2-binary pg8000 google-cloud-sql-connector

5. Enable the pgvector extension (this script will do it automatically)

💰 Cost Estimate:
   - db-g1-small: ~$25-50/month
   - 20GB SSD: ~$4/month
   - Total: ~$30-55/month (much cheaper than Vector Search!)

🚀 Performance:
   - Query time: 50-200ms (vs 10-50ms for Vector Search)
   - Highly scalable with proper indexing
   - Can handle millions of documents
""")

def main():
    """Main function for Cloud SQL query interface"""
    print("🚀 TradeSage Cloud SQL Vector Search Interface")
    print("=" * 60)
    
    # Check if we have metadata (indicating setup was completed)
    metadata = load_metadata()
    if not metadata:
        print("❌ No Cloud SQL metadata found!")
        print("💡 Please run corpus_processor_cloudsql.py first")
        setup_cloud_sql_instructions()
        return
    
    print(f"✅ Found metadata for database: {metadata.get('database_name')}")
    print(f"   Documents: {metadata.get('total_documents', 'unknown')}")
    print(f"   Created: {metadata.get('created_at', 'unknown')}")
    
    # Test database connection
    db = test_database_connection()
    if not db:
        print("❌ Cannot connect to database")
        setup_cloud_sql_instructions()
        return
    
    # Initialize Vertex AI for embeddings
    vertexai.init(project=PROJECT_ID, location=REGION)
    
    # Create query function
    query_func = create_query_function(db)
    
    # Run tests
    print("\n🧪 Running system tests...")
    if run_comprehensive_tests(query_func):
        print("\n✅ All tests passed! System is ready.")
        
        # Performance comparison
        compare_performance(query_func, db)
        
        # Interactive search
        interactive_search(query_func, db)
    else:
        print("\n❌ Some tests failed. Please check your setup.")
    
    # Close database connection
    db.close()
    print("\n👋 Database connection closed.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
        if len(sys.argv) > 2:
            INSTANCE_NAME = sys.argv[2]
        print(f"Using project ID: {PROJECT_ID}")
        print(f"Using instance name: {INSTANCE_NAME}")
    
    main()

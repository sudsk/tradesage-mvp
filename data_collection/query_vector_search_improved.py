# query_vector_search_improved.py
import json
import os
import time
from google.cloud import aiplatform
from google.cloud import storage
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configuration - UPDATE THESE VALUES
PROJECT_ID = "your-gcp-project-id"  # Update with your project ID
LOCATION = "us-central1"

# Initialize
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project=PROJECT_ID, location=LOCATION)

def load_deployment_metadata():
    """Load deployment metadata to get endpoint and index info"""
    metadata_files = []
    if os.path.exists("processed_corpus"):
        metadata_files = [f for f in os.listdir("processed_corpus") if f.startswith("vector_search_metadata_")]
    
    if not metadata_files:
        print("❌ No metadata files found. Please check your deployment.")
        return None
    
    # Use the most recent metadata file
    latest_metadata = sorted(metadata_files)[-1]
    metadata_path = f"processed_corpus/{latest_metadata}"
    
    print(f"📄 Loading metadata from: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    return metadata

def load_document_metadata(metadata):
    """Load document metadata for result enrichment"""
    bucket_name = metadata.get("bucket_name")
    uid = metadata.get("uid")
    
    if not bucket_name or not uid:
        print("⚠️  Missing bucket or UID in metadata")
        return {}
    
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"metadata/documents_{uid}.jsonl")
        
        if not blob.exists():
            print("⚠️  Document metadata file not found in GCS")
            return {}
        
        content = blob.download_as_text()
        doc_lookup = {}
        
        for line in content.strip().split('\n'):
            if line:
                doc = json.loads(line)
                doc_lookup[doc["id"]] = doc
        
        print(f"✅ Loaded {len(doc_lookup)} document metadata records")
        return doc_lookup
        
    except Exception as e:
        print(f"⚠️  Error loading document metadata: {str(e)}")
        return {}

def check_index_readiness(metadata):
    """Check if the index is ready for queries"""
    try:
        index_name = metadata.get("index_name")
        endpoint_name = metadata.get("endpoint_name")
        
        if not index_name or not endpoint_name:
            print("❌ Missing index or endpoint name in metadata")
            return False
        
        # Check index
        index = aiplatform.MatchingEngineIndex(index_name)
        print(f"📊 Index: {index.display_name}")
        
        # Check endpoint
        endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
        print(f"🚀 Endpoint: {endpoint.display_name}")
        
        # Check deployed indexes
        deployed_indexes = endpoint.deployed_indexes
        if not deployed_indexes:
            print("❌ No deployed indexes found on endpoint")
            return False
            
        print(f"✅ Found {len(deployed_indexes)} deployed index(es)")
        
        for deployed_index in deployed_indexes:
            print(f"   - ID: {deployed_index.id}")
            # Note: deployed_index.state might not be available in all API versions
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking index readiness: {str(e)}")
        return False

def create_robust_query_function(metadata, doc_lookup):
    """Create a robust query function that handles API variations"""
    
    endpoint_name = metadata.get("endpoint_name")
    deployed_index_id = metadata.get("deployed_index_id")
    
    if not endpoint_name or not deployed_index_id:
        print("❌ Missing endpoint or deployed index ID")
        return None
    
    try:
        endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        print(f"✅ Connected to endpoint: {endpoint.display_name}")
        print(f"✅ Using deployed index ID: {deployed_index_id}")
        
        def query_vector_search(query_text, num_neighbors=5, instrument_filter=None, source_filter=None, debug=False):
            """Robust query function with multiple fallback strategies"""
            try:
                if debug:
                    print(f"🔍 Debug mode: Searching for '{query_text}'")
                
                # Generate embedding for query
                query_embedding = embedding_model.get_embeddings([query_text])[0].values
                
                # Convert to list format (most compatible)
                if hasattr(query_embedding, 'tolist'):
                    embedding_list = query_embedding.tolist()
                else:
                    embedding_list = list(query_embedding)
                
                if debug:
                    print(f"   Generated embedding: {len(embedding_list)} dimensions")
                    print(f"   Sample values: {embedding_list[:3]}")
                
                # Try multiple query strategies
                strategies = [
                    {
                        "name": "Basic Query",
                        "params": {
                            "deployed_index_id": deployed_index_id,
                            "queries": [embedding_list],
                            "num_neighbors": num_neighbors
                        }
                    },
                    {
                        "name": "Alternative Parameter Format",
                        "params": {
                            "deployed_index_id": deployed_index_id,
                            "queries": [embedding_list],
                            "num_neighbors": num_neighbors,
                            "return_full_datapoint": False
                        }
                    }
                ]
                
                # Add filtering strategy if filters specified
                if instrument_filter or source_filter:
                    restricts = []
                    if instrument_filter:
                        restricts.append({"namespace": "instrument", "allow": [instrument_filter]})
                    if source_filter:
                        restricts.append({"namespace": "source_type", "allow": [source_filter]})
                    
                    strategies.append({
                        "name": "Filtered Query",
                        "params": {
                            "deployed_index_id": deployed_index_id,
                            "queries": [embedding_list],
                            "num_neighbors": num_neighbors * 2,  # Get more to filter
                            "restricts": restricts
                        }
                    })
                
                response = None
                successful_strategy = None
                
                for strategy in strategies:
                    try:
                        if debug:
                            print(f"   Trying strategy: {strategy['name']}")
                        
                        response = endpoint.find_neighbors(**strategy['params'])
                        
                        # Check if we got a valid response
                        if response and len(response) > 0:
                            # Handle different response formats
                            if isinstance(response, list) and len(response[0]) > 0:
                                successful_strategy = strategy['name']
                                if debug:
                                    print(f"   ✅ Strategy '{strategy['name']}' succeeded!")
                                break
                            elif hasattr(response, 'neighbors') and response.neighbors:
                                successful_strategy = strategy['name']
                                if debug:
                                    print(f"   ✅ Strategy '{strategy['name']}' succeeded!")
                                break
                        
                        if debug:
                            print(f"   ⚠️  Strategy '{strategy['name']}' returned empty results")
                            
                    except Exception as e:
                        if debug:
                            print(f"   ❌ Strategy '{strategy['name']}' failed: {str(e)}")
                        continue
                
                if not response or not successful_strategy:
                    print("❌ All query strategies failed")
                    return []
                
                # Process the response
                neighbors = []
                if isinstance(response, list) and len(response) > 0:
                    neighbors = response[0]
                elif hasattr(response, 'neighbors'):
                    neighbors = response.neighbors[0] if isinstance(response.neighbors, list) else response.neighbors
                
                if not neighbors:
                    print("⚠️  No neighbors found in response")
                    return []
                
                print(f"✅ Found {len(neighbors)} results using '{successful_strategy}'")
                
                # Format results
                results = []
                for i, neighbor in enumerate(neighbors):
                    try:
                        # Extract neighbor data
                        neighbor_id = getattr(neighbor, 'id', str(neighbor))
                        distance = getattr(neighbor, 'distance', 0.0)
                        
                        # Look up document metadata
                        doc = doc_lookup.get(neighbor_id, {})
                        
                        result = {
                            "rank": i + 1,
                            "id": neighbor_id,
                            "distance": distance,
                            "similarity": 1 - distance if distance <= 1 else 1 / (1 + distance),
                            "title": doc.get("title", "Unknown Document"),
                            "content_preview": doc.get("content", "")[:300] + "..." if doc.get("content") else "No content available",
                            "instrument": doc.get("instrument", "Unknown"),
                            "source_type": doc.get("source_type", "Unknown"),
                            "date": doc.get("date", "Unknown"),
                            "file_path": doc.get("file_path", "Unknown")
                        }
                        results.append(result)
                        
                    except Exception as e:
                        if debug:
                            print(f"   ⚠️  Error processing result {i}: {str(e)}")
                        continue
                
                # Apply manual filtering if needed
                if instrument_filter or source_filter:
                    filtered_results = []
                    for result in results:
                        if instrument_filter and result["instrument"] != instrument_filter:
                            continue
                        if source_filter and result["source_type"] != source_filter:
                            continue
                        filtered_results.append(result)
                    results = filtered_results[:num_neighbors]
                
                return results[:num_neighbors]
                
            except Exception as e:
                print(f"❌ Error in query function: {str(e)}")
                return []
        
        return query_vector_search
        
    except Exception as e:
        print(f"❌ Error creating query function: {str(e)}")
        return None

def run_comprehensive_tests(query_func, metadata):
    """Run comprehensive tests to verify the system works"""
    print("\n🧪 Running Comprehensive Tests...")
    
    # Get available instruments and source types from metadata
    instruments = metadata.get("instruments", [])
    source_types = metadata.get("source_types", [])
    
    print(f"   Available instruments: {instruments}")
    print(f"   Available source types: {source_types}")
    
    # Test queries
    test_queries = [
        {
            "query": "Bitcoin price analysis",
            "description": "General crypto query"
        },
        {
            "query": "Apple quarterly earnings",
            "description": "Specific company earnings"
        },
        {
            "query": "market trends and volatility",
            "description": "General market analysis"
        },
        {
            "query": "oil price forecast",
            "description": "Commodity analysis"
        }
    ]
    
    # Add instrument-specific tests
    if instruments:
        test_queries.extend([
            {
                "query": "recent news and analysis",
                "instrument_filter": instruments[0],
                "description": f"Filtered by instrument: {instruments[0]}"
            }
        ])
    
    # Add source-specific tests
    if source_types:
        test_queries.extend([
            {
                "query": "financial analysis",
                "source_filter": source_types[0],
                "description": f"Filtered by source: {source_types[0]}"
            }
        ])
    
    test_results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n   Test {i}: {test['description']}")
        print(f"   Query: '{test['query']}'")
        
        try:
            results = query_func(
                test['query'],
                num_neighbors=3,
                instrument_filter=test.get('instrument_filter'),
                source_filter=test.get('source_filter'),
                debug=True
            )
            
            if results:
                print(f"   ✅ Success: {len(results)} results")
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

def interactive_search(query_func):
    """Interactive search interface"""
    print("\n🔍 Interactive Search Mode")
    print("=" * 50)
    print("Enter search queries to test the Vector Search system.")
    print("Commands:")
    print("  - Type your search query and press Enter")
    print("  - 'debug on/off' to toggle debug mode")
    print("  - 'quit' or 'exit' to stop")
    
    debug_mode = False
    
    while True:
        print("\n" + "-" * 30)
        user_input = input("🔍 Search query: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if user_input.lower() == 'debug on':
            debug_mode = True
            print("✅ Debug mode enabled")
            continue
        
        if user_input.lower() == 'debug off':
            debug_mode = False
            print("✅ Debug mode disabled")
            continue
        
        if not user_input:
            continue
        
        # Optional filters
        instrument = input("Filter by instrument (optional): ").strip()
        source = input("Filter by source type (optional): ").strip()
        
        # Perform search
        try:
            results = query_func(
                user_input,
                num_neighbors=5,
                instrument_filter=instrument if instrument else None,
                source_filter=source if source else None,
                debug=debug_mode
            )
            
            if results:
                print(f"\n📊 Found {len(results)} results:")
                for result in results:
                    print(f"\n{result['rank']}. {result['title']}")
                    print(f"   Similarity: {result['similarity']:.3f}")
                    print(f"   Instrument: {result['instrument']}")
                    print(f"   Source: {result['source_type']}")
                    print(f"   Date: {result['date']}")
                    print(f"   Preview: {result['content_preview'][:150]}...")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Search error: {str(e)}")

def main():
    """Main function"""
    print("🚀 Enhanced Vector Search Query System")
    print("=" * 60)
    
    # Load metadata
    metadata = load_deployment_metadata()
    if not metadata:
        print("❌ Cannot proceed without metadata")
        return
    
    print(f"✅ Loaded metadata for deployment: {metadata.get('uid', 'unknown')}")
    
    # Check if system is ready
    if not check_index_readiness(metadata):
        print("❌ Vector Search system is not ready")
        print("💡 Wait 10-15 minutes after deployment and try again")
        return
    
    # Load document metadata
    doc_lookup = load_document_metadata(metadata)
    
    # Create query function
    query_func = create_robust_query_function(metadata, doc_lookup)
    if not query_func:
        print("❌ Failed to create query function")
        return
    
    # Run tests
    if run_comprehensive_tests(query_func, metadata):
        print("\n✅ System is working! Ready for interactive search.")
        interactive_search(query_func)
    else:
        print("\n❌ System tests failed. Please check your deployment.")
        print("💡 Try waiting longer or recreating the index.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
    main()

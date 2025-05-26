# query_deployed_index.py
import json
import os
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configuration - UPDATE THESE VALUES
PROJECT_ID = "your-gcp-project-id"  # Update with your project ID
LOCATION = "us-central1"

# You need to get these values from your deployment
# Check the metadata file created by the corpus processor: processed_corpus/vector_search_metadata_*.json
ENDPOINT_RESOURCE_NAME = "projects/YOUR_PROJECT_NUMBER/locations/us-central1/indexEndpoints/YOUR_ENDPOINT_ID"
DEPLOYED_INDEX_ID = "tradesage_deployed_YOUR_UID"

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
        return None, None
    
    # Use the most recent metadata file
    latest_metadata = sorted(metadata_files)[-1]
    metadata_path = f"processed_corpus/{latest_metadata}"
    
    print(f"📄 Loading metadata from: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    endpoint_name = metadata.get("endpoint_name")
    deployed_index_id = metadata.get("deployed_index_id")
    
    print(f"✅ Found endpoint: {endpoint_name}")
    print(f"✅ Found deployed index ID: {deployed_index_id}")
    
    return endpoint_name, deployed_index_id

def create_query_function(endpoint_name, deployed_index_id):
    """Create a query function for the deployed index"""
    
    # Get the endpoint
    try:
        endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
        print(f"✅ Connected to endpoint: {endpoint.display_name}")
    except Exception as e:
        print(f"❌ Error connecting to endpoint: {str(e)}")
        return None
    
    # Initialize embedding model (same as used for indexing)
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    def query_vector_search(query_text, num_neighbors=5, instrument_filter=None):
        """Query the Vector Search index"""
        try:
            print(f"🔍 Searching for: '{query_text}'")
            
            # Generate embedding for query
            query_embedding = embedding_model.get_embeddings([query_text])[0].values
            
            # Prepare restricts for filtering
            restricts = []
            if instrument_filter:
                restricts.append({
                    "namespace": "instrument",
                    "allow": [instrument_filter]
                })
                print(f"   Filtering by instrument: {instrument_filter}")
            
            # Query the deployed index
            # Note: restricts/filtering may not be supported in this API version
            # Try without restricts first, then apply filtering to results
            try:
                if restricts:
                    # Try with restricts parameter (different possible names)
                    try:
                        response = endpoint.find_neighbors(
                            deployed_index_id=deployed_index_id,
                            queries=[query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding],
                            num_neighbors=num_neighbors * 2,  # Get more results to filter
                            restrict_tokens=restricts
                        )
                    except TypeError:
                        # If restrict_tokens doesn't work, try other parameter names
                        try:
                            response = endpoint.find_neighbors(
                                deployed_index_id=deployed_index_id,
                                queries=[query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding],
                                num_neighbors=num_neighbors * 2,
                                filters=restricts
                            )
                        except TypeError:
                            # Fallback: no filtering at API level
                            print("   ⚠️  API-level filtering not supported, filtering results manually")
                            response = endpoint.find_neighbors(
                                deployed_index_id=deployed_index_id,
                                queries=[query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding],
                                num_neighbors=num_neighbors * 3  # Get more to filter manually
                            )
                else:
                    # No filtering requested
                    response = endpoint.find_neighbors(
                        deployed_index_id=deployed_index_id,
                        queries=[query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding],
                        num_neighbors=num_neighbors
                    )
            except Exception as api_error:
                print(f"   ❌ API Error: {str(api_error)}")
                # Try with minimal parameters
                response = endpoint.find_neighbors(
                    deployed_index_id=deployed_index_id,
                    queries=[query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding],
                    num_neighbors=num_neighbors
                )
            
            # Debug: Check response structure
            print(f"   🔍 Debug - Response type: {type(response)}")
            print(f"   🔍 Debug - Response length: {len(response) if hasattr(response, '__len__') else 'N/A'}")
            
            # Handle different response formats
            if isinstance(response, list) and len(response) > 0:
                neighbors = response[0]
            elif hasattr(response, 'neighbors') and response.neighbors:
                neighbors = response.neighbors[0] if isinstance(response.neighbors, list) else response.neighbors
            elif hasattr(response, '__iter__'):
                # Try to iterate and get first element
                try:
                    neighbors = next(iter(response))
                except (StopIteration, TypeError):
                    neighbors = []
            else:
                print(f"   ❌ Unexpected response format: {type(response)}")
                return []
            
            print(f"✅ Found {len(neighbors) if hasattr(neighbors, '__len__') else 0} results")
            
            # If we were filtering by instrument but couldn't do it at API level,
            # we need to filter results manually (this requires document metadata)
            filtered_results = neighbors
            if instrument_filter and len(neighbors) > num_neighbors:
                print(f"   🔍 Manually filtering by instrument: {instrument_filter}")
                # Note: This would require loading document metadata to filter by instrument
                # For now, we'll just take the first num_neighbors results
                filtered_results = neighbors[:num_neighbors]
            
            # Check if we have any results
            if not filtered_results or len(filtered_results) == 0:
                print("   ⚠️  No results returned from Vector Search")
                return []
            
            # Process and return results
            results = []
            for i, neighbor in enumerate(filtered_results):
                try:
                    result = {
                        "rank": i + 1,
                        "id": neighbor.id if hasattr(neighbor, 'id') else str(neighbor),
                        "distance": neighbor.distance if hasattr(neighbor, 'distance') else 0.0,
                        "similarity": 1 - (neighbor.distance if hasattr(neighbor, 'distance') else 0.0)
                    }
                    results.append(result)
                except Exception as e:
                    print(f"   ⚠️  Error processing result {i}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"❌ Error querying Vector Search: {str(e)}")
            return []
    
    return query_vector_search

def main():
    """Interactive query interface"""
    print("🚀 TradeSage Vector Search Query Interface")
    print("=" * 50)
    
    # Load deployment metadata
    endpoint_name, deployed_index_id = load_deployment_metadata()
    
    if not endpoint_name or not deployed_index_id:
        print("\n💡 Manual Setup Required:")
        print("If you don't have metadata files, you can set these manually:")
        print("1. Go to Google Cloud Console > Vertex AI > Vector Search")
        print("2. Find your endpoint and copy the resource name")
        print("3. Update ENDPOINT_RESOURCE_NAME and DEPLOYED_INDEX_ID in this script")
        return
    
    # Create query function
    query_func = create_query_function(endpoint_name, deployed_index_id)
    
    if not query_func:
        return
    
    print("\n🔍 Ready to search! Try some queries:")
    print("   Examples: 'Bitcoin price analysis', 'Apple earnings', 'market trends'")
    print("   Type 'quit' to exit")
    
    # Interactive query loop
    while True:
        print("\n" + "-" * 50)
        query = input("Enter your search query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not query:
            continue
        
        # Ask for optional instrument filter
        instrument = input("Filter by instrument (optional, press Enter to skip): ").strip()
        instrument_filter = instrument if instrument else None
        
        # Perform search
        results = query_func(query, num_neighbors=5, instrument_filter=instrument_filter)
        
        if results:
            print(f"\n📊 Results for '{query}':")
            for result in results:
                print(f"  {result['rank']}. ID: {result['id']}")
                print(f"     Distance: {result['distance']:.4f}")
                print(f"     Similarity: {result['similarity']:.4f}")
        else:
            print("❌ No results found")

def test_queries():
    """Run some test queries"""
    print("🧪 Running test queries...")
    
    # Load deployment metadata
    endpoint_name, deployed_index_id = load_deployment_metadata()
    
    if not endpoint_name or not deployed_index_id:
        print("❌ Cannot run tests without deployment metadata")
        return
    
    # Create query function
    query_func = create_query_function(endpoint_name, deployed_index_id)
    
    if not query_func:
        return
    
    # Test queries
    test_queries_list = [
        "Bitcoin price analysis",
        "Apple quarterly earnings",
        "market volatility trends",
        "oil price forecast",
        "cryptocurrency investment"
    ]
    
    for query in test_queries_list:
        print(f"\n🔍 Testing: '{query}'")
        results = query_func(query, num_neighbors=3)
        
        if results:
            for result in results:
                print(f"  - ID: {result['id'][:20]}... (similarity: {result['similarity']:.3f})")
        else:
            print("  No results found")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_queries()
        else:
            PROJECT_ID = sys.argv[1]
            main()
    else:
        main()

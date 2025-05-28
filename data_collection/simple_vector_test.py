# simple_vector_test.py
import json
import os
import time
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configuration
PROJECT_ID = "your-gcp-project-id"  # Update with your project ID
LOCATION = "us-central1"

# Initialize
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project=PROJECT_ID, location=LOCATION)

def load_metadata():
    """Load the latest metadata file"""
    metadata_files = [f for f in os.listdir("processed_corpus") if f.startswith("vector_search_metadata_")]
    if not metadata_files:
        return None
    
    latest = sorted(metadata_files)[-1]
    with open(f"processed_corpus/{latest}", 'r') as f:
        return json.load(f)

def test_basic_connectivity():
    """Test basic connectivity to Vector Search"""
    print("🔧 Testing Basic Connectivity...")
    
    metadata = load_metadata()
    if not metadata:
        print("❌ No metadata found")
        return False
    
    try:
        # Get endpoint
        endpoint_name = metadata["endpoint_name"]
        endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
        
        print(f"✅ Connected to endpoint: {endpoint.display_name}")
        
        # Check deployed indexes
        deployed_indexes = endpoint.deployed_indexes
        print(f"✅ Found {len(deployed_indexes)} deployed indexes")
        
        return True, endpoint, metadata
        
    except Exception as e:
        print(f"❌ Connectivity test failed: {str(e)}")
        return False, None, None

def test_embedding_generation():
    """Test embedding generation"""
    print("\n🧪 Testing Embedding Generation...")
    
    try:
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        test_text = "test query for vector search"
        
        embedding = model.get_embeddings([test_text])[0].values
        print(f"✅ Generated embedding: {len(embedding)} dimensions")
        print(f"✅ First 3 values: {embedding[:3]}")
        
        return embedding
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {str(e)}")
        return None

def test_different_query_formats(endpoint, deployed_index_id, test_embedding):
    """Test different ways to format the query"""
    print(f"\n🔍 Testing Different Query Formats...")
    print(f"Using deployed index ID: {deployed_index_id}")
    
    # Convert embedding to different formats
    formats_to_test = [
        ("Python List", test_embedding.tolist() if hasattr(test_embedding, 'tolist') else list(test_embedding)),
        ("Direct Values", test_embedding),
    ]
    
    for format_name, embedding_format in formats_to_test:
        print(f"\n   Testing {format_name}...")
        
        try:
            # Most basic query possible
            response = endpoint.find_neighbors(
                deployed_index_id=deployed_index_id,
                queries=[embedding_format],
                num_neighbors=3
            )
            
            print(f"     Response type: {type(response)}")
            print(f"     Response: {response}")
            
            # Try to extract meaningful info
            if response:
                if isinstance(response, list):
                    print(f"     Response is list with {len(response)} elements")
                    if len(response) > 0:
                        first_element = response[0]
                        print(f"     First element type: {type(first_element)}")
                        print(f"     First element: {first_element}")
                        
                        if hasattr(first_element, '__len__'):
                            print(f"     First element length: {len(first_element)}")
                            
                            if len(first_element) > 0:
                                print(f"✅ SUCCESS with {format_name}! Found {len(first_element)} results")
                                
                                # Try to examine the first result
                                try:
                                    first_result = first_element[0]
                                    print(f"     First result type: {type(first_result)}")
                                    print(f"     First result attributes: {dir(first_result)}")
                                    
                                    if hasattr(first_result, 'id'):
                                        print(f"     First result ID: {first_result.id}")
                                    if hasattr(first_result, 'distance'):
                                        print(f"     First result distance: {first_result.distance}")
                                        
                                    return True
                                except Exception as e:
                                    print(f"     Error examining first result: {str(e)}")
                            else:
                                print(f"     Empty results list")
                else:
                    print(f"     Non-list response: {response}")
            else:
                print(f"     Null/empty response")
                
        except Exception as e:
            print(f"     ❌ Error with {format_name}: {str(e)}")
    
    return False

def check_index_status_detailed(metadata):
    """Check detailed index status"""
    print(f"\n📊 Checking Detailed Index Status...")
    
    try:
        index_name = metadata["index_name"]
        index = aiplatform.MatchingEngineIndex(index_name)
        
        print(f"Index Display Name: {index.display_name}")
        print(f"Create Time: {index.create_time}")
        print(f"Update Time: {index.update_time}")
        
        # Try to get the index state/details
        try:
            index_dict = index.to_dict()
            
            if 'state' in index_dict:
                print(f"Index State: {index_dict['state']}")
            
            if 'indexStats' in index_dict:
                stats = index_dict['indexStats']
                print(f"Vector Count: {stats.get('vectorsCount', 'N/A')}")
                print(f"Shards Count: {stats.get('shardsCount', 'N/A')}")
            else:
                print("⚠️  No index stats available")
                
            if 'metadata' in index_dict and 'config' in index_dict['metadata']:
                config = index_dict['metadata']['config']
                print(f"Dimensions: {config.get('dimensions', 'N/A')}")
                print(f"Algorithm: {config.get('algorithmConfig', 'N/A')}")
                
        except Exception as e:
            print(f"⚠️  Could not get detailed index info: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error checking index status: {str(e)}")

def suggest_solutions():
    """Suggest potential solutions"""
    print(f"\n💡 POTENTIAL SOLUTIONS:")
    print(f"1. **Wait Longer**: Vector indexes can take 30+ minutes to be fully ready")
    print(f"2. **Check Google Cloud Console**: Verify index status is 'Ready'")
    print(f"3. **Recreate with Smaller Dataset**: Try with just 10-20 documents first")
    print(f"4. **Check Billing**: Ensure your GCP project has billing enabled")
    print(f"5. **Quota Issues**: Check if you've hit Vector Search quotas")
    print(f"6. **Region Issues**: Try a different region (us-central1, us-west1)")

def main():
    """Run focused diagnostics"""
    print("🔬 Simple Vector Search Test")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    success, endpoint, metadata = test_basic_connectivity()
    if not success:
        return
    
    # Test 2: Embedding generation
    test_embedding = test_embedding_generation()
    if test_embedding is None:
        return
    
    # Test 3: Index status
    check_index_status_detailed(metadata)
    
    # Test 4: Different query formats
    deployed_index_id = metadata["deployed_index_id"]
    query_success = test_different_query_formats(endpoint, deployed_index_id, test_embedding)
    
    print(f"\n" + "=" * 50)
    print(f"📊 FINAL DIAGNOSIS")
    print(f"=" * 50)
    
    if query_success:
        print(f"✅ Vector Search is working!")
        print(f"✅ The issue was likely in query formatting or timing")
    else:
        print(f"❌ Vector Search is still returning empty results")
        print(f"❌ This suggests the index is not properly populated or ready")
        
        # Check timing
        created_time = metadata.get('created_at', '')
        if created_time:
            from datetime import datetime
            try:
                created = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                now = datetime.now(created.tzinfo)
                elapsed = now - created
                elapsed_minutes = elapsed.total_seconds() / 60
                
                print(f"⏰ Time since creation: {elapsed_minutes:.1f} minutes")
                
                if elapsed_minutes < 30:
                    print(f"💡 LIKELY CAUSE: Index is still building (needs ~30 minutes)")
                    print(f"💡 RECOMMENDATION: Wait {30 - elapsed_minutes:.1f} more minutes and try again")
                else:
                    print(f"💡 LIKELY CAUSE: Index creation may have failed silently")
                    print(f"💡 RECOMMENDATION: Recreate the index")
                    
            except:
                print(f"⏰ Could not parse creation time")
    
    suggest_solutions()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
    main()

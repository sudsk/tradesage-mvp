# deep_vector_search_debug.py
import json
import os
from google.cloud import aiplatform
from google.cloud import storage
import vertexai
from vertexai.language_models import TextEmbeddingModel
import time

# Configuration
PROJECT_ID = "your-gcp-project-id"  # Update with your project ID
LOCATION = "us-central1"

# Initialize
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project=PROJECT_ID, location=LOCATION)

def load_deployment_metadata():
    """Load deployment metadata"""
    metadata_files = []
    if os.path.exists("processed_corpus"):
        metadata_files = [f for f in os.listdir("processed_corpus") if f.startswith("vector_search_metadata_")]
    
    if not metadata_files:
        print("❌ No metadata files found.")
        return None
    
    latest_metadata = sorted(metadata_files)[-1]
    metadata_path = f"processed_corpus/{latest_metadata}"
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    return metadata

def check_index_detailed_status(metadata):
    """Get detailed index status using the REST API"""
    print("🔍 Checking Detailed Index Status...")
    
    try:
        index_name = metadata.get("index_name")
        index = aiplatform.MatchingEngineIndex(index_name)
        
        # Get full index details
        index_dict = index.to_dict()
        
        print(f"📊 Detailed Index Information:")
        print(f"   Display Name: {index_dict.get('displayName', 'N/A')}")
        print(f"   State: {index_dict.get('state', 'N/A')}")
        
        # Check metadata
        if 'metadata' in index_dict:
            metadata_info = index_dict['metadata']
            print(f"   Metadata: {metadata_info}")
            
            if 'config' in metadata_info:
                config = metadata_info['config']
                print(f"   Dimensions: {config.get('dimensions', 'N/A')}")
                print(f"   Algorithm: {config.get('algorithmConfig', 'N/A')}")
        
        # Check index stats
        if 'indexStats' in index_dict:
            stats = index_dict['indexStats']
            print(f"   Vectors Count: {stats.get('vectorsCount', 'N/A')}")
            print(f"   Shards Count: {stats.get('shardsCount', 'N/A')}")
        else:
            print("   ⚠️  No index stats available")
        
        # Check deployed indexes
        if 'deployedIndexes' in index_dict:
            deployed = index_dict['deployedIndexes']
            print(f"   Deployed Indexes: {len(deployed)}")
        
        return index_dict
        
    except Exception as e:
        print(f"❌ Error getting detailed index status: {str(e)}")
        return None

def validate_gcs_embeddings(metadata):
    """Validate the GCS embeddings file in detail"""
    print("\n🔍 Validating GCS Embeddings File...")
    
    try:
        gcs_uri = metadata.get("gcs_uri")
        if not gcs_uri:
            print("❌ No GCS URI found")
            return False
        
        # Parse GCS URI
        gcs_parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = gcs_parts[0]
        blob_name = gcs_parts[1]
        
        # Access GCS
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            print("❌ GCS file does not exist")
            return False
        
        # Download and validate content
        content = blob.download_as_text()
        lines = content.strip().split('\n')
        
        print(f"📊 GCS File Validation:")
        print(f"   Total lines: {len(lines)}")
        
        # Check first few records
        valid_records = 0
        invalid_records = 0
        
        for i, line in enumerate(lines[:5]):  # Check first 5 records
            try:
                record = json.loads(line)
                
                # Validate required fields
                required_fields = ['id', 'embedding']
                missing_fields = [field for field in required_fields if field not in record]
                
                if missing_fields:
                    print(f"   Record {i+1}: Missing fields: {missing_fields}")
                    invalid_records += 1
                else:
                    embedding = record['embedding']
                    if isinstance(embedding, list) and len(embedding) == 768:
                        valid_records += 1
                        print(f"   Record {i+1}: ✅ Valid (ID: {record['id'][:20]}..., Embedding: {len(embedding)} dims)")
                    else:
                        print(f"   Record {i+1}: ❌ Invalid embedding format")
                        invalid_records += 1
                        
            except json.JSONDecodeError as e:
                print(f"   Record {i+1}: ❌ JSON decode error: {str(e)}")
                invalid_records += 1
        
        print(f"   Valid records: {valid_records}/5 sampled")
        print(f"   Invalid records: {invalid_records}/5 sampled")
        
        return invalid_records == 0
        
    except Exception as e:
        print(f"❌ Error validating GCS file: {str(e)}")
        return False

def test_direct_api_call(metadata):
    """Test direct API call to Vector Search"""
    print("\n🧪 Testing Direct Vector Search API Call...")
    
    try:
        endpoint_name = metadata.get("endpoint_name")
        deployed_index_id = metadata.get("deployed_index_id")
        
        # Initialize endpoint
        endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
        
        # Generate test embedding
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        test_embedding = embedding_model.get_embeddings(["test query"])[0].values
        
        print(f"   Test embedding dimension: {len(test_embedding)}")
        print(f"   Test embedding type: {type(test_embedding)}")
        print(f"   Test embedding sample: {test_embedding[:3]}...")
        
        # Try different query formats
        test_formats = [
            ("List format", test_embedding.tolist() if hasattr(test_embedding, 'tolist') else list(test_embedding)),
            ("Raw format", test_embedding),
        ]
        
        for format_name, embedding_format in test_formats:
            try:
                print(f"   Testing {format_name}...")
                
                response = endpoint.find_neighbors(
                    deployed_index_id=deployed_index_id,
                    queries=[embedding_format],
                    num_neighbors=1
                )
                
                print(f"     Response type: {type(response)}")
                print(f"     Response length: {len(response) if hasattr(response, '__len__') else 'N/A'}")
                
                if response and len(response) > 0:
                    print(f"     First result type: {type(response[0])}")
                    print(f"     First result length: {len(response[0]) if hasattr(response[0], '__len__') else 'N/A'}")
                    if len(response[0]) > 0:
                        print(f"     SUCCESS: Got {len(response[0])} results!")
                        return True
                else:
                    print(f"     Empty response")
                    
            except Exception as e:
                print(f"     Error with {format_name}: {str(e)}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error in direct API test: {str(e)}")
        return False

def check_google_cloud_console_status():
    """Instructions for checking Google Cloud Console"""
    print("\n🌐 Google Cloud Console Check:")
    print("   1. Go to: https://console.cloud.google.com/vertex-ai/matching-engine/indexes")
    print("   2. Find your index: tradesage-index-20250526190708")
    print("   3. Check the Status column - should show 'Ready'")
    print("   4. Click on the index name to see details")
    print("   5. Look for 'Vector count' - should show 102")
    print("   6. Check 'Last updated' timestamp")
    print("\n   If status shows 'Updating' or 'Failed', that's the issue!")

def try_recreate_index_suggestion(metadata):
    """Suggest recreating the index if all else fails"""
    print("\n🔄 If Vector Search is still not working after 2+ hours:")
    print("   The index creation may have silently failed.")
    print("   Recommendation: Recreate the index")
    print("\n   Steps to recreate:")
    print("   1. Delete current index and endpoint in Google Cloud Console")
    print("   2. Re-run your corpus processor script")
    print("   3. Wait 30 minutes for new index to build")
    print("\n   Alternative: Try a smaller test index first")
    print("   - Create index with just 10-20 documents")
    print("   - Verify it works before scaling up")

def main():
    """Run deep debugging"""
    print("🔬 Deep Vector Search Debugging")
    print("=" * 60)
    
    # Load metadata
    metadata = load_deployment_metadata()
    if not metadata:
        return
    
    created_time = metadata.get('created_at', 'unknown')
    print(f"📋 Index created: {created_time}")
    print(f"   Time since creation: ~2+ hours (as reported)")
    
    # Deep checks
    checks = [
        ("Detailed Index Status", lambda: check_index_detailed_status(metadata)),
        ("GCS Embeddings Validation", lambda: validate_gcs_embeddings(metadata)),
        ("Direct API Test", lambda: test_direct_api_call(metadata)),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n{'='*60}")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ Error in {check_name}: {str(e)}")
            results[check_name] = False
    
    # Console check instructions
    check_google_cloud_console_status()
    
    # Summary and recommendations
    print(f"\n{'='*60}")
    print("📊 DEEP DEBUG SUMMARY")
    print("=" * 60)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:25} | {status}")
    
    print("\n💡 NEXT STEPS:")
    
    if results.get("Direct API Test", False):
        print("   🎉 Vector Search is working! There might be a query formatting issue.")
    elif not results.get("GCS Embeddings Validation", False):
        print("   📁 GCS embeddings file has issues - need to regenerate embeddings")
    elif not results.get("Detailed Index Status", False):
        print("   🔍 Index has configuration or state issues")
    else:
        print("   🔄 Index creation likely failed silently")
        try_recreate_index_suggestion(metadata)
    
    print("\n🎯 IMMEDIATE ACTION:")
    print("   1. Check Google Cloud Console status (see instructions above)")
    print("   2. If status is 'Failed' or stuck 'Updating' -> recreate index")
    print("   3. If status is 'Ready' but still no results -> contact support")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
    main()

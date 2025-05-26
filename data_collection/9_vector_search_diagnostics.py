# vector_search_diagnostics.py
import json
import os
from google.cloud import aiplatform
from google.cloud import storage
import vertexai
from vertexai.language_models import TextEmbeddingModel

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

def check_index_status(metadata):
    """Check the status of the Vector Search index"""
    print("🔍 Checking Vector Search Index Status...")
    
    try:
        index_name = metadata.get("index_name")
        if not index_name:
            print("❌ No index name found in metadata")
            return False
        
        # Get the index
        index = aiplatform.MatchingEngineIndex(index_name)
        
        print(f"📊 Index Details:")
        print(f"   Name: {index.display_name}")
        print(f"   Resource Name: {index.resource_name}")
        print(f"   Create Time: {index.create_time}")
        print(f"   Update Time: {index.update_time}")
        
        # Check if index is ready
        if hasattr(index, 'state'):
            print(f"   State: {index.state}")
        
        # Try to get more detailed info
        try:
            index_stats = index.to_dict()
            if 'indexStats' in index_stats:
                stats = index_stats['indexStats']
                print(f"   Vector Count: {stats.get('vectorsCount', 'Unknown')}")
                print(f"   Shards Count: {stats.get('shardsCount', 'Unknown')}")
        except:
            print("   ⚠️  Detailed stats not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking index: {str(e)}")
        return False

def check_endpoint_status(metadata):
    """Check the status of the index endpoint"""
    print("\n🚀 Checking Index Endpoint Status...")
    
    try:
        endpoint_name = metadata.get("endpoint_name")
        if not endpoint_name:
            print("❌ No endpoint name found in metadata")
            return False
        
        # Get the endpoint
        endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
        
        print(f"📊 Endpoint Details:")
        print(f"   Name: {endpoint.display_name}")
        print(f"   Resource Name: {endpoint.resource_name}")
        print(f"   Create Time: {endpoint.create_time}")
        print(f"   Update Time: {endpoint.update_time}")
        
        # Check deployed indexes
        try:
            deployed_indexes = endpoint.deployed_indexes
            print(f"   Deployed Indexes: {len(deployed_indexes)}")
            
            for i, deployed_index in enumerate(deployed_indexes):
                print(f"     {i+1}. ID: {deployed_index.id}")
                print(f"        Index: {deployed_index.index}")
                print(f"        Create Time: {deployed_index.create_time}")
                if hasattr(deployed_index, 'state'):
                    print(f"        State: {deployed_index.state}")
                
        except Exception as e:
            print(f"   ⚠️  Could not get deployed indexes: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking endpoint: {str(e)}")
        return False

def check_gcs_data(metadata):
    """Check the GCS data that was uploaded"""
    print("\n💾 Checking GCS Data...")
    
    try:
        gcs_uri = metadata.get("gcs_uri")
        if not gcs_uri:
            print("❌ No GCS URI found in metadata")
            return False
        
        print(f"📁 GCS URI: {gcs_uri}")
        
        # Parse bucket and blob name
        gcs_parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = gcs_parts[0]
        blob_name = gcs_parts[1]
        
        # Check if file exists
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        if blob.exists():
            print(f"✅ GCS file exists")
            print(f"   Size: {blob.size} bytes")
            print(f"   Created: {blob.time_created}")
            print(f"   Updated: {blob.updated}")
            
            # Try to read first few lines to check format
            try:
                content = blob.download_as_text()
                lines = content.strip().split('\n')
                print(f"   Lines in file: {len(lines)}")
                
                if lines:
                    # Check first line format
                    first_line = json.loads(lines[0])
                    print(f"   First record keys: {list(first_line.keys())}")
                    if 'embedding' in first_line:
                        embedding_len = len(first_line['embedding'])
                        print(f"   Embedding dimension: {embedding_len}")
                
            except Exception as e:
                print(f"   ⚠️  Could not read file contents: {str(e)}")
        else:
            print("❌ GCS file does not exist")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking GCS data: {str(e)}")
        return False

def test_embedding_generation():
    """Test if embedding generation is working"""
    print("\n🧪 Testing Embedding Generation...")
    
    try:
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        test_texts = ["Apple earnings report", "Bitcoin price analysis", "Market trends"]
        
        for text in test_texts:
            try:
                embeddings = embedding_model.get_embeddings([text])
                embedding = embeddings[0].values
                
                print(f"   ✅ '{text}' -> {len(embedding)} dimensions")
                
            except Exception as e:
                print(f"   ❌ Error generating embedding for '{text}': {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing embeddings: {str(e)}")
        return False

def run_simple_query_test(metadata):
    """Try a very simple query to see what happens"""
    print("\n🔍 Running Simple Query Test...")
    
    try:
        endpoint_name = metadata.get("endpoint_name")
        deployed_index_id = metadata.get("deployed_index_id")
        
        if not endpoint_name or not deployed_index_id:
            print("❌ Missing endpoint or deployed index ID")
            return False
        
        # Get endpoint
        endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
        
        # Generate a simple query embedding
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        query_embedding = embedding_model.get_embeddings(["test"])[0].values
        
        print(f"   Query embedding dimension: {len(query_embedding)}")
        
        # Try the simplest possible query
        try:
            response = endpoint.find_neighbors(
                deployed_index_id=deployed_index_id,
                queries=[query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding],
                num_neighbors=1
            )
            
            print(f"   Response type: {type(response)}")
            print(f"   Response: {response}")
            
            return True
            
        except Exception as query_error:
            print(f"   ❌ Query error: {str(query_error)}")
            return False
        
    except Exception as e:
        print(f"❌ Error in query test: {str(e)}")
        return False

def main():
    """Run full diagnostics"""
    print("🏥 Vector Search Diagnostics")
    print("=" * 50)
    
    # Load metadata
    metadata = load_deployment_metadata()
    if not metadata:
        return
    
    print(f"📋 Loaded metadata from deployment: {metadata.get('uid', 'unknown')}")
    print(f"   Total documents: {metadata.get('total_documents', 'unknown')}")
    print(f"   Created: {metadata.get('created_at', 'unknown')}")
    
    # Run checks
    checks = [
        ("Index Status", lambda: check_index_status(metadata)),
        ("Endpoint Status", lambda: check_endpoint_status(metadata)),
        ("GCS Data", lambda: check_gcs_data(metadata)),
        ("Embedding Generation", test_embedding_generation),
        ("Simple Query", lambda: run_simple_query_test(metadata))
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ Error in {check_name}: {str(e)}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:20} | {status}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not results.get("Index Status", False):
        print("   - Check if your index creation completed successfully")
        
    if not results.get("Endpoint Status", False):
        print("   - Check if your endpoint deployment completed successfully")
        
    if not results.get("GCS Data", False):
        print("   - Verify that embeddings were uploaded to GCS correctly")
        
    if not results.get("Embedding Generation", False):
        print("   - Check your Vertex AI API access and quotas")
        
    if not results.get("Simple Query", False):
        print("   - The index might still be building or there's a configuration issue")
        print("   - Wait 10-15 minutes and try again if the index was just created")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
    main()

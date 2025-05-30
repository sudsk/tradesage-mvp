# corpus_processor_vertex_FIXED.py
import os
import json
import html2text
from bs4 import BeautifulSoup
import glob
import uuid
from datetime import datetime
from tqdm import tqdm
import time

# Google Cloud imports
from google.cloud import storage
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Set up environment
PROJECT_ID = "your-gcp-project-id"  # Update with your Google Cloud project ID
LOCATION = "us-central1"             # Choose appropriate region
BUCKET_NAME = f"{PROJECT_ID}-vector-search-data"  # GCS bucket for embeddings
UID = datetime.now().strftime("%Y%m%d%H%M%S")  # Unique identifier

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Create output directory
OUTPUT_DIR = "processed_corpus"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def preprocess_text(text):
    """Clean and normalize text content"""
    if "<" in text and ">" in text:
        h = html2text.HTML2Text()
        h.ignore_links = False
        text = h.handle(text)
    
    text = text.replace("\n\n", " ").replace("\t", " ").strip()
    text = " ".join(text.split())
    return text

def extract_text_from_item(item, instrument, source_type, file_path):
    """Extract text content from a JSON item"""
    title_fields = ["title", "headline", "name", "symbol"]
    content_fields = ["text", "content", "summary", "description", "analysis_text", "article"]
    
    # Find title
    title = None
    for field in title_fields:
        if field in item and item[field]:
            title = item[field]
            break
    
    # Find content
    content = None
    for field in content_fields:
        if field in item and item[field]:
            content = item[field]
            break
    
    # Look deeper for nested content
    if not content and isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, dict):
                for field in content_fields:
                    if field in value and value[field]:
                        content = value[field]
                        break
    
    if not content or len(content) < 50:
        return None
    
    content = preprocess_text(content)
    
    # Extract date
    date = None
    date_fields = ["date", "publish_date", "published", "timestamp", "created_at"]
    for field in date_fields:
        if field in item and item[field]:
            date = item[field]
            break
    
    if date and isinstance(date, str):
        try:
            if 'T' in date:
                date = date.split('T')[0]
            elif '/' in date:
                parts = date.split('/')
                if len(parts) == 3:
                    date = f"{parts[2]}-{parts[0]}-{parts[1]}"
        except:
            date = None
    
    return {
        "id": str(uuid.uuid4()),
        "title": title if title else "Untitled Document",
        "content": content,
        "instrument": instrument,
        "source_type": source_type,
        "file_path": file_path,
        "date": date if date else "Unknown",
        "metadata": {
            "instrument": instrument,
            "source_type": source_type,
            "has_title": bool(title)
        }
    }

def process_json_files(directory):
    """Process JSON files and extract text content"""
    processed_documents = []
    json_files = glob.glob(f"{directory}/**/*.json", recursive=True)
    
    for file_path in tqdm(json_files, desc=f"Processing JSON files in {directory}"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            parts = file_path.split(os.path.sep)
            instrument = parts[-2] if len(parts) >= 2 else "unknown"
            source_type = parts[-3] if len(parts) >= 3 else "unknown"
            
            if isinstance(data, list):
                for item in data:
                    doc = extract_text_from_item(item, instrument, source_type, file_path)
                    if doc:
                        processed_documents.append(doc)
            else:
                doc = extract_text_from_item(data, instrument, source_type, file_path)
                if doc:
                    processed_documents.append(doc)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return processed_documents

def process_html_files(directory):
    """Process HTML files"""
    processed_documents = []
    html_files = glob.glob(f"{directory}/**/*.html", recursive=True)
    
    for file_path in tqdm(html_files, desc=f"Processing HTML files in {directory}"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            parts = file_path.split(os.path.sep)
            instrument = parts[-2] if len(parts) >= 2 else "unknown"
            source_type = parts[-3] if len(parts) >= 3 else "unknown"
            
            # Convert HTML to text
            soup = BeautifulSoup(html_content, 'html.parser')
            content = soup.get_text(separator="\n")
            content = preprocess_text(content)
            
            if len(content) < 100:
                continue
            
            filename = os.path.basename(file_path)
            title = filename.replace('.html', '').replace('_', ' ')
            
            doc = {
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "instrument": instrument,
                "source_type": source_type,
                "file_path": file_path,
                "date": "Unknown",
                "metadata": {
                    "instrument": instrument,
                    "source_type": source_type,
                    "has_title": True
                }
            }
            
            processed_documents.append(doc)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return processed_documents

def chunk_document(doc, chunk_size=512):
    """Split document into chunks"""
    content = doc["content"]
    paragraphs = content.split("\n\n")
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunk_doc = doc.copy()
                chunk_doc["id"] = f"{doc['id']}_chunk_{len(chunks)}"
                chunk_doc["content"] = current_chunk.strip()
                chunks.append(chunk_doc)
            
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunk_doc = doc.copy()
        chunk_doc["id"] = f"{doc['id']}_chunk_{len(chunks)}"
        chunk_doc["content"] = current_chunk.strip()
        chunks.append(chunk_doc)
    
    return chunks

def generate_embeddings_and_upload(documents):
    """Generate embeddings WITHOUT restricts - this is the key fix!"""
    print("🔮 Generating embeddings...")
    
    # Initialize embedding model
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    # Create GCS bucket if it doesn't exist
    storage_client = storage.Client(project=PROJECT_ID)
    try:
        bucket = storage_client.get_bucket(BUCKET_NAME)
        print(f"✅ Using existing bucket: {BUCKET_NAME}")
    except:
        bucket = storage_client.create_bucket(BUCKET_NAME, location=LOCATION)
        print(f"✅ Created new bucket: {BUCKET_NAME}")
    
    # Generate embeddings in batches
    all_embeddings = []
    failed_count = 0
    batch_size = 5
    
    for i in tqdm(range(0, len(documents), batch_size), desc="Generating embeddings"):
        batch = documents[i:i + batch_size]
        batch_texts = [doc["content"] for doc in batch]
        
        try:
            # Generate embeddings for batch
            embeddings_response = embedding_model.get_embeddings(batch_texts)
            
            # Process each embedding in the batch
            for doc, embedding_obj in zip(batch, embeddings_response):
                try:
                    embedding_values = embedding_obj.values
                    
                    # Convert to list
                    if hasattr(embedding_values, 'tolist'):
                        embedding_list = embedding_values.tolist()
                    else:
                        embedding_list = list(embedding_values)
                    
                    # CRITICAL FIX: Use the simple format without restricts
                    # Vector Search will accept this basic format
                    embedding_data = {
                        "id": doc["id"],
                        "embedding": embedding_list
                        # NO RESTRICTS - this was causing the index to reject embeddings
                    }
                    
                    all_embeddings.append(embedding_data)
                    
                except Exception as e:
                    print(f"❌ Error processing embedding: {str(e)}")
                    failed_count += 1
                    continue
            
            # Rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ Error generating embeddings for batch: {str(e)}")
            failed_count += len(batch)
            continue
    
    if not all_embeddings:
        raise Exception("No embeddings generated successfully")
    
    success_rate = len(all_embeddings) / len(documents) * 100
    print(f"✅ Generated {len(all_embeddings)}/{len(documents)} embeddings ({success_rate:.1f}% success rate)")
    
    # Save embeddings to JSONL file
    embeddings_file = f"{OUTPUT_DIR}/embeddings_{UID}.jsonl"
    with open(embeddings_file, 'w') as f:
        for embedding_data in all_embeddings:
            f.write(json.dumps(embedding_data) + '\n')
    
    # Upload to GCS
    blob_name = f"embeddings/embeddings_{UID}.jsonl"
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(embeddings_file)
    
    gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}"
    print(f"✅ Uploaded {len(all_embeddings)} embeddings to: {gcs_uri}")
    
    # Also save document metadata for reference
    metadata_file = f"{OUTPUT_DIR}/documents_{UID}.jsonl"
    with open(metadata_file, 'w') as f:
        for doc in documents:
            f.write(json.dumps(doc) + '\n')
    
    metadata_blob = bucket.blob(f"metadata/documents_{UID}.jsonl")
    metadata_blob.upload_from_filename(metadata_file)
    
    return gcs_uri

def create_vector_search_index(gcs_uri):
    """Create Vector Search index with simple configuration"""
    print("🔍 Creating Vector Search index...")
    
    try:
        # CRITICAL FIX: Use simple index configuration without complex metadata
        my_index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
            display_name=f"tradesage-simple-{UID}",
            contents_delta_uri=gcs_uri,
            dimensions=768,  # text-embedding-004 dimensions
            approximate_neighbors_count=100,
            description=f"TradeSage simple index - {UID}"
        )
        
        print(f"✅ Created Vector Search index: {my_index.display_name}")
        print(f"   Resource name: {my_index.resource_name}")
        return my_index
        
    except Exception as e:
        print(f"❌ Error creating Vector Search index: {str(e)}")
        raise

def create_index_endpoint():
    """Create Index Endpoint"""
    print("🚀 Creating Index Endpoint...")
    
    try:
        my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name=f"tradesage-endpoint-{UID}",
            public_endpoint_enabled=True
        )
        
        print(f"✅ Created Index Endpoint: {my_index_endpoint.display_name}")
        print(f"   Resource name: {my_index_endpoint.resource_name}")
        return my_index_endpoint
        
    except Exception as e:
        print(f"❌ Error creating Index Endpoint: {str(e)}")
        raise

def deploy_index(my_index, my_index_endpoint):
    """Deploy the index to the endpoint"""
    print("🚀 Deploying index to endpoint...")
    
    deployed_index_id = f"tradesage_simple_{UID}"
    
    try:
        my_index_endpoint.deploy_index(
            index=my_index,
            deployed_index_id=deployed_index_id
        )
        
        print(f"✅ Successfully deployed index with ID: {deployed_index_id}")
        return deployed_index_id
        
    except Exception as e:
        print(f"❌ Error deploying index: {str(e)}")
        raise

def create_simple_query_function(my_index_endpoint, deployed_index_id, documents):
    """Create a simple query function"""
    
    # Create document lookup
    doc_lookup = {doc["id"]: doc for doc in documents}
    
    def query_vector_search(query_text, num_neighbors=5):
        """Simple query function without complex filtering"""
        try:
            # Generate embedding for query
            embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            query_embedding = embedding_model.get_embeddings([query_text])[0].values
            
            # Convert to list
            if hasattr(query_embedding, 'tolist'):
                embedding_list = query_embedding.tolist()
            else:
                embedding_list = list(query_embedding)
            
            # Simple query
            response = my_index_endpoint.find_neighbors(
                deployed_index_id=deployed_index_id,
                queries=[embedding_list],
                num_neighbors=num_neighbors
            )
            
            # Process results
            if not response or len(response) == 0:
                return []
            
            neighbors = response[0]
            results = []
            
            for i, neighbor in enumerate(neighbors):
                doc = doc_lookup.get(neighbor.id, {})
                
                result = {
                    "rank": i + 1,
                    "id": neighbor.id,
                    "distance": neighbor.distance,
                    "similarity": 1 - neighbor.distance,
                    "title": doc.get("title", "Unknown"),
                    "content_preview": doc.get("content", "")[:200] + "...",
                    "instrument": doc.get("instrument", "Unknown"),
                    "source_type": doc.get("source_type", "Unknown"),
                    "date": doc.get("date", "Unknown")
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ Error querying Vector Search: {str(e)}")
            return []
    
    return query_vector_search

def main():
    """Main function with simplified approach"""
    print("🚀 TradeSage FIXED Corpus Processor")
    print("=" * 50)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Unique ID: {UID}")
    print("=" * 50)
    
    # Step 1: Process documents
    print("\n📚 Step 1: Processing documents...")
    all_documents = []
    
    directories = ["news", "analyst_reports", "technical_analysis"]
    for directory in directories:
        if os.path.exists(directory):
            docs = process_json_files(directory)
            all_documents.extend(docs)
            print(f"  - {directory}: {len(docs)} documents")
    
    if os.path.exists("earnings"):
        html_docs = process_html_files("earnings")
        all_documents.extend(html_docs)
        print(f"  - earnings: {len(html_docs)} documents")
    
    if not all_documents:
        print("❌ No documents found!")
        return
    
    print(f"📄 Total documents: {len(all_documents)}")
    
    # Step 2: Chunk documents
    print("\n✂️  Step 2: Chunking documents...")
    chunked_documents = []
    for doc in tqdm(all_documents, desc="Chunking"):
        chunks = chunk_document(doc)
        chunked_documents.extend(chunks)
    
    print(f"📝 Total chunks: {len(chunked_documents)}")
    
    # Step 3: Generate embeddings and upload (FIXED VERSION)
    print("\n🔮 Step 3: Generating embeddings (FIXED)...")
    gcs_uri = generate_embeddings_and_upload(chunked_documents)
    
    # Step 4: Create Vector Search Index (SIMPLIFIED)
    print("\n🔍 Step 4: Creating Vector Search Index (SIMPLIFIED)...")
    my_index = create_vector_search_index(gcs_uri)
    
    # Step 5: Create Index Endpoint
    print("\n🚀 Step 5: Creating Index Endpoint...")
    my_index_endpoint = create_index_endpoint()
    
    # Step 6: Deploy Index
    print("\n🚀 Step 6: Deploying Index...")
    deployed_index_id = deploy_index(my_index, my_index_endpoint)
    
    # Step 7: Create simple query function
    print("\n🔍 Step 7: Creating simple query function...")
    query_func = create_simple_query_function(my_index_endpoint, deployed_index_id, chunked_documents)
    
    # Save metadata
    metadata = {
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "uid": UID,
        "bucket_name": BUCKET_NAME,
        "total_documents": len(chunked_documents),
        "original_documents": len(all_documents),
        "instruments": list(set(doc["instrument"] for doc in all_documents)),
        "source_types": list(set(doc["source_type"] for doc in all_documents)),
        "index_name": my_index.resource_name,
        "endpoint_name": my_index_endpoint.resource_name,
        "deployed_index_id": deployed_index_id,
        "gcs_uri": gcs_uri,
        "created_at": datetime.now().isoformat(),
        "version": "FIXED_SIMPLE"
    }
    
    with open(f"{OUTPUT_DIR}/vector_search_metadata_{UID}.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ FIXED Vector Search setup complete!")
    print(f"📊 Key Changes Made:")
    print(f"   - ❌ Removed problematic 'restricts' from embeddings")
    print(f"   - ✅ Used simple embedding format")
    print(f"   - ✅ Added proper batch processing")
    print(f"   - ✅ Simplified index configuration")
    
    print(f"\n⏳ Wait 15-20 minutes, then test with:")
    print(f"   python simple_vector_test.py {PROJECT_ID}")
    
    return query_func

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
        BUCKET_NAME = f"{PROJECT_ID}-vector-search-data"
        print(f"Using project ID: {PROJECT_ID}")
    
    main()

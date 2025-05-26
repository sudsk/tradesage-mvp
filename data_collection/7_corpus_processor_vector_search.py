# corpus_processor_with_vertex_vector_search.py
import os
import json
import html2text
from bs4 import BeautifulSoup
import pandas as pd
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
CORPUS_NAME = "tradesage-corpus"     # Name for your vector database

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
storage_client = storage.Client(project=PROJECT_ID)

# Create a directory for processed documents
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

def convert_html_to_text(html_content):
    """Convert HTML content to plain text"""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator="\n")

def process_json_files(directory):
    """Process JSON files and extract text content"""
    processed_documents = []
    json_files = glob.glob(f"{directory}/**/*.json", recursive=True)
    
    for file_path in tqdm(json_files, desc="Processing JSON files"):
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

def extract_text_from_item(item, instrument, source_type, file_path):
    """Extract text content from a JSON item"""
    title_fields = ["title", "headline", "name", "symbol"]
    content_fields = ["text", "content", "summary", "description", "analysis_text", "article"]
    
    title = None
    for field in title_fields:
        if field in item and item[field]:
            title = item[field]
            break
    
    content = None
    for field in content_fields:
        if field in item and item[field]:
            content = item[field]
            break
    
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
    
    date = None
    date_fields = ["date", "publish_date", "published", "timestamp", "created_at"]
    for field in date_fields:
        if field in item and item[field]:
            date = item[field]
            break
    
    if date:
        try:
            if isinstance(date, str):
                if 'T' in date:
                    date = date.split('T')[0]
                elif '/' in date:
                    parts = date.split('/')
                    if len(parts) == 3:
                        date = f"{parts[2]}-{parts[0]}-{parts[1]}"
        except:
            date = None
    
    doc = {
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
    
    return doc

def process_html_files(directory):
    """Process HTML files (like SEC filings)"""
    processed_documents = []
    html_files = glob.glob(f"{directory}/**/*.html", recursive=True)
    
    for file_path in tqdm(html_files, desc="Processing HTML files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            parts = file_path.split(os.path.sep)
            instrument = parts[-2] if len(parts) >= 2 else "unknown"
            source_type = parts[-3] if len(parts) >= 3 else "unknown"
            
            content = convert_html_to_text(html_content)
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

def chunk_document(doc, chunk_size=512, overlap=50):
    """Split document into chunks for embedding"""
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

def create_vector_search_index():
    """Create a Vertex AI Vector Search index using the current SDK"""
    print("Creating Vertex AI Vector Search index...")
    
    try:
        # Check if index already exists
        existing_indexes = aiplatform.MatchingEngineIndex.list(
            filter=f'display_name="{CORPUS_NAME}"',
            project=PROJECT_ID,
            location=LOCATION
        )
        
        if existing_indexes:
            print(f"Index '{CORPUS_NAME}' already exists, using existing index")
            return existing_indexes[0]
        
        # Create a new Vector Search index using the correct API
        print("Creating new Vector Search index...")
        
        # Use the aiplatform client directly
        client = aiplatform.gapic.IndexServiceClient(
            client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
        )
        
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
        
        index = {
            "display_name": CORPUS_NAME,
            "description": "TradeSage financial document corpus",
            "metadata": {
                "config": {
                    "dimensions": 768,  # Text embedding gecko dimensions
                    "approximate_neighbors_count": 150,
                    "shard_size": "SHARD_SIZE_SMALL",
                    "distance_measure_type": "DOT_PRODUCT_DISTANCE",
                    "algorithm_config": {
                        "tree_ah_config": {
                            "leaf_node_embedding_count": 500,
                            "leaf_nodes_to_search_percent": 7
                        }
                    }
                }
            }
        }
        
        operation = client.create_index(parent=parent, index=index)
        print(f"Creating index... Operation: {operation.name}")
        
        # Wait for the operation to complete
        result = operation.result(timeout=1800)  # 30 minutes timeout
        print(f"Index created: {result.name}")
        
        return result
        
    except Exception as e:
        print(f"Error creating Vector Search index: {str(e)}")
        print("Falling back to local processing...")
        return None

def create_index_endpoint():
    """Create an index endpoint for serving the index"""
    print("Creating Vector Search index endpoint...")
    
    try:
        # Check if endpoint already exists
        existing_endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
            filter=f'display_name="{CORPUS_NAME}-endpoint"',
            project=PROJECT_ID,
            location=LOCATION
        )
        
        if existing_endpoints:
            print(f"Endpoint already exists, using existing endpoint")
            return existing_endpoints[0]
        
        # Create endpoint using the aiplatform library
        endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name=f"{CORPUS_NAME}-endpoint",
            description="Endpoint for TradeSage corpus",
            public_endpoint_enabled=True,
            project=PROJECT_ID,
            location=LOCATION
        )
        
        print(f"Endpoint created: {endpoint.name}")
        return endpoint
        
    except Exception as e:
        print(f"Error creating endpoint: {str(e)}")
        return None

def generate_embeddings_and_upload(documents):
    """Generate embeddings and upload to GCS for Vector Search"""
    print("Generating embeddings for Vector Search...")
    
    try:
        # Initialize embedding model
        embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        
        # Prepare data for Vector Search format
        vector_data = []
        batch_size = 50
        
        for i in tqdm(range(0, len(documents), batch_size), desc="Generating embeddings"):
            batch = documents[i:i+batch_size]
            texts = [doc["content"] for doc in batch]
            
            try:
                embeddings = embedding_model.get_embeddings(texts)
                
                for j, doc in enumerate(batch):
                    # Format for Vector Search: {"id": "...", "embedding": [...], "restricts": {...}}
                    vector_point = {
                        "id": doc["id"],
                        "embedding": embeddings[j].values,
                        "restricts": [
                            {"namespace": "instrument", "allow": [doc["instrument"]]},
                            {"namespace": "source_type", "allow": [doc["source_type"]]}
                        ]
                    }
                    vector_data.append(vector_point)
                    
            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size + 1}: {str(e)}")
                continue
        
        if not vector_data:
            print("No embeddings generated")
            return None, None
        
        # Upload to GCS in the format expected by Vector Search
        gcs_bucket_name = f"{PROJECT_ID}-vector-search-data"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create bucket if it doesn't exist
        try:
            bucket = storage_client.get_bucket(gcs_bucket_name)
        except:
            bucket = storage_client.create_bucket(gcs_bucket_name, location=LOCATION)
        
        # Save embeddings in JSONL format for Vector Search
        embeddings_file = f"{OUTPUT_DIR}/embeddings_{timestamp}.jsonl"
        with open(embeddings_file, 'w') as f:
            for point in vector_data:
                # Convert numpy array to list for JSON serialization
                point_copy = point.copy()
                point_copy["embedding"] = point_copy["embedding"].tolist()
                f.write(json.dumps(point_copy) + '\n')
        
        # Upload to GCS
        blob_name = f"embeddings/{timestamp}/embeddings.jsonl"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(embeddings_file)
        
        gcs_uri = f"gs://{gcs_bucket_name}/{blob_name}"
        print(f"Uploaded embeddings to: {gcs_uri}")
        
        # Also save metadata
        metadata_file = f"{OUTPUT_DIR}/documents_metadata_{timestamp}.jsonl"
        with open(metadata_file, 'w') as f:
            for doc in documents:
                f.write(json.dumps(doc) + '\n')
        
        metadata_blob = bucket.blob(f"metadata/{timestamp}/documents.jsonl")
        metadata_blob.upload_from_filename(metadata_file)
        
        return gcs_uri, f"gs://{gcs_bucket_name}/metadata/{timestamp}/documents.jsonl"
        
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return None, None

def deploy_index_to_endpoint(index, endpoint, embeddings_uri):
    """Deploy the index to an endpoint"""
    if not index or not endpoint or not embeddings_uri:
        print("Cannot deploy index: missing index, endpoint, or embeddings")
        return None
    
    try:
        print("Deploying index to endpoint...")
        
        # Deploy the index
        deployed_index = endpoint.deploy_index(
            index=index,
            deployed_index_id=f"{CORPUS_NAME}-deployed",
            display_name=f"{CORPUS_NAME} Deployed Index",
            machine_type="e2-standard-2",
            min_replica_count=1,
            max_replica_count=1
        )
        
        print(f"Index deployed successfully!")
        return deployed_index
        
    except Exception as e:
        print(f"Error deploying index: {str(e)}")
        return None

def create_query_interface(endpoint, documents_metadata):
    """Create a simple query interface for the Vector Search"""
    if not endpoint:
        return None
    
    def query_vector_search(query_text, num_neighbors=5, instrument_filter=None):
        """Query the Vector Search index"""
        try:
            # Generate embedding for query
            embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
            query_embedding = embedding_model.get_embeddings([query_text])[0].values
            
            # Prepare restricts if instrument filter is provided
            restricts = []
            if instrument_filter:
                restricts.append({
                    "namespace": "instrument",
                    "allow": [instrument_filter]
                })
            
            # Query the deployed index
            response = endpoint.find_neighbors(
                deployed_index_id=f"{CORPUS_NAME}-deployed",
                queries=[query_embedding.tolist()],
                num_neighbors=num_neighbors,
                restricts=restricts if restricts else None
            )
            
            # Process results
            results = []
            for neighbor in response[0]:
                # Find the corresponding document metadata
                doc_metadata = next(
                    (doc for doc in documents_metadata if doc["id"] == neighbor.id),
                    None
                )
                
                if doc_metadata:
                    results.append({
                        "id": neighbor.id,
                        "distance": neighbor.distance,
                        "title": doc_metadata["title"],
                        "content_preview": doc_metadata["content"][:200] + "...",
                        "instrument": doc_metadata["instrument"],
                        "source_type": doc_metadata["source_type"]
                    })
            
            return results
            
        except Exception as e:
            print(f"Error querying Vector Search: {str(e)}")
            return []
    
    return query_vector_search

def main():
    """Main function with Vertex AI Vector Search"""
    print("🚀 TradeSage Corpus Processor with Vertex AI Vector Search")
    print("=" * 70)
    
    # Process corpus files
    print("📚 Processing documents...")
    json_documents = process_json_files("news") + \
                     process_json_files("analyst_reports") + \
                     process_json_files("technical_analysis")
    html_documents = process_html_files("earnings")
    
    all_documents = json_documents + html_documents
    print(f"Processed {len(all_documents)} documents")
    
    # Chunk documents
    chunked_documents = []
    for doc in tqdm(all_documents, desc="Chunking documents"):
        chunks = chunk_document(doc)
        chunked_documents.extend(chunks)
    
    print(f"Created {len(chunked_documents)} chunks from {len(all_documents)} documents")
    
    # Save processed documents locally
    output_path = f"{OUTPUT_DIR}/processed_documents.jsonl"
    with open(output_path, 'w') as f:
        for doc in chunked_documents:
            f.write(json.dumps(doc) + '\n')
    
    print(f"Saved processed documents to {output_path}")
    
    # Create Vector Search index
    index = create_vector_search_index()
    
    if index:
        # Create endpoint
        endpoint = create_index_endpoint()
        
        if endpoint:
            # Generate embeddings and upload to GCS
            embeddings_uri, metadata_uri = generate_embeddings_and_upload(chunked_documents)
            
            if embeddings_uri:
                # Deploy index to endpoint
                deployed_index = deploy_index_to_endpoint(index, endpoint, embeddings_uri)
                
                if deployed_index:
                    # Create query interface
                    query_func = create_query_interface(endpoint, chunked_documents)
                    
                    # Test the search
                    if query_func:
                        print("\n🔍 Testing Vector Search...")
                        test_queries = ["Bitcoin analysis", "Apple earnings", "market trends"]
                        
                        for query in test_queries:
                            results = query_func(query, num_neighbors=3)
                            print(f"   Query: '{query}' -> {len(results)} results")
                            for result in results[:1]:  # Show first result
                                print(f"     - {result['title'][:50]}... (distance: {result['distance']:.3f})")
    
    # Save metadata
    metadata = {
        "corpus_size": len(chunked_documents),
        "original_documents": len(all_documents),
        "instruments": list(set(doc["instrument"] for doc in all_documents)),
        "source_types": list(set(doc["source_type"] for doc in all_documents)),
        "processed_date": datetime.now().isoformat(),
        "vertex_ai": {
            "project": PROJECT_ID,
            "location": LOCATION,
            "index_name": index.name if index else None,
            "endpoint_name": endpoint.name if 'endpoint' in locals() and endpoint else None
        }
    }
    
    with open(f"{OUTPUT_DIR}/corpus_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Corpus processing complete!")
    print(f"📊 Summary:")
    print(f"   - Total chunks: {len(chunked_documents)}")
    print(f"   - Vector Search index: {'✅ Created' if index else '❌ Failed'}")
    print(f"   - Endpoint: {'✅ Created' if 'endpoint' in locals() and endpoint else '❌ Failed'}")
    print(f"   - Metadata saved to: {OUTPUT_DIR}/corpus_metadata.json")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PROJECT_ID = sys.argv[1]
        print(f"Using project ID: {PROJECT_ID}")
    
    main()
